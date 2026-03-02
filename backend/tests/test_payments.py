"""Payment system tests aligned with current API contracts."""
import asyncio
import hashlib
import hmac
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.firebase_auth import verify_firebase_token
from app.services.idempotency_service import IdempotencyService


class _FakeCollection:
    def __init__(self, matched_count: int = 1):
        self.matched_count = matched_count

    async def update_one(self, *args, **kwargs):
        return SimpleNamespace(matched_count=self.matched_count)

    async def insert_one(self, *args, **kwargs):
        return SimpleNamespace(inserted_id="x")


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_firebase_token():
    async def override_verify_firebase_token():
        return {"uid": "test-user-123"}

    app.dependency_overrides[verify_firebase_token] = override_verify_firebase_token
    yield
    app.dependency_overrides.pop(verify_firebase_token, None)


@pytest.fixture
def mock_razorpay_client():
    with patch("app.api.routes.payments.get_razorpay_client") as mock_get_client:
        mock_client = Mock()
        mock_client.order = Mock()
        mock_client.payment = Mock()
        mock_client.utility = Mock()
        mock_get_client.return_value = mock_client
        yield mock_client


class TestPaymentIdempotency:
    @pytest.mark.asyncio
    async def test_idempotency_key_generation(self):
        key1 = await IdempotencyService.generate_key("user123", 50000, {"tier": "adventure"})
        key2 = await IdempotencyService.generate_key("user123", 50000, {"tier": "adventure"})
        assert key1 == key2
        assert len(key1) == 64

    def test_duplicate_request_detection(self, mock_razorpay_client, mock_firebase_token, client):
        mock_razorpay_client.order.create.return_value = {
            "id": "order_test123",
            "amount": 29900,
            "currency": "INR",
        }
        cached = {
            "order_id": "order_test123",
            "amount": 29900,
            "currency": "INR",
            "key_id": "rzp_test_key",
            "tier": "adventure",
        }

        with patch("app.api.routes.payments.settings.razorpay_key_id", "rzp_test_key"), patch(
            "app.services.idempotency_service.IdempotencyService.check_and_store",
            new=AsyncMock(side_effect=[None, cached]),
        ), patch(
            "app.services.idempotency_service.IdempotencyService.store_response",
            new=AsyncMock(return_value=None),
        ):
            headers = {"X-Idempotency-Key": "idem-123"}
            response1 = client.post("/api/v1/payments/create-order?tier=adventure", headers=headers)
            response2 = client.post("/api/v1/payments/create-order?tier=adventure", headers=headers)

            assert response1.status_code == 200
            assert response2.status_code == 200
            assert mock_razorpay_client.order.create.call_count == 1
            assert response2.json() == cached


class TestPaymentFailures:
    def test_signature_verification_failure(self, mock_razorpay_client, mock_firebase_token, client):
        mock_razorpay_client.utility.verify_payment_signature.side_effect = Exception("Invalid signature")

        with patch("app.api.routes.payments.settings.app_env", "production"):
            response = client.post(
                "/api/v1/payments/verify",
                json={
                    "razorpay_order_id": "order_123",
                    "razorpay_payment_id": "pay_123",
                    "razorpay_signature": "invalid_signature",
                },
            )

        assert response.status_code == 400
        assert "invalid payment signature" in response.json()["message"].lower()


class TestPaymentEndToEnd:
    def test_complete_payment_flow(self, mock_razorpay_client, mock_firebase_token, client):
        mock_razorpay_client.order.create.return_value = {
            "id": "order_e2e123",
            "amount": 29900,
            "currency": "INR",
        }
        mock_razorpay_client.payment.fetch.return_value = {
            "id": "pay_e2e123",
            "order_id": "order_e2e123",
            "status": "captured",
        }
        mock_razorpay_client.order.fetch.return_value = {
            "id": "order_e2e123",
            "amount": 29900,
            "currency": "INR",
            "notes": {"user_id": "test-user-123", "tier": "adventure"},
        }
        mock_razorpay_client.utility.verify_payment_signature.return_value = True

        fake_db = {
            "payments": _FakeCollection(matched_count=1),
            "users": _FakeCollection(matched_count=1),
        }

        with patch("app.api.routes.payments.settings.razorpay_key_id", "rzp_test_key"), patch(
            "app.services.idempotency_service.IdempotencyService.check_and_store",
            new=AsyncMock(return_value=None),
        ), patch(
            "app.services.idempotency_service.IdempotencyService.store_response",
            new=AsyncMock(return_value=None),
        ), patch("app.api.routes.payments.MongoDB.get_db", return_value=fake_db):
            create_response = client.post("/api/v1/payments/create-order?tier=adventure")
            assert create_response.status_code == 200

            verify_response = client.post(
                "/api/v1/payments/verify",
                json={
                    "razorpay_order_id": "order_e2e123",
                    "razorpay_payment_id": "pay_e2e123",
                    "razorpay_signature": "valid_signature",
                },
            )

            assert verify_response.status_code == 200
            payload = verify_response.json()
            assert payload["status"] == "success"
            assert payload["tier"] == "adventure"


class TestWebhookHandling:
    def test_webhook_duplicate_event_is_ignored(self, client):
        class _Receipts:
            async def update_one(self, *args, **kwargs):
                return SimpleNamespace(matched_count=1)

        fake_db = {
            "webhook_receipts": _Receipts(),
            "payments": _FakeCollection(),
            "users": _FakeCollection(),
            "webhook_errors": _FakeCollection(),
        }

        payload = {"id": "evt_1", "event": "payment.captured", "payload": {"payment": {"entity": {}}}}

        with patch("app.api.routes.webhooks.settings.app_env", "development"), patch(
            "app.api.routes.webhooks.MongoDB.get_db", return_value=fake_db
        ):
            response = client.post("/api/v1/webhooks/razorpay", json=payload)

        assert response.status_code == 200
        assert response.json()["status"] == "duplicate_ignored"

    def test_webhook_signature_helper(self):
        from app.api.routes.webhooks import verify_razorpay_signature

        payload = b'{"event":"payment.captured"}'
        secret = "secret"
        signature = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

        assert asyncio.run(verify_razorpay_signature(payload, signature, secret)) is True

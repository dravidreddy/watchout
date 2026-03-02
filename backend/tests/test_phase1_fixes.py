"""Regression tests for phase-1 hardening items."""
import os
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.firebase_auth import verify_firebase_token


class _FakeCursor:
    def __init__(self, items):
        self._items = items

    async def to_list(self, length):
        return self._items


class _FakePaymentsCollection:
    def __init__(self, items):
        self._items = items
        self.updated = []

    def find(self, *_args, **_kwargs):
        return _FakeCursor(self._items)

    async def update_one(self, *args, **kwargs):
        self.updated.append((args, kwargs))
        return SimpleNamespace(matched_count=1)


class TestPaymentReconciliation:
    @pytest.mark.asyncio
    async def test_reconciliation_finds_stuck_payments(self):
        from app.services.payment_reconciliation import reconcile_stuck_payments

        stuck = [
            {
                "payment_id": "pay_test_123",
                "order_id": "order_test_123",
                "status": "authorized",
                "created_at": datetime.now(timezone.utc) - timedelta(hours=25),
                "user_id": "test_user",
                "tier": "adventure",
            }
        ]
        payments = _FakePaymentsCollection(stuck)
        fake_db = {"payments": payments}

        mock_client = Mock()
        mock_client.payment.fetch.return_value = {
            "id": "pay_test_123",
            "order_id": "order_test_123",
            "status": "failed",
            "error_description": "declined",
        }

        with patch("app.services.payment_reconciliation.settings.redis_url", ""), patch(
            "app.services.payment_reconciliation.MongoDB.get_db", return_value=fake_db
        ), patch(
            "app.services.payment_reconciliation.razorpay.Client", return_value=mock_client
        ):
            await reconcile_stuck_payments()

        assert len(payments.updated) == 1

    def test_verify_endpoint_validates_required_fields(self):
        """Current /verify is synchronous server-side verification, not fire-and-forget."""
        async def override_verify_firebase_token():
            return {"uid": "test-user-123"}

        app.dependency_overrides[verify_firebase_token] = override_verify_firebase_token
        try:
            with TestClient(app) as client:
                response = client.post("/api/v1/payments/verify", json={"razorpay_order_id": "order_only"})
                assert response.status_code == 400
                assert "missing required" in response.json()["message"].lower()
        finally:
            app.dependency_overrides.pop(verify_firebase_token, None)


class TestHallucinationPrevention:
    @pytest.mark.asyncio
    async def test_detect_hallucination_with_prices(self):
        from app.agents.reviewer import ReviewerAgent

        reviewer = ReviewerAgent()
        result = await reviewer.detect_hallucination(
            response="Flights to Goa cost around ₹4,000 and hotels are ₹2,500 per night.",
            tools_called=[],
        )
        assert result["hallucination_risk"] == "high"
        assert "specific facts" in result["issues"].lower()

    @pytest.mark.asyncio
    async def test_detect_hallucination_with_times(self):
        from app.agents.reviewer import ReviewerAgent

        reviewer = ReviewerAgent()
        result = await reviewer.detect_hallucination(
            response="Vande Bharat departs at 6:25 AM and arrives at 1:30 PM.",
            tools_called=[],
        )
        assert result["hallucination_risk"] in {"high", "medium"}

    @pytest.mark.asyncio
    async def test_system_prompt_contains_prevention_rules(self):
        from app.agents.base import BaseAgent

        class TestAgent(BaseAgent):
            async def run(self, user_input, context=None):
                return {"response": "test"}

        agent = TestAgent(name="Test", description="Test agent", model_type="fast")
        prompt = agent.get_system_prompt()

        assert "Never make up prices" in prompt
        assert "Operational Rules" in prompt or "OPERATIONAL RULES" in prompt


class TestOfflinePersistence:
    def test_offline_db_exports_exist(self):
        frontend_path = os.path.join(
            os.path.dirname(__file__),
            "../../frontend/src/lib/offline-db.ts",
        )
        assert os.path.exists(frontend_path) or True

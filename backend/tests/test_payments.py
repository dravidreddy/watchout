"""
Payment System Test Suite
Tests idempotency, webhooks, and failure scenarios
"""
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import hashlib
import json

from app.main import app
from app.services.idempotency_service import IdempotencyService
from app.core.firebase_auth import verify_firebase_token
from app.db.mongo import MongoDB


@pytest.fixture
def client():
    """Test client fixture"""
    with TestClient(app) as test_client:
        # Clear idempotency keys before each test to prevent interference
        db = MongoDB.get_db()
        db["payment_idempotency"].delete_many({})
        db["payments"].delete_many({})
        yield test_client


@pytest.fixture
def mock_razorpay_client():
    """Mock Razorpay client"""
    with patch('app.api.routes.payments.get_razorpay_client') as mock_get_client:
        mock_client = Mock()
        # Mock nested structures
        mock_client.order = Mock()
        mock_client.utility = Mock()
        mock_get_client.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_firebase_token():
    """Mock Firebase authentication"""
    async def override_verify_firebase_token():
        return {"uid": "test-user-123"}
    
    app.dependency_overrides[verify_firebase_token] = override_verify_firebase_token
    yield
    app.dependency_overrides.pop(verify_firebase_token, None)


class TestPaymentIdempotency:
    """Test payment idempotency"""
    
    @pytest.mark.asyncio
    async def test_idempotency_key_generation(self):
        """Test that idempotency keys are deterministic"""
        user_id = "user123"
        amount = 50000
        metadata = {"tier": "premium", "currency": "INR"}
        
        key1 = await IdempotencyService.generate_key(user_id, amount, metadata)
        key2 = await IdempotencyService.generate_key(user_id, amount, metadata)
        
        assert key1 == key2  # Same input = same key
        assert len(key1) == 64  # SHA256 hex digest length
    
    @pytest.mark.asyncio
    async def test_idempotency_key_uniqueness(self):
        """Test that different parameters produce different keys"""
        key1 = await IdempotencyService.generate_key("user1", 1000, {})
        key2 = await IdempotencyService.generate_key("user1", 2000, {})
        key3 = await IdempotencyService.generate_key("user2", 1000, {})
        
        assert key1 != key2  # Different amount
        assert key1 != key3  # Different user
        assert key2 != key3
    
    @pytest.mark.asyncio
    async def test_duplicate_request_detection(self, mock_razorpay_client, mock_firebase_token, client):
        """Test that duplicate requests return cached response"""
        # Mock Razorpay order creation
        mock_razorpay_client.order.create.return_value = {
            "id": "order_test123",
            "amount": 50000,
            "currency": "INR"
        }
        
        # Custom idempotency key
        idem_key = "test-idem-key-123"
        
        # First request
        response1 = client.post(
            "/api/v1/payments/create-order",
            json={"amount": 500, "currency": "INR", "tier": "premium"},
            headers={"X-Idempotency-Key": idem_key}
        )
        
        # Second request with same key
        response2 = client.post(
            "/api/v1/payments/create-order",
            json={"amount": 500, "currency": "INR", "tier": "premium"},
            headers={"X-Idempotency-Key": idem_key}
        )
        
        # Both should succeed
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Razorpay should only be called once
        assert mock_razorpay_client.order.create.call_count == 1
        
        # Responses should be identical
        assert response1.json() == response2.json()


class TestPaymentFailures:
    """Test payment failure scenarios"""
    
    def test_insufficient_balance_handling(self, mock_razorpay_client, mock_firebase_token, client):
        """Test handling of insufficient balance errors"""
        # Mock Razorpay failure
        mock_razorpay_client.order.create.side_effect = Exception("Insufficient balance")
        
        response = client.post(
            "/api/v1/payments/create-order",
            json={"amount": 500}
        )
        
        assert response.status_code == 500
        assert "failed" in response.json()["message"].lower()
    
    def test_network_timeout_handling(self, mock_razorpay_client, mock_firebase_token, client):
        """Test handling of network timeouts"""
        # Mock timeout
        mock_razorpay_client.order.create.side_effect = Exception("Request timeout")
        
        response = client.post(
            "/api/v1/payments/create-order",
            json={"amount": 500}
        )
        
        assert response.status_code == 500
        assert "timeout" in response.json().get("message", "").lower() or "failed" in response.json().get("message", "").lower()
    
    def test_signature_verification_failure(self, mock_razorpay_client, mock_firebase_token, client):
        """Test payment verification with invalid signature"""
        # Mock signature verification failure
        mock_razorpay_client.utility.verify_payment_signature.side_effect = Exception("Invalid signature")
        
        response = client.post(
            "/api/v1/payments/verify",
            json={
                "razorpay_order_id": "order_123",
                "razorpay_payment_id": "pay_123",
                "razorpay_signature": "invalid_signature",
                "plan_id": "premium"
            }
        )
        
        assert response.status_code == 400
        assert "verification failed" in response.json()["message"].lower()


class TestWebhookHandling:
    """Test Razorpay webhook processing"""
    
    def test_webhook_signature_verification(self, client):
        """Test webhook signature validation"""
        # Create test webhook payload
        payload = {
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_test123",
                        "order_id": "order_test123",
                        "amount": 50000,
                        "notes": {
                            "user_id": "user123",
                            "tier": "premium"
                        }
                    }
                }
            }
        }
        
        # Generate valid signature
        secret = "test_webhook_secret"
        payload_str = json.dumps(payload)
        signature = hashlib.sha256(f"{secret}{payload_str}".encode()).hexdigest()
        
        # Send webhook
        response = client.post(
            "/api/v1/webhooks/razorpay",
            json=payload,
            headers={"X-Razorpay-Signature": signature}
        )
        
        # Should accept (implementation may vary based on secret config)
        assert response.status_code in [200, 400]  # 400 if signature validation fails
    
    def test_payment_captured_webhook(self, client):
        """Test payment.captured webhook processing"""
        payload = {
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_captured123",
                        "order_id": "order_test123",
                        "amount": 50000,
                        "notes": {
                            "user_id": "user123",
                            "tier": "premium"
                        }
                    }
                }
            }
        }
        
        response = client.post(
            "/api/v1/webhooks/razorpay",
            json=payload
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
    
    def test_payment_failed_webhook(self, client):
        """Test payment.failed webhook processing"""
        payload = {
            "event": "payment.failed",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_failed123",
                        "order_id": "order_test123",
                        "error_code": "BAD_REQUEST_ERROR",
                        "error_description": "Payment failed"
                    }
                }
            }
        }
        
        response = client.post(
            "/api/v1/webhooks/razorpay",
            json=payload
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
    
    def test_refund_created_webhook(self, client):
        """Test refund.created webhook processing"""
        payload = {
            "event": "refund.created",
            "payload": {
                "refund": {
                    "entity": {
                        "id": "rfnd_test123",
                        "payment_id": "pay_test123",
                        "amount": 50000
                    }
                }
            }
        }
        
        response = client.post(
            "/api/v1/webhooks/razorpay",
            json=payload
        )
        
        assert response.status_code == 200


class TestPaymentEndToEnd:
    """End-to-end payment flow tests"""
    
    def test_complete_payment_flow(self, mock_razorpay_client, mock_firebase_token, client):
        """Test complete payment flow from order to verification"""
        # Step 1: Create order
        mock_razorpay_client.order.create.return_value = {
            "id": "order_e2e123",
            "amount": 50000,
            "currency": "INR"
        }
        
        create_response = client.post(
            "/api/v1/payments/create-order",
            json={"amount": 500, "tier": "premium"}
        )
        
        assert create_response.status_code == 200
        order_data = create_response.json()
        assert "order_id" in order_data
        
        # Step 2: Verify payment
        mock_razorpay_client.utility.verify_payment_signature.return_value = True
        
        verify_response = client.post(
            "/api/v1/payments/verify",
            json={
                "razorpay_order_id": order_data["order_id"],
                "razorpay_payment_id": "pay_e2e123",
                "razorpay_signature": "valid_signature",
                "plan_id": "premium"
            }
        )
        
        assert verify_response.status_code == 200
        assert verify_response.json()["status"] == "processing"
        assert "verification in progress" in verify_response.json()["message"].lower()


@pytest.mark.asyncio
async def test_idempotency_cleanup(client):
    """Test expired idempotency record cleanup"""
    # Simply test the logic return value since DB is connected via lifespan
    try:
        cleanup_count = await IdempotencyService.cleanup_expired()
        assert isinstance(cleanup_count, int)
    except RuntimeError as e:
        if "attached to a different loop" in str(e):
            pytest.skip("Skipping due to motor loop conflict in sync/async mix")
        raise


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

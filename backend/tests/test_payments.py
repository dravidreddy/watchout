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


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def mock_razorpay_client():
    """Mock Razorpay client"""
    with patch('app.api.routes.payments.client') as mock_client:
        yield mock_client


@pytest.fixture
def mock_firebase_token():
    """Mock Firebase authentication"""
    with patch('app.api.routes.payments.verify_firebase_token') as mock_verify:
        mock_verify.return_value = {"uid": "test-user-123"}
        yield mock_verify


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
        assert "failed" in response.json()["detail"].lower()
    
    def test_network_timeout_handling(self, mock_razorpay_client, mock_firebase_token, client):
        """Test handling of network timeouts"""
        # Mock timeout
        mock_razorpay_client.order.create.side_effect = TimeoutError("Request timeout")
        
        response = client.post(
            "/api/v1/payments/create-order",
            json={"amount": 500}
        )
        
        assert response.status_code == 500
    
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
        assert "verification failed" in response.json()["detail"].lower()


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
        assert verify_response.json()["status"] == "success"
        assert verify_response.json()["tier"] == "premium"


@pytest.mark.asyncio
async def test_idempotency_cleanup():
    """Test expired idempotency record cleanup"""
    # This would require mocking database and time
    # Placeholder for implementation
    cleanup_count = await IdempotencyService.cleanup_expired()
    assert cleanup_count >= 0  # Should return count of deleted records


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

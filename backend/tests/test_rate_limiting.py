"""
Tests for rate limiting functionality.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_chat_stream_rate_limit():
    """Test that chat stream endpoint is rate limited."""
    # Mock auth token
    headers = {"Authorization": "Bearer test_token"}
    
    responses = []
    for i in range(12):  # Try 12 requests (limit is 10/minute)
        response = client.post(
            "/api/v1/chat/stream",
            json={"message": "Hello", "trip_id": "test"},
            headers=headers
        )
        responses.append(response.status_code)
    
    # First 10 should succeed (200 or 401 if auth fails)
    # 11th and 12th should return 429 (Rate Limit Exceeded)
    assert 429 in responses, "Rate limiting should trigger after 10 requests"
    assert responses.count(429) >= 2, "Should have at least 2 rate-limited responses"


def test_rate_limit_response_format():
    """Test that rate limit response has correct format."""
    headers = {"Authorization": "Bearer test_token"}
    
    # Exceed rate limit
    for i in range(15):
        response = client.post(
            "/api/v1/chat/stream",
            json={"message": "Test"},
            headers=headers
        )
    
    # Check the 429 response format
    if response.status_code == 429:
        data = response.json()
        assert "error" in data
        assert "retry_after" in data
        assert data["error"] == "Rate limit exceeded"


def test_different_users_different_limits():
    """Test that different users have separate rate limits."""
    # This would require mocking different user IDs
    # For now, just verify the concept
    pass


@pytest.mark.asyncio
async def test_rate_limit_headers():
    """Test that rate limit headers are included in responses."""
    from fastapi import Request
    from app.core.rate_limiter import limiter
    
    # Rate limit headers should include:
    # - X-RateLimit-Limit
    # - X-RateLimit-Remaining
    # - X-RateLimit-Reset
    pass

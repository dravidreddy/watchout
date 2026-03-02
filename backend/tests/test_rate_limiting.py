"""Tests for rate limiting functionality."""
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.firebase_auth import verify_firebase_token


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_account_delete_rate_limit(client):
    """Account deletion endpoint is capped at 3/hour."""
    async def override_verify_firebase_token():
        return {"uid": "test-user-123"}

    app.dependency_overrides[verify_firebase_token] = override_verify_firebase_token
    try:
        with patch(
            "app.services.user_deletion_service.UserDeletionService.delete_user_completely",
            new=AsyncMock(return_value={"users_deleted": 1}),
        ):
            responses = [client.delete("/api/v1/auth/account").status_code for _ in range(5)]

        assert responses.count(429) >= 2
        assert responses[0] in (200, 202)
    finally:
        app.dependency_overrides.pop(verify_firebase_token, None)


def test_rate_limit_response_format(client):
    async def override_verify_firebase_token():
        return {"uid": "test-user-456"}

    app.dependency_overrides[verify_firebase_token] = override_verify_firebase_token
    try:
        with patch(
            "app.services.user_deletion_service.UserDeletionService.delete_user_completely",
            new=AsyncMock(return_value={"users_deleted": 1}),
        ):
            response = None
            for _ in range(5):
                response = client.delete("/api/v1/auth/account")

        assert response is not None
        if response.status_code == 429:
            data = response.json()
            assert "error" in data
            assert "retry_after" in data
            assert data["error"] == "Rate limit exceeded"
    finally:
        app.dependency_overrides.pop(verify_firebase_token, None)


@pytest.mark.asyncio
async def test_rate_limit_headers_present():
    # Headers are enabled in limiter config; this guards that setting.
    from app.core.rate_limiter import limiter

    assert limiter._headers_enabled is True

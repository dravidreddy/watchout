import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.main import app
from app.core.config import settings
from app.core.firebase_auth import verify_firebase_token


DEV_HEADERS = {"X-Test-Bypass-Token": settings.dev_bypass_secret}


@pytest.fixture(autouse=True)
def setup_dev_env():
    """Ensure dev environment is active for tests."""
    original_env = settings.app_env
    settings.app_env = "development"
    yield
    settings.app_env = original_env


def test_legacy_chat_message_endpoint_removed():
    """/chat/message was replaced by /chat/stream and should stay unavailable."""
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/chat/message",
            headers=DEV_HEADERS,
            json={"message": "I want to go to Goa", "context": {}},
        )
        assert response.status_code == 404


def test_trip_creation_api():
    """Test trip creation without touching real MongoDB."""
    async def override_verify_firebase_token():
        return {"uid": "test-user-123"}

    mock_insert_result = type("InsertResult", (), {"inserted_id": "mocked-trip-id"})
    mock_trips = AsyncMock()
    mock_trips.insert_one = AsyncMock(return_value=mock_insert_result)
    mock_trips.find_one = AsyncMock(
        return_value={
            "_id": "mocked-trip-id",
            "trip_id": "mocked-trip-id",
            "user_id": "test-user-123",
            "title": "QA Test Trip",
            "cities": ["Mumbai"],
            "num_travelers": 2,
            "status": "planning",
            "tags": [],
            "is_public": False,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }
    )

    app.dependency_overrides[verify_firebase_token] = override_verify_firebase_token
    with patch("app.api.routes.trips.check_trip_limit", new=AsyncMock(return_value=None)), patch(
        "app.api.routes.trips.trips_collection", return_value=mock_trips
    ):
        with TestClient(app) as client:
            trip_data = {
                "title": "QA Test Trip",
                "cities": ["Mumbai"],
                "num_travelers": 2,
                "budget_total": 50000,
            }

            response = client.post("/api/v1/trips/", json=trip_data)
            assert response.status_code == 200
            data = response.json()
            assert "trip_id" in data
            assert data["status"] == "created"

    app.dependency_overrides.pop(verify_firebase_token, None)


def test_protected_route_access():
    """Verify protected route works with explicit auth override."""
    async def override_verify_firebase_token():
        return {"uid": "test-user-123", "email": "qa@watchout.app", "name": "QA"}

    app.dependency_overrides[verify_firebase_token] = override_verify_firebase_token
    try:
        with patch("app.api.routes.auth.users_collection") as mock_users_collection:
            mock_users = AsyncMock()
            mock_users.find_one = AsyncMock(
                return_value={
                    "_id": "user1",
                    "firebase_id": "test-user-123",
                    "email": "qa@watchout.app",
                    "name": "QA",
                    "preferences": {},
                    "onboarding_completed": True,
                    "subscription_tier": "free",
                    "created_at": "2026-01-01T00:00:00Z",
                }
            )
            mock_users_collection.return_value = mock_users
            with TestClient(app) as client:
                response = client.get("/api/v1/auth/me")
                assert response.status_code == 200
    finally:
        app.dependency_overrides.pop(verify_firebase_token, None)

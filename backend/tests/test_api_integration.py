import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

# Common headers for Dev Bypass
DEV_HEADERS = {
    "X-Test-Bypass-Token": settings.dev_bypass_secret
}

@pytest.fixture(autouse=True)
def setup_dev_env():
    """Ensure dev environment is active for tests."""
    original_env = settings.app_env
    settings.app_env = "development"
    yield
    settings.app_env = original_env

def test_clarification_agent_api():
    """Test Chat Agent Endpoint via API."""
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/chat/message",
            headers=DEV_HEADERS,
            json={"message": "I want to go to Goa", "context": {}}
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        # assert "is_complete" in data # Response format is different for /message

def test_trip_creation_api():
    """Test Trip Creation Endpoint via API (Full Flow)."""
    with TestClient(app) as client:
        trip_data = {
            "title": "QA Test Trip",
            "cities": ["Mumbai"],
            "num_travelers": 2,
            "budget_total": 50000
        }
        
        response = client.post(
            "/api/v1/trips/", 
            headers=DEV_HEADERS,
            json=trip_data
        )
        assert response.status_code == 200
        data = response.json()
        assert "trip_id" in data
        assert data["status"] == "created"
        
        # Verify Trip Retrieval
        trip_id = data["trip_id"]
        get_response = client.get(f"/api/v1/trips/{trip_id}", headers=DEV_HEADERS)
        assert get_response.status_code == 200
        trip_details = get_response.json()
        assert trip_details["title"] == "QA Test Trip"

def test_protected_route_access():
    """Verify protected route works with bypass."""
    with TestClient(app) as client:
        response = client.get("/api/v1/auth/me", headers=DEV_HEADERS)
        assert response.status_code == 200
        assert response.json()["email"] == "qa@watchout.app"

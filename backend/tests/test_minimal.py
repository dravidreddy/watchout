from fastapi.testclient import TestClient
from app.main import app

def test_health():
    with TestClient(app) as client:
        response = client.get("/health")
        print(f"Health Response: {response.status_code} {response.text}")
        assert response.status_code == 200

def test_api_route():
    with TestClient(app) as client:
        # Check a GET route that doesn't need auth (if any exists) or check 401 instead of 404
        # /api/v1/auth/me requires auth, likely 401 if missing header, but DEFINITELY not 404.
        response = client.get("/api/v1/auth/me")
        print(f"Auth Me Response: {response.status_code} {response.text}")
        assert response.status_code != 404

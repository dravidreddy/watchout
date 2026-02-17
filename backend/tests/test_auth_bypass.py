import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

def test_auth_bypass_success():
    """Test that valid bypass token returns mock user."""
    with TestClient(app) as client:
        # Ensure we are in development mode for the test
        original_env = settings.app_env
        settings.app_env = "development"
        
        headers = {
            "X-Test-Bypass-Token": settings.dev_bypass_secret
        }
        
        try:
            response = client.get("/api/v1/auth/me", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == "qa@watchout.app"
            assert data["is_dev_bypass"] is True
        finally:
            settings.app_env = original_env

def test_auth_bypass_failure_wrong_token():
    """Test that invalid bypass token fails."""
    with TestClient(app) as client:
        # Ensure dev env
        original_env = settings.app_env
        settings.app_env = "development"
        
        headers = {
            "X-Test-Bypass-Token": "wrong-secret"
        }
        try:
            response = client.get("/api/v1/auth/me", headers=headers)
            assert response.status_code == 401
        finally:
            settings.app_env = original_env

def test_auth_bypass_failure_no_token():
    """Test that missing token fails (when no real auth provided)."""
    with TestClient(app) as client:
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

DEV_HEADERS = {"X-Test-Bypass-Token": settings.dev_bypass_secret}

def test_trips_debug():
    with TestClient(app) as client:
        # 1. Try with slash
        r1 = client.post("/api/v1/trips/", headers=DEV_HEADERS, json={"title": "Test", "cities": ["Mumbai"], "num_travelers": 1, "budget_total": 1000})
        print(f"POST /trips/ -> {r1.status_code}")
        
        # 2. Try without slash
        r2 = client.post("/api/v1/trips", headers=DEV_HEADERS, json={"title": "Test", "cities": ["Mumbai"], "num_travelers": 1, "budget_total": 1000})
        print(f"POST /trips -> {r2.status_code}")
        
        assert r1.status_code == 200 or r2.status_code == 200

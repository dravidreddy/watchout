from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.core.firebase_auth import verify_firebase_token


def test_trips_debug():
    async def override_verify_firebase_token():
        return {"uid": "test-user-123"}

    app.dependency_overrides[verify_firebase_token] = override_verify_firebase_token
    try:
        mock_trips = AsyncMock()
        mock_trips.insert_one = AsyncMock(return_value=None)

        with patch("app.api.routes.trips.check_trip_limit", new=AsyncMock(return_value=None)), patch(
            "app.api.routes.trips.trips_collection", return_value=mock_trips
        ):
            with TestClient(app) as client:
                payload = {
                    "title": "Test",
                    "cities": ["Mumbai"],
                    "num_travelers": 1,
                    "budget_total": 1000,
                }
                r1 = client.post("/api/v1/trips/", json=payload)
                r2 = client.post("/api/v1/trips", json=payload)

                assert r1.status_code == 200 or r2.status_code in (200, 307, 308)
    finally:
        app.dependency_overrides.pop(verify_firebase_token, None)

from datetime import datetime, timedelta, timezone

import pytest

from app.models.chat import ChatRequest
from app.models.trip import TripCreate


def test_chat_request_sanitizes_html() -> None:
    request = ChatRequest(message="  <b>Hello</b>   world  ")
    assert request.message == "Hello world"


def test_chat_request_rejects_empty() -> None:
    with pytest.raises(ValueError):
        ChatRequest(message="<script></script>")


def test_trip_create_validates_dates() -> None:
    start = (datetime.now(timezone.utc) + timedelta(days=5)).date()
    end = start + timedelta(days=2)
    trip = TripCreate(cities=["Goa"], start_date=start, end_date=end)
    assert trip.num_days == 3

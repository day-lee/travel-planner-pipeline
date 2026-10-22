"""Unit tests for weather API ingestion retries."""

import pytest

from ingest import api_weather


CITY = {
    "city_id": "SYD",
    "city_name": "Sydney",
    "latitude": -33.8688,
    "longitude": 151.2093,
    "timezone": "Australia/Sydney",
}


class DummyResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


def test_fetch_weather_retries_then_succeeds(monkeypatch):
    calls = {"count": 0}
    sleeps = []
    expected = {"daily": {"precipitation_sum": [0.1]}}

    def fake_get(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] < 3:
            raise api_weather.requests.exceptions.ReadTimeout("timed out")
        return DummyResponse(expected)

    monkeypatch.setattr(api_weather.requests, "get", fake_get)
    monkeypatch.setattr(api_weather.time, "sleep", lambda seconds: sleeps.append(seconds))

    weather = api_weather.fetch_weather(CITY)

    assert weather == expected
    assert calls["count"] == 3
    assert sleeps == [1, 2]


def test_fetch_weather_raises_after_max_attempts(monkeypatch):
    calls = {"count": 0}
    sleeps = []

    def fake_get(*args, **kwargs):
        calls["count"] += 1
        raise api_weather.requests.exceptions.ReadTimeout("timed out")

    monkeypatch.setattr(api_weather.requests, "get", fake_get)
    monkeypatch.setattr(api_weather.time, "sleep", lambda seconds: sleeps.append(seconds))

    with pytest.raises(RuntimeError, match="Failed to fetch weather data for Sydney."):
        api_weather.fetch_weather(CITY)

    assert calls["count"] == api_weather.MAX_FETCH_ATTEMPTS
    assert sleeps == [1, 2]

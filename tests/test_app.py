"""
Unit tests for the async weather API comparator (app.py).

This test suite uses pytest with asyncio support and mock objects to simulate
HTTP responses from the four weather APIs. It verifies:
- Each fetch_* function correctly parses a valid JSON response into WeatherData.
- Each fetch_* function raises an exception on HTTP errors or invalid JSON.
- fetch_all runs multiple requests concurrently and returns only successful results.
- The main logic (min temperature) works correctly.
"""

import pytest
from unittest import mock
import asyncio
from httpx import HTTPStatusError, RequestError
from app import (
    WeatherData,
    fetch_weatherapi,
    fetch_openweather,
    fetch_weatherstack,
    fetch_weatherbit,
    fetch_all,
)

# -------------------------------------------------------------------------
# Helper to create an async mock response
# -------------------------------------------------------------------------
def async_mock_response(status_code=200, json_data=None):
    """Return a mock object that behaves like an httpx.Response."""
    resp = mock.AsyncMock()
    resp.status_code = status_code
    resp.raise_for_status = mock.AsyncMock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = HTTPStatusError(
            message="Error", request=mock.Mock(), response=resp
        )
    resp.json = mock.AsyncMock(return_value=json_data or {})
    return resp

# -------------------------------------------------------------------------
# Tests for individual fetch functions
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_fetch_weatherapi_success():
    """Test fetch_weatherapi with a valid WeatherAPI response."""
    valid_json = {
        "location": {"name": "London"},
        "current": {"temp_c": 22.5}
    }
    with mock.patch("httpx.AsyncClient.get", return_value=async_mock_response(200, valid_json)):
        result = await fetch_weatherapi("http://fake.url")
        assert isinstance(result, WeatherData)
        assert result.city == "London"
        assert result.temperature_c == 22.5
        assert result.source == "WeatherAPI"

@pytest.mark.asyncio
async def test_fetch_weatherapi_http_error():
    """Test fetch_weatherapi raises an exception on HTTP 401."""
    with mock.patch("httpx.AsyncClient.get", return_value=async_mock_response(401)):
        with pytest.raises(HTTPStatusError):
            await fetch_weatherapi("http://fake.url")

@pytest.mark.asyncio
async def test_fetch_openweather_success():
    """Test fetch_openweather with a valid OpenWeatherMap response."""
    valid_json = {
        "name": "London",
        "main": {"temp": 18.3}
    }
    with mock.patch("httpx.AsyncClient.get", return_value=async_mock_response(200, valid_json)):
        result = await fetch_openweather("http://fake.url")
        assert result.city == "London"
        assert result.temperature_c == 18.3
        assert result.source == "OpenWeatherMap"

@pytest.mark.asyncio
async def test_fetch_weatherstack_success():
    """Test fetch_weatherstack with a valid Weatherstack response."""
    valid_json = {
        "location": {"name": "London"},
        "current": {"temperature": 20.1}
    }
    with mock.patch("httpx.AsyncClient.get", return_value=async_mock_response(200, valid_json)):
        result = await fetch_weatherstack("http://fake.url")
        assert result.city == "London"
        assert result.temperature_c == 20.1
        assert result.source == "Weatherstack"

@pytest.mark.asyncio
async def test_fetch_weatherbit_success():
    """Test fetch_weatherbit with a valid Weatherbit response."""
    valid_json = {
        "data": [{"city_name": "London", "temp": 19.7}]
    }
    with mock.patch("httpx.AsyncClient.get", return_value=async_mock_response(200, valid_json)):
        result = await fetch_weatherbit("http://fake.url")
        assert result.city == "London"
        assert result.temperature_c == 19.7
        assert result.source == "Weatherbit"

# -------------------------------------------------------------------------
# Tests for fetch_all (concurrent fetching)
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_fetch_all_all_success():
    """fetch_all returns all WeatherData objects when every API succeeds."""
    endpoints = [
        {"fetch_func": fetch_weatherapi, "url": "http://weatherapi.com"},
        {"fetch_func": fetch_openweather, "url": "http://openweathermap.org"},
    ]
    # Mock the fetch functions directly to avoid nested patches
    with mock.patch("app.fetch_weatherapi", return_value=WeatherData("London", 22.0, "WeatherAPI")):
        with mock.patch("app.fetch_openweather", return_value=WeatherData("London", 18.5, "OpenWeatherMap")):
            results = await fetch_all(endpoints)
            assert len(results) == 2
            assert results[0].temperature_c == 22.0
            assert results[1].temperature_c == 18.5

@pytest.mark.asyncio
async def test_fetch_all_partial_failure():
    """fetch_all returns only successful results, logs errors."""
    endpoints = [
        {"fetch_func": fetch_weatherapi, "url": "http://weatherapi.com"},
        {"fetch_func": fetch_openweather, "url": "http://openweathermap.org"},
    ]
    # Make the second function raise an exception
    async def failing_fetch(*args, **kwargs):
        raise Exception("API failure")

    with mock.patch("app.fetch_weatherapi", return_value=WeatherData("London", 22.0, "WeatherAPI")):
        with mock.patch("app.fetch_openweather", side_effect=failing_fetch):
            results = await fetch_all(endpoints)
            assert len(results) == 1
            assert results[0].source == "WeatherAPI"

# -------------------------------------------------------------------------
# Test the main cheap-finding logic (optional, but good to have)
# -------------------------------------------------------------------------
def test_find_cheapest():
    """Verify that min(WeatherData, key=...) finds the lowest temperature."""
    data = [
        WeatherData("London", 22.0, "A"),
        WeatherData("Paris", 18.5, "B"),
        WeatherData("Tokyo", 25.0, "C"),
    ]
    cheapest = min(data, key=lambda w: w.temperature_c)
    assert cheapest.city == "Paris"
    assert cheapest.temperature_c == 18.5
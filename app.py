# =============================================================================
# app.py - Async Weather API Comparator (Fully Commented)
# =============================================================================
# This script demonstrates asynchronous HTTP requests using asyncio and httpx.
# It calls 4 different weather APIs in parallel, parses each response according
# to its unique JSON structure, prints every successful result, and finally
# reports the lowest temperature (the "cheapest" in terms of temperature).
# 
# Key concepts shown:
#   - async/await and event loop
#   - Pydantic models for data validation
#   - Handling different API response schemas
#   - Concurrent execution with asyncio.gather()
#   - Error resilience (one failing API does not crash the whole script)
#   - Environment variables for API keys
#   - Timing execution to observe async speedup
# =============================================================================

# ---------- Standard library imports ----------
import asyncio        # Provides async/await, event loop, and asyncio.gather()
import logging        # For logging errors and info messages (instead of print)
import os             # To read environment variables (API keys) from the system
import time           # To measure elapsed wall-clock time
from dataclasses import dataclass   # A decorator to create simple data containers
from typing import List, Dict       # Type hints for lists and dictionaries

# ---------- Third-party imports ----------
import httpx          # Modern async HTTP client (supports HTTP/2)
from dotenv import load_dotenv   # Loads key=value pairs from a .env file into os.environ
from pydantic import BaseModel   # For data validation and parsing using Python type hints

# -----------------------------------------------------------------------------
# Load environment variables from a file named `.env` in the same directory.
# This file should contain lines like:
#   WEATHERAPI_KEY=your_key_here
#   OPENWEATHER_API_KEY=your_key_here
#   WEATHERSTACK_ACCESS_KEY=your_key_here
#   WEATHERBIT_API_KEY=your_key_here
# -----------------------------------------------------------------------------
load_dotenv()

# Configure logging: level INFO shows main events; change to DEBUG for more details.
logging.basicConfig(level=logging.INFO)

# =============================================================================
# 1. Common data structure to unify results from all APIs
# =============================================================================
@dataclass
class WeatherData:
    """
    A simple container (dataclass) that holds normalized weather information.
    Every API fetch function will return an object of this type.
    """
    city: str               # Name of the city (e.g., "London")
    temperature_c: float    # Temperature in degrees Celsius
    source: str             # Name of the API that provided this data

# =============================================================================
# 2. API-specific models and fetch functions
# =============================================================================

# -----------------------------------------------------------------------------
# API 1: WeatherAPI (weatherapi.com)
# -----------------------------------------------------------------------------
class WeatherAPIResponse(BaseModel):
    """
    Pydantic model for the JSON response from WeatherAPI.
    Expected structure:
        {
            "location": {"name": "London", ...},
            "current": {"temp_c": 22.3, ...}
        }
    Pydantic automatically checks that these fields exist and have the correct types.
    """
    location: dict   # The 'location' field must be a dictionary
    current: dict    # The 'current' field must be a dictionary

    @property
    def city(self) -> str:
        """A helper property to extract the city name from the nested 'location' dict."""
        return self.location.get("name", "Unknown")

    @property
    def temperature(self) -> float:
        """Helper to extract temperature in Celsius from the nested 'current' dict."""
        return self.current.get("temp_c", 0.0)

async def fetch_weatherapi(url: str) -> WeatherData:
    """
    Fetch weather data from WeatherAPI, parse with Pydantic, and return a WeatherData object.
    The 'async def' makes this a coroutine – it can be paused with 'await'.
    """
    # Use 'async with' to create an async HTTP client that automatically closes when done.
    async with httpx.AsyncClient() as client:
        # 'await' yields control back to the event loop while the network request is in progress.
        # The event loop can run other tasks during this time.
        resp = await client.get(url)

        # Raise an exception if the HTTP status code is 4xx or 5xx.
        # This will be caught by the caller's exception handling.
        resp.raise_for_status()

        # Parse the JSON response into our Pydantic model.
        # The ** unpacks the dictionary into keyword arguments.
        data = WeatherAPIResponse(**resp.json())

        # Return a unified WeatherData object.
        return WeatherData(
            city=data.city,
            temperature_c=data.temperature,
            source="WeatherAPI"
        )

# -----------------------------------------------------------------------------
# API 2: OpenWeatherMap
# -----------------------------------------------------------------------------
class OpenWeatherResponse(BaseModel):
    """
    Pydantic model for OpenWeatherMap's current weather response.
    Expected structure:
        {
            "name": "London",
            "main": {"temp": 22.3, ...}
        }
    """
    name: str        # The city name is at the top level under 'name'
    main: dict       # The 'main' object contains temperature, pressure, etc.

    @property
    def temperature(self) -> float:
        """Extract temperature from the 'main' dictionary."""
        return self.main.get("temp", 0.0)

async def fetch_openweather(url: str) -> WeatherData:
    """Fetch from OpenWeatherMap, parse, and return a WeatherData object."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = OpenWeatherResponse(**resp.json())
        return WeatherData(
            city=data.name,
            temperature_c=data.temperature,
            source="OpenWeatherMap"
        )

# -----------------------------------------------------------------------------
# API 3: Weatherstack
# -----------------------------------------------------------------------------
class WeatherstackResponse(BaseModel):
    """
    Pydantic model for Weatherstack response.
    Expected structure:
        {
            "location": {"name": "London"},
            "current": {"temperature": 22.3}
        }
    Note: Weatherstack uses "temperature" (not "temp_c").
    """
    location: dict
    current: dict

    @property
    def city(self) -> str:
        return self.location.get("name", "Unknown")

    @property
    def temperature(self) -> float:
        return self.current.get("temperature", 0.0)

async def fetch_weatherstack(url: str) -> WeatherData:
    """Fetch from Weatherstack, parse, return WeatherData."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = WeatherstackResponse(**resp.json())
        return WeatherData(
            city=data.city,
            temperature_c=data.temperature,
            source="Weatherstack"
        )

# -----------------------------------------------------------------------------
# API 4: Weatherbit
# -----------------------------------------------------------------------------
class WeatherbitResponse(BaseModel):
    """
    Pydantic model for Weatherbit response.
    Expected structure:
        {
            "data": [
                {"city_name": "London", "temp": 22.3}
            ]
        }
    """
    data: list      # The 'data' field is a list of weather records

    @property
    def city(self) -> str:
        """Extract city name from the first element of the 'data' list."""
        if self.data:
            return self.data[0].get("city_name", "Unknown")
        return "Unknown"

    @property
    def temperature(self) -> float:
        """Extract temperature from the first element of the 'data' list."""
        if self.data:
            return self.data[0].get("temp", 0.0)
        return 0.0

async def fetch_weatherbit(url: str) -> WeatherData:
    """Fetch from Weatherbit, parse, return WeatherData."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = WeatherbitResponse(**resp.json())
        return WeatherData(
            city=data.city,
            temperature_c=data.temperature,
            source="Weatherbit"
        )

# =============================================================================
# 3. Concurrent fetching logic
# =============================================================================
async def fetch_all(endpoints: List[Dict]) -> List[WeatherData]:
    """
    Execute all API fetch functions concurrently.

    Args:
        endpoints: A list of dictionaries, each containing:
            - "fetch_func": an async function that takes a URL and returns WeatherData
            - "url": the full endpoint URL (including API keys)

    Returns:
        A list of WeatherData objects for all successful requests.
        Failed requests are logged but do not appear in the returned list.
    """
    # Build a list of coroutines (each is an async function call)
    tasks = []
    for ep in endpoints:
        # ep["fetch_func"] is e.g., fetch_weatherapi, and ep["url"] is the URL string.
        tasks.append(ep["fetch_func"](ep["url"]))

    # Run all tasks concurrently. 'return_exceptions=True' means that if any task
    # raises an exception, that exception is returned as a value instead of crashing
    # the whole gather. This allows us to handle failures individually.
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter the results: keep only those that are WeatherData objects.
    valid = []
    for r in results:
        if isinstance(r, WeatherData):
            valid.append(r)
        else:
            # r is an Exception object (or other non-WeatherData)
            logging.error(f"Request failed: {r}")

    return valid

# =============================================================================
# 4. Main asynchronous entry point
# =============================================================================
async def main():
    """
    Build the list of API endpoints, call fetch_all(), print every successful result,
    then find and display the cheapest (lowest temperature) along with execution time.
    """
    # Define the endpoints. Each entry pairs a fetch function with the complete URL.
    # The API keys are read from environment variables (loaded from .env).
    endpoints = [
        {
            "fetch_func": fetch_weatherapi,
            "url": f"http://api.weatherapi.com/v1/current.json?key={os.getenv('WEATHERAPI_KEY')}&q=London"
        },
        #{
        #    "fetch_func": fetch_openweather,
        #    "url": f"https://api.openweathermap.org/data/2.5/weather?q=London&appid={os.getenv('OPENWEATHER_API_KEY')}&units=metric"
        #},
        {
            "fetch_func": fetch_weatherstack,
            "url": f"http://api.weatherstack.com/current?access_key={os.getenv('WEATHERSTACK_ACCESS_KEY')}&query=London"
        },
        {
            "fetch_func": fetch_weatherbit,
            "url": f"https://api.weatherbit.io/v2.0/current?city=London&country=UK&key={os.getenv('WEATHERBIT_API_KEY')}"
        },
    ]

    # Record the start time using high-resolution perf_counter.
    start_time = time.perf_counter()

    # Fetch all APIs concurrently.
    results = await fetch_all(endpoints)

    # Calculate elapsed time.
    elapsed = time.perf_counter() - start_time

    # If no API succeeded, print an error message and exit.
    if not results:
        print("❌ No successful API calls. Check your API keys and network.")
        return

    # --- Print all successful results ---
    print("\n🌍 Weather data from all APIs:\n")
    for w in results:
        # Print each result with fixed width (15 characters) and one decimal place.
        print(f"   {w.source:15} : {w.city} – {w.temperature_c:.1f}°C")

    # --- Find the cheapest (lowest temperature) ---
    # The min() function uses the key to extract the temperature from each WeatherData object.
    cheapest = min(results, key=lambda w: w.temperature_c)

    # --- Print the cheapest result and timing ---
    print(f"\n✅ Cheapest weather: {cheapest.city} – {cheapest.temperature_c:.1f}°C (from {cheapest.source})")
    print(f"⏱️  Time taken (async): {elapsed:.2f} seconds\n")

# =============================================================================
# 5. Script entry point
# =============================================================================
if __name__ == "__main__":
    # asyncio.run() creates a new event loop, runs the main() coroutine,
    # and then closes the loop. This is the standard way to start an async program.
    asyncio.run(main())
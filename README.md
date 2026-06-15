# 🌦️ Async Weather API Comparator

Python project that demonstrates **asynchronous programming** by fetching weather data from **four different weather APIs** concurrently, printing all temperatures, and identifying the “cheapest” (lowest temperature). The code uses **Pydantic** for response validation, and is managed with **uv** – the fast, modern Python package manager.

---

## 📖 Table of Contents

- [The Async Analogy](#the-async-analogy)
- [Features](#features)
- [How It Works](#how-it-works)
- [Requirements](#requirements)
- [Setup from Scratch](#setup-from-scratch)
- [Usage](#usage)
- [Expected Output](#expected-output)
- [Project Structure](#project-structure)
- [Code Explanation](#code-explanation)
  - [Async / Await & Concurrency](#async--await--concurrency)
  - [Pydantic Models](#pydantic-models)
  - [Error Handling](#error-handling)
  - [Environment Variables](#environment-variables)
- [Testing](#testing)
- [Customisation](#customisation)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## The Async Analogy

Imagine a restaurant with **one cashier** (the CPU thread):

- **Sequential (synchronous):**  
  Cashier takes order from Customer 1, walks to the kitchen, waits for the food to cook, brings it back, then moves to Customer 2.  
  Total time = sum of all cooking times. 🐢

- **Concurrent (asynchronous):**  
  Cashier takes orders from **all customers at once**, then as each dish finishes, rushes to serve it.  
  Total time ≈ the longest cooking time – **not the sum**. ⚡

The same cashier (one thread) handles all waiting concurrently, without needing extra workers. This is exactly how `asyncio` works – it keeps the CPU busy while waiting for slow I/O (like network requests).

---

## Features

- ✅ **Async concurrent requests** – calls 4 weather APIs in parallel (add as many as you like).
- ✅ **Pydantic validation** – each API’s JSON response is validated and parsed into a clean data model.
- ✅ **Unified output** – all results are converted to a common `WeatherData` dataclass.
- ✅ **Error resilience** – one failing API does not crash the others.
- ✅ **Timing measurement** – shows the real speed advantage of async I/O.
- ✅ **Fully commented code** – every line explained, ideal for learning.
- ✅ **Test suite** – unit tests with `pytest` and `pytest-asyncio`.
- ✅ **Modern Python** – uses `uv` for lightning‑fast dependency management.

---

## How It Works

1. You provide API keys for four weather services in a `.env` file.
2. The script builds a list of endpoint URLs.
3. All four requests are fired **concurrently** using `asyncio.gather()`.
4. Each response is validated with a dedicated Pydantic model.
5. Successful results are printed, and the lowest temperature (the “cheapest”) is displayed along with the total execution time.

---

## Requirements

- **Python 3.10 or higher** (uses modern typing and `asyncio` features)
- **uv** – fast Python package manager ([install uv](https://docs.astral.sh/uv/getting-started/installation/))
- API keys from (free tiers are fine):
  - [WeatherAPI](https://www.weatherapi.com/signup.aspx)
  - [OpenWeatherMap](https://openweathermap.org/api)
  - [Weatherstack](https://weatherstack.com/signup/free)
  - [Weatherbit](https://www.weatherbit.io/account/create)

---

## Setup from Scratch

### 1. Clone or create the project folder

```bash
mkdir weather-comparator && cd weather-comparator
```

### 2. Create the following files

Copy the contents below into your editor:

- `app.py` – (the fully commented script – [see final code above](#))
- `pyproject.toml` – project dependencies
- `.gitignore` – standard Python ignores
- `tests/test_app.py` – unit tests

### 3. Create the virtual environment and install dependencies

```bash
uv sync
```

This reads `pyproject.toml`, creates a `.venv` folder, and installs all required packages (`httpx`, `pydantic`, `python-dotenv`, plus `pytest` for development).

### 4. Set up environment variables

Create a `.env` file in the project root:

```env
WEATHERAPI_KEY=your_weatherapi_key_here
OPENWEATHER_API_KEY=your_openweather_key_here
WEATHERSTACK_ACCESS_KEY=your_weatherstack_key_here
WEATHERBIT_API_KEY=your_weatherbit_key_here
```

> ⚠️ **Never commit `.env` to version control** – it is already ignored by `.gitignore`.

### 5. Run the script

```bash
uv run python app.py
```

Or activate the environment first:

```bash
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows
python app.py
```

---

## Usage

Simply run the script. No command‑line arguments are required – all configuration is done via `.env`.

If you want to test a different city, edit the `q=` or `query=` parameter inside each URL in the `endpoints` list (e.g., change `London` to `Paris`).

---

## Expected Output

When all API keys are valid, you will see something like:

```
🌍 Weather data from all APIs:

   WeatherAPI      : London – 22.3°C
   OpenWeatherMap  : London – 21.8°C
   Weatherstack    : London – 22.1°C
   Weatherbit      : City of London – 21.5°C

✅ Cheapest weather: City of London – 21.5°C (from Weatherbit)
⏱️  Time taken (async): 0.85 seconds
```

If some APIs fail (e.g., invalid key), only successful ones appear, and errors are logged.

---

## Project Structure

```
weather-comparator/
├── .env                      # API keys (not committed)
├── .gitignore                # Ignores .venv, __pycache__, etc.
├── pyproject.toml            # Project metadata and dependencies
├── README.md                 # This file
├── app.py                    # Main async script
└── tests/
    └── test_app.py           # Unit tests (pytest)
```

---

## Code Explanation

### Async / Await & Concurrency

- `async def` – defines a coroutine (pausable function).
- `await` – yields control back to the event loop while waiting for an I/O operation.
- `asyncio.gather()` – runs multiple coroutines concurrently.  
  **Result:** 4 requests of 1 second each take ~1 second total, not 4 seconds.

```python
async def fetch_weatherapi(url):
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)   # <-- yields control
        return resp.json()
```

### Pydantic Models

Each API returns a different JSON shape. Pydantic models:

- Validate that required fields exist and have the right types.
- Provide clean attribute access via properties.

```python
class WeatherAPIResponse(BaseModel):
    location: dict
    current: dict

    @property
    def temperature(self) -> float:
        return self.current.get("temp_c", 0.0)
```

### Error Handling

- `return_exceptions=True` in `asyncio.gather` prevents one failed task from cancelling others.
- Exceptions are logged, but successful results are still returned.

```python
results = await asyncio.gather(*tasks, return_exceptions=True)
valid = [r for r in results if isinstance(r, WeatherData)]
```

### Environment Variables

- `python-dotenv` loads `.env` into `os.environ`.
- Keys are accessed with `os.getenv('VAR_NAME')` – never hard‑coded.

---

## Testing

The project includes a complete test suite using `pytest` and `pytest-asyncio`.

### Run all tests

```bash
uv run pytest tests/ -v
```

### Example test

```python
@pytest.mark.asyncio
async def test_fetch_weatherapi_success():
    valid_json = {"location": {"name": "London"}, "current": {"temp_c": 22.5}}
    with mock.patch("httpx.AsyncClient.get", return_value=async_mock_response(200, valid_json)):
        result = await fetch_weatherapi("http://fake.url")
        assert result.city == "London" and result.temperature_c == 22.5
```

The tests verify:
- Each fetch function parses valid JSON correctly.
- HTTP errors (401, 404) raise exceptions.
- `fetch_all` returns only successful results when some APIs fail.
- The cheap‑finding logic (lowest temperature) works.

---

## Customisation

### Add more weather APIs

1. Write a new fetch function with its own Pydantic model.
2. Append an entry to the `endpoints` list in `main()`.

### Compare API cost instead of temperature

Replace `temperature_c` with a `price_per_call` field (e.g., from a configuration dictionary). Then change the key in `min(results, key=lambda w: w.price)`.

### Change city

Edit the `q=London` or `query=London` in each URL inside `main()`.

### Run sequentially for comparison

Uncomment a sequential version (using `requests.get` in a for‑loop) to see the speed difference.

---

## Troubleshooting

| Problem | Likely cause | Solution |
|---------|--------------|----------|
| `401 Unauthorized` | Invalid or missing API key | Check `.env` variable name and key value. OpenWeatherMap keys can take up to 2 hours to activate. |
| `ValidationError` | API response structure changed | Verify the JSON structure with `curl` and update the Pydantic model. |
| `ModuleNotFoundError` | Dependencies not installed | Run `uv sync` again. |
| No output / all errors | All API keys invalid | Enable `logging.DEBUG` in `app.py` to see raw responses. |

---

## License

This project is licensed under the **MIT License** – you are free to use, modify, and distribute it.

---

## Acknowledgements

- Built with Python’s `asyncio` and `httpx`.
- Data validation powered by Pydantic.
- Dependency management with `uv` (Astral).

---
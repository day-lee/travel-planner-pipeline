"""Fetch and save weather data"""

import json
import time
from datetime import datetime
from pathlib import Path

import requests


CURRENT_YEAR = datetime.now().year
OPEN_METEO_WEATHER_URL = "https://archive-api.open-meteo.com/v1/archive"
START_DATE = "2020-01-01"
END_DATE = f"{CURRENT_YEAR - 1}-12-31"
WEATHER_RAW_DIR = Path("data/weather")
CITIES_PATH = Path("sql/0_seed/cities_weather_thresholds.json")

DAILY_VARIABLES = (
    "precipitation_sum",
    "apparent_temperature_max",
    "apparent_temperature_min",
    "wind_speed_10m_max",
    "wind_gusts_10m_max",
)
REQUEST_TIMEOUT_SECONDS = 30
MAX_FETCH_ATTEMPTS = 3

def build_params(city: dict) -> dict:
    """Build Open-Meteo query parameters for one city."""
    return {
        "latitude": city["latitude"],
        "longitude": city["longitude"],
        "start_date": START_DATE,
        "end_date": END_DATE,
        "daily": ",".join(DAILY_VARIABLES),
        "timezone": city["timezone"],
    }


def build_output_path(city: dict) -> Path:
    """Return the raw file path, e.g. data/raw/weather/ICN_2020-01-01_2025-12-31.json."""
    filename = f"{city['city_id']}_{START_DATE}_{END_DATE}.json"
    return WEATHER_RAW_DIR / filename


def fetch_weather(city: dict) -> dict:
    """Fetch weather data for one city with retries for transient request failures."""
    last_error = None
    for attempt in range(1, MAX_FETCH_ATTEMPTS + 1):
        try:
            response = requests.get(
                OPEN_METEO_WEATHER_URL,
                params=build_params(city),
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as error:
            last_error = error
            if attempt < MAX_FETCH_ATTEMPTS:
                time.sleep(attempt)

    raise RuntimeError(
        f"Failed to fetch weather data for {city['city_name']}."
    ) from last_error


def main() -> None:
    """Fetch and persist daily weather data for every configured city."""
    try:
        cities = json.loads(CITIES_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise RuntimeError(f"Failed to load city data from {CITIES_PATH}.") from error

    WEATHER_RAW_DIR.mkdir(parents=True, exist_ok=True)
    for city in cities:
        weather = fetch_weather(city)

        output_path = build_output_path(city)
        output_path.write_text(
            json.dumps(weather, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Saved weather data for {city['city_name']} to {output_path}")


if __name__ == "__main__":
    main()
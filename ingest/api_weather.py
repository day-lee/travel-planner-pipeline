"""Fetch and save weather data"""

import json
from datetime import datetime
from pathlib import Path

import requests


CURRENT_YEAR = datetime.now().year
OPEN_METEO_WEATHER_URL = "https://archive-api.open-meteo.com/v1/archive"
START_DATE = "2020-01-01"
END_DATE = f"{CURRENT_YEAR - 1}-12-31"
WEATHER_RAW_DIR = Path("data/weather")

DAILY_VARIABLES = (
    "precipitation_sum",
    "apparent_temperature_max",
    "apparent_temperature_min",
    "wind_speed_10m_max",
    "wind_gusts_10m_max",
)

CITY = {
    "city_id": "ICN",
    "city_name": "Seoul",
    "country": "South Korea",
    "latitude": 37.5665,
    "longitude": 126.9780,
    "timezone": "Asia/Seoul",
}

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


def main() -> None:
    """Fetch and persist daily weather data for the configured city."""
    try:
        response = requests.get(
            OPEN_METEO_WEATHER_URL,
            params=build_params(CITY),
            timeout=30,
        )
        response.raise_for_status()
        weather = response.json()
    except requests.exceptions.RequestException as error:
        raise RuntimeError(
            f"Failed to fetch weather data for {CITY['city_name']}."
        ) from error

    output_path = build_output_path(CITY)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(weather, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Saved weather data for {CITY['city_name']} to {output_path}")


if __name__ == "__main__":
    main()
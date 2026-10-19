"""Export DuckDB mart data for the static dashboard."""

import json
from datetime import date
from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "travel_planner_warehouse.duckdb"
CITY_SEED_PATH = ROOT / "sql/0_seed/cities_weather_thresholds.json"
OUTPUT_PATH = ROOT / "dashboard/data/site_data.json"


def dates_for_week(year: int, week: int) -> list[str]:
    """Return dates in the selected calendar year for an ISO week."""
    week = min(week, 52)
    return [
        date.fromisocalendar(year, week, weekday).isoformat()
        for weekday in range(1, 8)
        if date.fromisocalendar(year, week, weekday).year == year
    ]


def load_cities() -> list[dict]:
    """Load city display metadata from the seed file."""
    return json.loads(CITY_SEED_PATH.read_text(encoding="utf-8"))


def main() -> None:
    """Export the data required by the dashboard."""
    cities = load_cities()
    city_ids = [city["city_id"] for city in cities]

    with duckdb.connect(str(DB_PATH), read_only=True) as connection:
        weather_rows = connection.execute(
            """
            SELECT city_id, week_of_year, good_day_share, is_good_weather
            FROM mart_weekly_weather_score
            ORDER BY city_id, week_of_year
            """
        ).fetchall()
        school_rows = connection.execute(
            """
            SELECT holiday_year, holiday_name, start_date, end_date
            FROM dim_uk_school_holidays_estimate
            ORDER BY holiday_year, start_date
            """
        ).fetchall()
        bank_rows = connection.execute(
            """
            SELECT holiday_date, holiday_name
            FROM stg_bank_holidays
            ORDER BY holiday_date
            """
        ).fetchall()

    weather = {}
    for city_id, week, share, is_good in weather_rows:
        weather.setdefault(city_id, {}).setdefault("scores", {})[str(week)] = {
            "good_day_share": share,
            "is_good_weather": is_good,
        }
        for year in {row[0] for row in school_rows}:
            if is_good:
                weather[city_id].setdefault("good_dates", {}).setdefault(
                    str(year), []
                ).extend(dates_for_week(year, week))

    data = {
        "cities": [
            {
                "city_id": city["city_id"],
                "city_name": city["city_name"],
            }
            for city in cities
        ],
        "city_ids": city_ids,
        "weather": weather,
        "school_holidays": [
            {
                "year": year,
                "name": name,
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
            }
            for year, name, start, end in school_rows
        ],
        "bank_holidays": [
            {"date": holiday_date.isoformat(), "name": name}
            for holiday_date, name in bank_rows
        ],
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"Built dashboard data at {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

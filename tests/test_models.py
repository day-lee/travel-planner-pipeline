"""Smoke tests for the warehouse tables.

Each query returns the rows that break a rule, so an empty result means the test passes.
"""

import json
from pathlib import Path

import duckdb
import pytest

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "travel_planner_warehouse.duckdb"
CITIES_SEED_PATH = ROOT / "sql" / "0_seed" / "cities_weather_thresholds.json"

WEEKS_PER_YEAR = 52
HOLIDAYS_PER_YEAR = 6


@pytest.fixture(scope="module")
def con():
    if not DB_PATH.exists():
        pytest.fail(f"{DB_PATH.name} not found. Run `python run_pipeline.py` first.")
    connection = duckdb.connect(str(DB_PATH), read_only=True)
    yield connection
    connection.close()


@pytest.fixture(scope="module")
def expected_city_ids() -> set:
    cities = json.loads(CITIES_SEED_PATH.read_text(encoding="utf-8"))
    return {city["city_id"] for city in cities}


def failing_rows(con, sql: str) -> list:
    return con.execute(sql).fetchall()


# --- Missing values ---------------------------------------------------------

def test_school_holidays_have_six_periods_per_year(con):
    total = con.execute("SELECT COUNT(*) FROM dim_uk_school_holidays_estimate").fetchone()[0]
    assert total > 0, "dim_uk_school_holidays_estimate is empty"

    rows = failing_rows(con, f"""
        SELECT holiday_year, COUNT(*) AS periods
        FROM dim_uk_school_holidays_estimate
        GROUP BY holiday_year
        HAVING COUNT(*) <> {HOLIDAYS_PER_YEAR}
    """)
    assert rows == [], f"Years without {HOLIDAYS_PER_YEAR} holiday periods: {rows}"


def test_school_holidays_have_start_and_end_dates(con):
    rows = failing_rows(con, """
        SELECT holiday_year, holiday_name, start_date, end_date
        FROM dim_uk_school_holidays_estimate
        WHERE start_date IS NULL
           OR end_date IS NULL
    """)
    assert rows == [], f"Holiday periods with a missing date: {rows}"


def test_mart_has_52_unique_weeks_per_city(con, expected_city_ids):
    mart_city_ids = {
        row[0]
        for row in con.execute("SELECT DISTINCT city_id FROM mart_weekly_weather_score").fetchall()
    }
    missing = expected_city_ids - mart_city_ids
    assert not missing, f"Cities in the seed but missing from the mart: {sorted(missing)}"

    rows = failing_rows(con, f"""
        SELECT
            city_id,
            COUNT(*)                     AS row_count,
            COUNT(DISTINCT week_of_year) AS distinct_weeks,
            MIN(week_of_year)            AS first_week,
            MAX(week_of_year)            AS last_week
        FROM mart_weekly_weather_score
        GROUP BY city_id
        HAVING row_count      <> {WEEKS_PER_YEAR}
            OR distinct_weeks <> {WEEKS_PER_YEAR}
            OR first_week     <> 1
            OR last_week      <> {WEEKS_PER_YEAR}
    """)
    assert rows == [], f"Cities without weeks 1–{WEEKS_PER_YEAR}: {rows}"


# --- Duplicate values -------------------------------------------------------

def test_stg_weather_has_one_row_per_city_per_day(con):
    rows = failing_rows(con, """
        SELECT city_id, weather_date, COUNT(*) AS n
        FROM stg_weather
        GROUP BY city_id, weather_date
        HAVING COUNT(*) > 1
        LIMIT 10
    """)
    assert rows == [], f"Duplicate city/day rows: {rows}"


# --- Implausible values -----------------------------------------------------

def test_good_day_share_is_between_0_and_1(con):
    rows = failing_rows(con, """
        SELECT city_id, week_of_year, good_day_share
        FROM mart_weekly_weather_score
        WHERE good_day_share IS NULL
           OR good_day_share < 0
           OR good_day_share > 1
        LIMIT 10
    """)
    assert rows == [], f"good_day_share is NULL or outside 0–1: {rows}"


def test_stg_weather_values_are_plausible(con):
    # NULLs are not checked here: a NULL comparison is never true, so those rows are skipped.
    rows = failing_rows(con, """
        SELECT city_id, weather_date
        FROM stg_weather
        WHERE apparent_temperature_max_c NOT BETWEEN -60 AND 60
           OR apparent_temperature_min_c NOT BETWEEN -60 AND 60
           OR precipitation_sum_mm       NOT BETWEEN 0 AND 500
           OR wind_speed_max_kmh         NOT BETWEEN 0 AND 250
           OR wind_gusts_max_kmh         NOT BETWEEN 0 AND 450
        LIMIT 10
    """)
    assert rows == [], f"Weather values outside plausible ranges: {rows}"
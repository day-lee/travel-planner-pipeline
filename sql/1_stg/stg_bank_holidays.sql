CREATE OR REPLACE TABLE stg_bank_holidays AS
WITH raw AS (
    SELECT
        "england-and-wales" AS england_and_wales,
        filename
    FROM read_json('data/uk_bank_holidays/*.json', filename = true)
),

-- Use most recent file, as indicated by the filename. e.g. 2026.json
latest AS (
    SELECT england_and_wales
    FROM raw
    WHERE filename = (SELECT MAX(filename) FROM raw)
),

events AS (
    SELECT UNNEST(england_and_wales.events) AS event
    FROM latest
)

SELECT
    CAST(event.date AS DATE)       AS holiday_date,
    YEAR(CAST(event.date AS DATE)) AS holiday_year,
    event.title                    AS holiday_name,
    event.notes = 'Substitute day' AS is_substitute_day
FROM events;
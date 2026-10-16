-- Daily weather per city from the saved Open-Meteo responses.
-- city_id comes from the file name (e.g. BKK_2021-01-01_2025-12-31.json).

CREATE OR REPLACE TABLE stg_weather AS
WITH raw AS (
    SELECT
        REGEXP_EXTRACT(filename, '([A-Z]{3})_[0-9]{4}-', 1) AS city_id,
        CAST(
            REGEXP_EXTRACT(filename, '_([0-9]{4}-[0-9]{2}-[0-9]{2})[.]json$', 1)
            AS DATE
        ) AS end_date,
        latitude,
        longitude,
        timezone,
        daily
    FROM read_json('data/weather/*.json', filename = true)
),

-- select the latest file per city_id
selected AS (
    SELECT *
    FROM raw
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY city_id
        ORDER BY end_date DESC
    ) = 1
),

unnested AS (
    SELECT
        city_id,
        latitude,
        longitude,
        timezone,
        UNNEST(daily.time)                     AS weather_date,
        UNNEST(daily.precipitation_sum)        AS precipitation_sum_mm,
        UNNEST(daily.apparent_temperature_max) AS apparent_temperature_max_c,
        UNNEST(daily.apparent_temperature_min) AS apparent_temperature_min_c,
        UNNEST(daily.wind_speed_10m_max)       AS wind_speed_max_kmh,
        UNNEST(daily.wind_gusts_10m_max)       AS wind_gusts_max_kmh
    FROM selected
)

SELECT
    city_id,
    CAST(latitude AS DOUBLE)                   AS latitude,
    CAST(longitude AS DOUBLE)                  AS longitude,
    timezone,
    CAST(weather_date AS DATE)                 AS weather_date,
    CAST(precipitation_sum_mm AS DOUBLE)       AS precipitation_sum_mm,
    CAST(apparent_temperature_max_c AS DOUBLE) AS apparent_temperature_max_c,
    CAST(apparent_temperature_min_c AS DOUBLE) AS apparent_temperature_min_c,
    CAST(wind_speed_max_kmh AS DOUBLE)         AS wind_speed_max_kmh,
    CAST(wind_gusts_max_kmh AS DOUBLE)         AS wind_gusts_max_kmh
FROM unnested;
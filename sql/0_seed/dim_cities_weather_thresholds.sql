CREATE OR REPLACE TABLE dim_weather_thresholds (
    city_id              VARCHAR PRIMARY KEY,
    city_name            VARCHAR NOT NULL,
    country              VARCHAR NOT NULL,
    latitude             DOUBLE  NOT NULL,
    longitude            DOUBLE  NOT NULL,
    timezone             VARCHAR NOT NULL,
    min_apparent_temp_c  DOUBLE  NOT NULL,
    max_apparent_temp_c  DOUBLE  NOT NULL,
    max_daily_rain_mm    DOUBLE  NOT NULL,
    max_wind_speed_kmh   DOUBLE  NOT NULL,
    max_wind_gust_kmh    DOUBLE  NOT NULL,
    CHECK (min_apparent_temp_c < max_apparent_temp_c),
    CHECK (max_wind_speed_kmh <= max_wind_gust_kmh)
);

INSERT INTO dim_weather_thresholds (
    city_id,
    city_name,
    country,
    latitude,
    longitude,
    timezone,
    min_apparent_temp_c,
    max_apparent_temp_c,
    max_daily_rain_mm,
    max_wind_speed_kmh,
    max_wind_gust_kmh
)
SELECT
    city_id,
    city_name,
    country,
    latitude,
    longitude,
    timezone,
    min_apparent_temp_c,
    max_apparent_temp_c,
    max_daily_rain_mm,
    max_wind_speed_kmh,
    max_wind_gust_kmh
FROM read_json('sql/0_seed/cities_weather_thresholds.json');
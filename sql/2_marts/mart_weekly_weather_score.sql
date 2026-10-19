CREATE OR REPLACE TABLE mart_weekly_weather_score AS
WITH daily AS (
    SELECT
        w.city_id,
        w.weather_date,
        ISOYEAR(w.weather_date)    AS iso_year,
        WEEKOFYEAR(w.weather_date) AS week_of_year,
        w.apparent_temperature_max_c <= t.max_apparent_temp_c
            AND w.apparent_temperature_min_c >= t.min_apparent_temp_c AS is_temp_comfortable,
        w.precipitation_sum_mm <= t.max_daily_rain_mm                 AS is_rain_low,
        w.wind_speed_max_kmh <= t.max_wind_speed_kmh
            AND w.wind_gusts_max_kmh <= t.max_wind_gust_kmh           AS is_wind_calm
    FROM stg_weather AS w
    JOIN dim_weather_thresholds AS t USING (city_id)
    WHERE WEEKOFYEAR(w.weather_date) <= 52   -- drop the rare week 53
),

daily_scored AS (
    SELECT
        *,
        is_temp_comfortable AND is_rain_low AND is_wind_calm AS is_good_day
    FROM daily
),

weekly_by_year AS (
    SELECT
        city_id,
        iso_year,
        week_of_year,
        COUNT(is_good_day)            AS days_with_data,   -- excludes days that can't be scored (NULL)
        COUNT_IF(is_good_day)         AS good_days,
        COUNT_IF(is_temp_comfortable) AS comfortable_temp_days,
        COUNT_IF(is_rain_low)         AS low_rain_days,
        COUNT_IF(is_wind_calm)        AS calm_wind_days
    FROM daily_scored
    GROUP BY city_id, iso_year, week_of_year
)

SELECT
    city_id,
    week_of_year, 
    COUNT(*)                                                    AS years_of_data,
    ROUND(SUM(good_days) / SUM(days_with_data), 2) AS good_day_share,
    -- Business rule: good week means at least 60% good days, i.e. about 4 of 7 days on average.
    SUM(good_days) / SUM(days_with_data) >= 0.6                 AS is_good_weather,
    ROUND(SUM(comfortable_temp_days) / SUM(days_with_data), 2)  AS comfortable_temp_share,
    ROUND(SUM(low_rain_days) / SUM(days_with_data), 2)          AS low_rain_share,
    ROUND(SUM(calm_wind_days) / SUM(days_with_data), 2)         AS calm_wind_share
FROM weekly_by_year
GROUP BY city_id, week_of_year;
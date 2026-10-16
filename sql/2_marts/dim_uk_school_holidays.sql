-- England school holidays (estimated).
-- There is no national dataset of school holidays. The rules are anchored on bank
-- holidays and kept wide on purpose: flagging an extra week costs the user less than
-- missing a holiday week. The estimates were spot-checked against a sample of council calendars.
--
-- Every holiday is a range of Monday–Sunday weeks that contain an anchor date.
-- Each period runs from Saturday to Sunday so that it covers the travel weekends.
--
-- 1. February half-term (1 week): the week containing 18 Feb.
--    Half-term starts on a Monday between 12 and 18 Feb, so that week always contains 18 Feb.
-- 2. Easter holidays (2–3 weeks): schools follow early April more closely than Easter itself,
--    so the period takes the earlier start and the later end of
--    (a) the two weeks starting on the first Monday of April (the week containing 7 Apr), and
--    (b) the Good Friday week to the Easter Monday week.
--    The start is no earlier than two weeks before the Easter Monday week (max 3 weeks).
-- 3. May half-term (1 week): the week containing the spring bank holiday.
-- 4. Summer holidays (~6 weeks): the week containing 22 Jul to the week containing 1 Sep.
--    Schools break up around 18–24 Jul and return around 1–5 Sep.
-- 5. October half-term (1 week): the week containing 28 Oct.
--    Half-term starts on a Monday between 22 and 28 Oct, so that week always contains 28 Oct.
-- 6. Christmas holidays (2 weeks): the week containing Christmas Day to the week containing 2 Jan.
--    2 Jan is used instead of 1 Jan because a Sunday 1 Jan falls in the Christmas week,
--    which would end the holiday a week early.
----------------------------------------------------------------
-- Monday of the week that contains d (weeks start on Monday).
CREATE OR REPLACE MACRO week_start(d) AS CAST(DATE_TRUNC('week', d) AS DATE);


-- Good Friday, Easter Monday and Spring bank holiday move every year,
-- so they come from the gov.uk data instead of fixed dates.
CREATE OR REPLACE TABLE dim_uk_school_holidays_estimate AS
WITH anchors AS (
    SELECT
        holiday_year,
        MAX(CASE WHEN holiday_name = 'Good Friday' THEN holiday_date END)         AS good_friday,
        MAX(CASE WHEN holiday_name = 'Easter Monday' THEN holiday_date END)       AS easter_monday,
        MAX(CASE WHEN holiday_name = 'Spring bank holiday' THEN holiday_date END) AS spring_bank_holiday
    FROM stg_bank_holidays
    WHERE holiday_year >= YEAR(CURRENT_DATE)
    GROUP BY holiday_year
),

-- From a Monday: -2 = the Saturday before, +6 = that week's Sunday.
estimates AS (
    SELECT
        holiday_year,
        '1.February half-term' AS holiday_name,
        week_start(MAKE_DATE(holiday_year, 2, 18)) - 2 AS start_date,
        week_start(MAKE_DATE(holiday_year, 2, 18)) + 6 AS end_date,
        'Week containing 18 Feb' AS rule
    FROM anchors

    UNION ALL
    SELECT
        holiday_year,
        '2.Easter holidays',
        GREATEST(
            LEAST(
                week_start(MAKE_DATE(holiday_year, 4, 7)),
                week_start(good_friday)
            ),
            week_start(easter_monday) - 14
        ) - 2,
        GREATEST(
            week_start(MAKE_DATE(holiday_year, 4, 7)) + 7,
            week_start(easter_monday)
        ) + 6,
        'Two weeks from the week containing 7 Apr, widened to the Good Friday and Easter Monday weeks, max 3 weeks'
    FROM anchors
    WHERE good_friday IS NOT NULL
      AND easter_monday IS NOT NULL

    UNION ALL
    SELECT
        holiday_year,
        '3.May half-term',
        week_start(spring_bank_holiday) - 2,
        week_start(spring_bank_holiday) + 6,
        'Week of the spring bank holiday'
    FROM anchors
    WHERE spring_bank_holiday IS NOT NULL

    UNION ALL
    SELECT
        holiday_year,
        '4.Summer holidays',
        week_start(MAKE_DATE(holiday_year, 7, 22)) - 2,
        week_start(MAKE_DATE(holiday_year, 9, 1)) + 6,
        'Week containing 22 Jul to week containing 1 Sep'
    FROM anchors

    UNION ALL
    SELECT
        holiday_year,
        '5.October half-term',
        week_start(MAKE_DATE(holiday_year, 10, 28)) - 2,
        week_start(MAKE_DATE(holiday_year, 10, 28)) + 6,
        'Week containing 28 Oct'
    FROM anchors

    UNION ALL
    SELECT
        holiday_year,
        '6.Christmas holidays',
        week_start(MAKE_DATE(holiday_year, 12, 25)) - 2,
        week_start(MAKE_DATE(holiday_year + 1, 1, 2)) + 6,
        'Week containing Christmas Day to week containing 2 Jan'
    FROM anchors
)

SELECT
    holiday_year,
    holiday_name,
    start_date,
    end_date,
    'England' AS region,
    rule
FROM estimates
ORDER BY start_date;
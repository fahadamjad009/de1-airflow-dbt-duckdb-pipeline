-- Mart: sector-level aggregated performance summary
WITH daily AS (
    SELECT * FROM {{ ref('mart_asx_daily_metrics') }}
),

latest AS (
    SELECT *
    FROM daily
    WHERE date = (SELECT MAX(date) FROM daily)
),

sector_agg AS (
    SELECT
        sector,
        COUNT(DISTINCT ticker)              AS ticker_count,
        ROUND(AVG(cum_return_pct), 2)       AS avg_cumulative_return_pct,
        ROUND(AVG(volatility_20d_rounded), 4) AS avg_volatility,
        ROUND(AVG(rel_volume), 2)           AS avg_relative_volume,
        ROUND(SUM(volume), 0)               AS total_volume,
        ROUND(AVG(close), 2)                AS avg_close_price,
        MIN(cum_return_pct)                 AS min_return,
        MAX(cum_return_pct)                 AS max_return
    FROM latest
    GROUP BY sector
)

SELECT
    sector,
    ticker_count,
    avg_cumulative_return_pct,
    avg_volatility,
    avg_relative_volume,
    total_volume,
    avg_close_price,
    min_return,
    max_return,
    CASE
        WHEN avg_cumulative_return_pct > 5  THEN 'Strong Buy'
        WHEN avg_cumulative_return_pct > 0  THEN 'Hold'
        WHEN avg_cumulative_return_pct > -5 THEN 'Weak'
        ELSE 'Underperform'
    END AS sector_signal
FROM sector_agg
ORDER BY avg_cumulative_return_pct DESC
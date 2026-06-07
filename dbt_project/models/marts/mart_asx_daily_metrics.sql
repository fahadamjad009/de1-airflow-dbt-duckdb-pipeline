-- Mart: daily metrics per ticker with moving averages and volatility
WITH base AS (
    SELECT * FROM {{ ref('stg_asx_prices') }}
),

with_metrics AS (
    SELECT
        date,
        ticker,
        company,
        sector,
        open,
        high,
        low,
        close,
        volume,
        daily_return,

        -- 5-day moving average
        AVG(close) OVER (
            PARTITION BY ticker
            ORDER BY date
            ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
        ) AS ma_5,

        -- 20-day moving average
        AVG(close) OVER (
            PARTITION BY ticker
            ORDER BY date
            ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
        ) AS ma_20,

        -- 20-day volatility (annualised)
        STDDEV(daily_return) OVER (
            PARTITION BY ticker
            ORDER BY date
            ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
        ) * SQRT(252) AS volatility_20d,

        -- Cumulative return from first date
        (close / FIRST_VALUE(close) OVER (
            PARTITION BY ticker ORDER BY date
        ) - 1) * 100 AS cumulative_return_pct,

        -- Daily price range
        ROUND(high - low, 3) AS daily_range,

        -- Volume vs 20-day avg volume
        volume / AVG(volume) OVER (
            PARTITION BY ticker
            ORDER BY date
            ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
        ) AS relative_volume

    FROM base
)

SELECT
    *,
    ROUND(ma_5, 3)                AS ma_5_rounded,
    ROUND(ma_20, 3)               AS ma_20_rounded,
    ROUND(volatility_20d, 4)      AS volatility_20d_rounded,
    ROUND(cumulative_return_pct, 2) AS cum_return_pct,
    ROUND(relative_volume, 2)     AS rel_volume
FROM with_metrics
ORDER BY ticker, date
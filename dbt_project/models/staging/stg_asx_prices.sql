-- Staging model: clean and type-cast raw ASX price data
SELECT
    CAST(date AS DATE)          AS date,
    ticker,
    company,
    sector,
    ROUND(CAST(open  AS DOUBLE), 3) AS open,
    ROUND(CAST(high  AS DOUBLE), 3) AS high,
    ROUND(CAST(low   AS DOUBLE), 3) AS low,
    ROUND(CAST(close AS DOUBLE), 3) AS close,
    CAST(volume AS BIGINT)      AS volume,
    ROUND(CAST(daily_return AS DOUBLE), 4) AS daily_return
FROM {{ source('raw', 'raw_asx_prices') }}
WHERE close > 0
  AND volume > 0
-- Staging model: clean macro indicator data
SELECT
    indicator,
    ROUND(CAST(value AS DOUBLE), 4) AS value,
    unit,
    CAST(date AS DATE) AS date,
    source
FROM {{ source('raw', 'raw_macro_indicators') }}
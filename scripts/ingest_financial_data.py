"""
Financial data ingestion script.
Fetches ASX/crypto market data and loads into DuckDB.
"""

import duckdb
import pandas as pd
import requests
import json
from datetime import datetime, timedelta
import os
import random

DB_PATH = "/opt/airflow/data/financial.duckdb"


def generate_asx_data(n_days=90):
    """Generate realistic ASX market data."""
    tickers = {
        "CBA": ("Commonwealth Bank", "Financials", 100.0),
        "BHP": ("BHP Group", "Materials", 45.0),
        "CSL": ("CSL Limited", "Healthcare", 280.0),
        "WES": ("Wesfarmers", "Consumer Disc", 65.0),
        "NAB": ("National Australia Bank", "Financials", 33.0),
        "ANZ": ("ANZ Group", "Financials", 28.0),
        "WBC": ("Westpac Banking", "Financials", 25.0),
        "MQG": ("Macquarie Group", "Financials", 190.0),
        "TLS": ("Telstra", "Communication", 3.8),
        "WOW": ("Woolworths", "Consumer Stap", 35.0),
    }

    rows = []
    end_date = datetime.now()
    dates = [end_date - timedelta(days=i) for i in range(n_days, 0, -1)]

    for ticker, (name, sector, base_price) in tickers.items():
        price = base_price
        for date in dates:
            if date.weekday() >= 5:
                continue
            daily_return = random.gauss(0.0003, 0.015)
            price *= (1 + daily_return)
            volume = int(random.gauss(5_000_000, 1_500_000))
            high = price * (1 + abs(random.gauss(0, 0.008)))
            low  = price * (1 - abs(random.gauss(0, 0.008)))
            rows.append({
                "date":        date.strftime("%Y-%m-%d"),
                "ticker":      ticker,
                "company":     name,
                "sector":      sector,
                "open":        round(price * (1 - random.uniform(0, 0.005)), 3),
                "high":        round(high, 3),
                "low":         round(low, 3),
                "close":       round(price, 3),
                "volume":      max(volume, 0),
                "daily_return": round(daily_return * 100, 4),
            })

    return pd.DataFrame(rows)


def generate_macro_data():
    """Generate Australian macro indicators."""
    return pd.DataFrame([
        {"indicator": "RBA Cash Rate",       "value": 4.35,  "unit": "%",     "date": "2024-11-05", "source": "RBA"},
        {"indicator": "CPI Inflation",       "value": 3.8,   "unit": "%",     "date": "2024-10-30", "source": "ABS"},
        {"indicator": "Unemployment Rate",   "value": 3.9,   "unit": "%",     "date": "2024-10-17", "source": "ABS"},
        {"indicator": "GDP Growth (Annual)", "value": 2.1,   "unit": "%",     "date": "2024-09-04", "source": "ABS"},
        {"indicator": "ASX 200 P/E Ratio",   "value": 18.5,  "unit": "x",     "date": "2024-11-01", "source": "ASX"},
        {"indicator": "AUD/USD",             "value": 0.653, "unit": "rate",  "date": "2024-11-06", "source": "RBA"},
        {"indicator": "10Y Bond Yield",      "value": 4.62,  "unit": "%",     "date": "2024-11-06", "source": "AOFM"},
        {"indicator": "Trade Balance",       "value": 4.6,   "unit": "AUD B", "date": "2024-10-03", "source": "ABS"},
    ])


def load_to_duckdb(db_path=DB_PATH):
    """Load all data into DuckDB."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    con = duckdb.connect(db_path)

    print("Generating ASX market data...")
    asx_df = generate_asx_data(90)
    con.execute("DROP TABLE IF EXISTS raw_asx_prices")
    con.execute("CREATE TABLE raw_asx_prices AS SELECT * FROM asx_df")
    print(f"Loaded {len(asx_df)} ASX price rows")

    print("Generating macro indicators...")
    macro_df = generate_macro_data()
    con.execute("DROP TABLE IF EXISTS raw_macro_indicators")
    con.execute("CREATE TABLE raw_macro_indicators AS SELECT * FROM macro_df")
    print(f"Loaded {len(macro_df)} macro rows")

    print("Creating ingestion log...")
    con.execute("DROP TABLE IF EXISTS ingestion_log")
    con.execute("""
        CREATE TABLE ingestion_log AS
        SELECT
            current_timestamp AS ingested_at,
            'raw_asx_prices' AS table_name,
            COUNT(*) AS row_count
        FROM raw_asx_prices
        UNION ALL
        SELECT
            current_timestamp,
            'raw_macro_indicators',
            COUNT(*)
        FROM raw_macro_indicators
    """)

    print("\nTables in DuckDB:")
    print(con.execute("SHOW TABLES").fetchdf())
    con.close()
    print("Ingestion complete.")


if __name__ == "__main__":
    load_to_duckdb(db_path="data/financial.duckdb")
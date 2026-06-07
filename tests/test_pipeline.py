"""
Unit tests for DE1 ASX Financial Data Pipeline.
Run: python -m pytest tests/ -v
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import pytest
import pandas as pd
import duckdb
from ingest_financial_data import generate_asx_data, generate_macro_data


def test_asx_data_row_count():
    df = generate_asx_data(n_days=30)
    assert len(df) > 0


def test_asx_data_columns():
    df = generate_asx_data(n_days=10)
    expected = ["date","ticker","company","sector","open","high","low","close","volume","daily_return"]
    for col in expected:
        assert col in df.columns


def test_asx_data_tickers():
    df = generate_asx_data(n_days=10)
    assert df["ticker"].nunique() == 10


def test_asx_close_positive():
    df = generate_asx_data(n_days=10)
    assert (df["close"] > 0).all()


def test_asx_volume_positive():
    df = generate_asx_data(n_days=10)
    assert (df["volume"] >= 0).all()


def test_macro_data_rows():
    df = generate_macro_data()
    assert len(df) == 8


def test_macro_data_columns():
    df = generate_macro_data()
    assert "indicator" in df.columns
    assert "value" in df.columns


def test_duckdb_load():
    df = generate_asx_data(n_days=10)
    con = duckdb.connect(":memory:")
    con.execute("CREATE TABLE test AS SELECT * FROM df")
    count = con.execute("SELECT COUNT(*) FROM test").fetchone()[0]
    assert count == len(df)
    con.close()


def test_high_gte_low():
    df = generate_asx_data(n_days=20)
    assert (df["high"] >= df["low"]).all()


def test_sector_coverage():
    df = generate_asx_data(n_days=5)
    assert df["sector"].nunique() >= 4
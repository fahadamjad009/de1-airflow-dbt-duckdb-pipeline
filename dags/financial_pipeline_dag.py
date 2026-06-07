"""
DE1 — Financial Data Pipeline DAG
Orchestrates: data ingestion → dbt transformations → validation
Schedule: daily at 6am AEST
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    "owner": "fahad",
    "depends_on_past": False,
    "start_date": datetime(2026, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 0,
}


def ingest_financial_data(**context):
    import sys
    sys.path.insert(0, "/opt/airflow/scripts")
    from ingest_financial_data import load_to_duckdb
    load_to_duckdb(db_path="/opt/airflow/data/financial.duckdb")
    print("Ingestion complete.")


def validate_data(**context):
    import duckdb
    con = duckdb.connect("/opt/airflow/data/financial.duckdb")
    checks = []

    raw_count = con.execute("SELECT COUNT(*) FROM raw_asx_prices").fetchone()[0]
    checks.append(("raw_asx_prices row count > 0", raw_count > 0, raw_count))

    null_close = con.execute(
        "SELECT COUNT(*) FROM main.mart_asx_daily_metrics WHERE close IS NULL"
    ).fetchone()[0]
    checks.append(("no null close prices", null_close == 0, null_close))

    sector_count = con.execute(
        "SELECT COUNT(*) FROM main.mart_sector_summary"
    ).fetchone()[0]
    checks.append(("sector summary has rows", sector_count > 0, sector_count))

    ticker_count = con.execute(
        "SELECT COUNT(DISTINCT ticker) FROM main.mart_asx_daily_metrics"
    ).fetchone()[0]
    checks.append(("all 10 tickers present", ticker_count == 10, ticker_count))

    con.close()

    print("\n--- Data Quality Checks ---")
    all_passed = True
    for name, passed, value in checks:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name} (value={value})")
        if not passed:
            all_passed = False

    if not all_passed:
        raise ValueError("Data quality checks failed.")
    print("\nAll checks passed.")


with DAG(
    dag_id="financial_pipeline",
    default_args=default_args,
    description="ASX financial data pipeline: ingest → dbt → validate",
    schedule="0 6 * * *",
    catchup=False,
    tags=["finance", "dbt", "duckdb", "asx"],
) as dag:

    task_ingest = PythonOperator(
        task_id="ingest_financial_data",
        python_callable=ingest_financial_data,
    )

    task_dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command="/home/airflow/.local/bin/dbt run --profiles-dir /opt/airflow/dbt_project --project-dir /opt/airflow/dbt_project",
    )

    task_validate = PythonOperator(
        task_id="validate_data",
        python_callable=validate_data,
    )

    task_ingest >> task_dbt_run >> task_validate
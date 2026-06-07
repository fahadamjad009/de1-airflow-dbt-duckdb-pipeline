# 🔧 DE1 — ASX Financial Data Pipeline

> End-to-end financial data engineering pipeline — **Apache Airflow** orchestration, **dbt** transformations, **DuckDB** analytics, and an interactive **Streamlit** dashboard with candlestick charts, sector rotation, Sharpe ratio, drawdown analysis, and macro overlays.

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)
![Airflow](https://img.shields.io/badge/Apache_Airflow-2.9.1-017CEE?style=flat&logo=apacheairflow&logoColor=white)
![dbt](https://img.shields.io/badge/dbt-1.8.7-FF694B?style=flat&logo=dbt&logoColor=white)
![DuckDB](https://img.shields.io/badge/DuckDB-1.5.3-FFF000?style=flat&logo=duckdb&logoColor=black)
![Docker](https://img.shields.io/badge/Docker-29.4.0-2496ED?style=flat&logo=docker&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.58-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-Interactive-3F4F75?style=flat&logo=plotly&logoColor=white)
![Tests](https://img.shields.io/badge/tests-10%20passed-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Why this project

Most data engineering portfolios show pipelines that load CSV files into Postgres. This project builds a production-pattern financial pipeline — Airflow DAG orchestrating Python ingestion, dbt transformations with window functions and sector signals, DuckDB analytics engine, and a 5-tab Streamlit dashboard with 20+ interactive visualisations. Runs fully in Docker on any machine.

**Target use case:** Financial analytics platforms, FinTech data teams, trading desks, RegTech reporting pipelines.

---

## Pipeline Architecture
Raw Data Generation
↓
ingest_financial_data (PythonOperator)
→ 650 rows ASX OHLCV · 10 tickers · 90 days
→ 8 Australian macro indicators
→ Loaded into DuckDB raw tables
↓
dbt_run (BashOperator)
→ stg_asx_prices (view) — clean and typed OHLCV
→ stg_macro_indicators (view) — clean macro data
→ mart_asx_daily_metrics (table) — MA5, MA20, volatility, cumulative return, relative volume
→ mart_sector_summary (table) — sector aggregates and buy/sell signals
↓
validate_data (PythonOperator)
→ 4 data quality checks
→ Row counts · Null prices · Ticker completeness · Sector coverage

---

## Live Dashboard

### [▶ View Live App on Streamlit Cloud](https://de1-airflow-dbt-duckdb-pipeline.streamlit.app)

> **Note:** The live Streamlit demo auto-generates sample data via a self-bootstrapping DuckDB pipeline — no Docker or dbt required for the demo. Locally, the full Airflow + dbt + Docker stack runs the real pipeline. See `_bootstrap_db()` in `app.py` for the cloud-compatible implementation.

Five-tab interactive Streamlit dashboard:

| Tab | Visualisations |
|---|---|
| **📈 Price & Technical** | Candlestick OHLCV + MA crossover signals + volume · Cumulative return · Daily return histogram · Volatility · Relative volume · Cross-ticker correlation heatmap |
| **🏭 Sector Analysis** | Sector return bar · Sector to ticker treemap · Sector rotation line chart · Risk vs return scatter · Multi-metric radar · Waterfall returns · Signal table |
| **🔬 Deep Analytics** | Rolling Sharpe ratio · Drawdown chart · Sharpe comparison bar · Max drawdown bar · Multi-ticker comparison · Analytics summary table |
| **🌍 Macro & Context** | 4 gauge indicators (RBA, CPI, Unemployment, GDP) · Macro bar + pie · ASX return vs RBA rate overlay |
| **🔧 Pipeline Architecture** | Pipeline description · dbt model lineage table · Simulated DAG run history stacked bar · Tech stack |

---

## All components

| Component | File | What it does |
|---|---|---|
| Data ingestion | `scripts/ingest_financial_data.py` | Generates 650 ASX OHLCV rows + 8 macro indicators, loads into DuckDB |
| Airflow DAG | `dags/financial_pipeline_dag.py` | 3-task DAG: ingest → dbt → validate, scheduled 6am daily |
| dbt staging | `dbt_project/models/staging/` | 2 views: clean and type-cast raw data |
| dbt marts | `dbt_project/models/marts/` | 2 tables: MA, volatility, cumulative return, sector signals |
| Dashboard | `app.py` | 5-tab Streamlit dashboard with 20+ Plotly charts |
| Docker | `docker-compose.yml` and `Dockerfile` | Airflow 2.9.1 + dbt + DuckDB containerised |

---

## Data Engineering skills demonstrated

| Skill | Where | Interview talking point |
|---|---|---|
| **Airflow DAG authoring** | `financial_pipeline_dag.py` | "PythonOperator + BashOperator with task dependency chain using >> operator" |
| **dbt window functions** | `mart_asx_daily_metrics.sql` | "MA5/MA20 using ROWS BETWEEN — same pattern as SQL Server analytics functions" |
| **dbt materialisation** | `dbt_project.yml` | "Staging as views (cheap to recompute), marts as tables (fast to query)" |
| **DuckDB analytics** | All mart queries | "DuckDB processes 650 rows in 0.09s — columnar engine optimised for analytics" |
| **Docker orchestration** | `docker-compose.yml` | "Multi-service compose: Postgres metadata DB + Airflow webserver + scheduler" |
| **Data quality checks** | `validate_data` task | "4 assertions on row count, nulls, cardinality — lightweight Great Expectations pattern" |
| **Sector signal logic** | `mart_sector_summary.sql` | "CASE expression generating buy/hold/sell signals from cumulative return thresholds" |
| **Custom Docker image** | `Dockerfile` | "Extends apache/airflow:2.9.1 with dbt-duckdb — standard production approach" |

---

## dbt Model Lineage

| Model | Type | Layer | Rows | Key columns |
|---|---|---|---|---|
| `raw_asx_prices` | Source | Raw | 650 | date, ticker, open, high, low, close, volume |
| `raw_macro_indicators` | Source | Raw | 8 | indicator, value, unit, date, source |
| `stg_asx_prices` | View | Staging | 650 | Cleaned and typed OHLCV |
| `stg_macro_indicators` | View | Staging | 8 | Cleaned macro data |
| `mart_asx_daily_metrics` | Table | Mart | 650 | MA5, MA20, volatility_20d, cum_return_pct, rel_volume |
| `mart_sector_summary` | Table | Mart | 6 | avg_return, avg_volatility, sector_signal |

---

## ASX Tickers

| Sector | Tickers |
|---|---|
| Financials | CBA, WBC, NAB, ANZ, MQG |
| Materials | BHP |
| Healthcare | CSL |
| Consumer Disc | WES |
| Consumer Stap | WOW |
| Communication | TLS |

---

## Local setup

```bash
git clone https://github.com/fahadamjad009/de1-airflow-dbt-duckdb-pipeline.git
cd de1-airflow-dbt-duckdb-pipeline
```

**Start Airflow with Docker:**

```bash
docker compose up airflow-init
docker compose up -d
```

Open http://localhost:8081 — login admin/admin — trigger financial_pipeline DAG.

**Run tests:**

```bash
python -m pytest tests/ -v
```

**Run Streamlit dashboard:**

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python scripts/ingest_financial_data.py
cd dbt_project && dbt run && cd ..
streamlit run app.py
```

---

## Tech stack

Apache Airflow · dbt-core · DuckDB · Docker · Streamlit · Plotly · pandas · Python

---

---

## License

MIT — see `LICENSE`
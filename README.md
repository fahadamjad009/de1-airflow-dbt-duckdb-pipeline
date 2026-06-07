\# 🔧 DE1 — ASX Financial Data Pipeline



> End-to-end financial data engineering pipeline — \*\*Apache Airflow\*\* orchestration, \*\*dbt\*\* transformations, \*\*DuckDB\*\* analytics, and an interactive \*\*Streamlit\*\* dashboard with candlestick charts, sector rotation, Sharpe ratio, drawdown analysis, and macro overlays.



!\[Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat\&logo=python\&logoColor=white)

!\[Airflow](https://img.shields.io/badge/Apache\_Airflow-2.9.1-017CEE?style=flat\&logo=apacheairflow\&logoColor=white)

!\[dbt](https://img.shields.io/badge/dbt-1.8.7-FF694B?style=flat\&logo=dbt\&logoColor=white)

!\[DuckDB](https://img.shields.io/badge/DuckDB-1.5.3-FFF000?style=flat\&logo=duckdb\&logoColor=black)

!\[Docker](https://img.shields.io/badge/Docker-29.4.0-2496ED?style=flat\&logo=docker\&logoColor=white)

!\[Streamlit](https://img.shields.io/badge/Streamlit-1.58-FF4B4B?style=flat\&logo=streamlit\&logoColor=white)

!\[Plotly](https://img.shields.io/badge/Plotly-Interactive-3F4F75?style=flat\&logo=plotly\&logoColor=white)

!\[License](https://img.shields.io/badge/license-MIT-green)



\---



\## Why this project



Most data engineering portfolios show pipelines that load CSV files into Postgres. This project builds a production-pattern financial pipeline — Airflow DAG orchestrating Python ingestion, dbt transformations with window functions and sector signals, DuckDB analytics engine, and a 5-tab Streamlit dashboard with 20+ interactive visualisations. Runs fully in Docker on any machine.



\*\*Target use case:\*\* Financial analytics platforms, FinTech data teams, trading desks, RegTech reporting pipelines.



\---



\## Pipeline Architecture

Raw Data Generation

↓

ingest\_financial\_data (PythonOperator)

→ 650 rows ASX OHLCV · 10 tickers · 90 days

→ 8 Australian macro indicators

→ Loaded into DuckDB raw tables

↓

dbt\_run (BashOperator)

→ stg\_asx\_prices      (view)   — clean + typed OHLCV

→ stg\_macro\_indicators (view)  — clean macro data

→ mart\_asx\_daily\_metrics (table) — MA5, MA20, volatility, cumulative return, relative volume

→ mart\_sector\_summary (table)  — sector aggregates + buy/sell signals

↓

validate\_data (PythonOperator)

→ 4 data quality checks

→ Row counts · Null prices · Ticker completeness · Sector coverage



\---



\## Live Dashboard



Five-tab interactive Streamlit dashboard:



| Tab | Visualisations |

|---|---|

| \*\*📈 Price \& Technical\*\* | Candlestick OHLCV + MA crossover signals + volume · Cumulative return · Daily return histogram · Volatility · Relative volume · Cross-ticker correlation heatmap |

| \*\*🏭 Sector Analysis\*\* | Sector return bar · Sector → ticker treemap · Sector rotation line chart · Risk vs return scatter · Multi-metric radar · Waterfall returns · Signal table |

| \*\*🔬 Deep Analytics\*\* | Rolling Sharpe ratio · Drawdown chart · Sharpe comparison bar · Max drawdown bar · Multi-ticker comparison · Analytics summary table |

| \*\*🌍 Macro \& Context\*\* | 4 gauge indicators (RBA, CPI, Unemployment, GDP) · Macro bar + pie · ASX return vs RBA rate overlay |

| \*\*🔧 Pipeline Architecture\*\* | Pipeline description · dbt model lineage table · Simulated DAG run history stacked bar · Tech stack |



\---



\## All components



| Component | File | What it does |

|---|---|---|

| Data ingestion | `scripts/ingest\_financial\_data.py` | Generates 650 ASX OHLCV rows + 8 macro indicators, loads into DuckDB |

| Airflow DAG | `dags/financial\_pipeline\_dag.py` | 3-task DAG: ingest → dbt → validate, scheduled 6am daily |

| dbt staging | `dbt\_project/models/staging/` | 2 views: clean + type-cast raw data |

| dbt marts | `dbt\_project/models/marts/` | 2 tables: MA, volatility, cumulative return, sector signals |

| Dashboard | `app.py` | 5-tab Streamlit dashboard — 20+ Plotly charts |

| Docker | `docker-compose.yml` + `Dockerfile` | Airflow 2.9.1 + dbt + DuckDB containerised |



\---



\## Data Engineering skills demonstrated



| Skill | Where | Interview talking point |

|---|---|---|

| \*\*Airflow DAG authoring\*\* | `financial\_pipeline\_dag.py` | "PythonOperator + BashOperator with task dependency chain using >> operator" |

| \*\*dbt window functions\*\* | `mart\_asx\_daily\_metrics.sql` | "MA5/MA20 using ROWS BETWEEN — same pattern as SQL Server analytics functions" |

| \*\*dbt materialisation\*\* | `dbt\_project.yml` | "Staging as views (cheap to recompute), marts as tables (fast to query)" |

| \*\*DuckDB analytics\*\* | All mart queries | "DuckDB processes 650 rows in 0.09s — columnar engine optimised for analytics" |

| \*\*Docker orchestration\*\* | `docker-compose.yml` | "Multi-service compose: Postgres metadata DB + Airflow webserver + scheduler" |

| \*\*Data quality checks\*\* | `validate\_data` task | "4 assertions on row count, nulls, cardinality — lightweight Great Expectations pattern" |

| \*\*Sector signal logic\*\* | `mart\_sector\_summary.sql` | "CASE expression generating buy/hold/sell signals from cumulative return thresholds" |

| \*\*Custom Docker image\*\* | `Dockerfile` | "Extends apache/airflow:2.9.1 with dbt-duckdb — standard production approach" |



\---



\## dbt Model Lineage

raw\_asx\_prices          raw\_macro\_indicators

↓                         ↓

stg\_asx\_prices      stg\_macro\_indicators

↓

mart\_asx\_daily\_metrics

↓

mart\_sector\_summary



| Model | Type | Key columns |

|---|---|---|

| `stg\_asx\_prices` | View | date, ticker, open, high, low, close, volume, daily\_return |

| `stg\_macro\_indicators` | View | indicator, value, unit, date, source |

| `mart\_asx\_daily\_metrics` | Table | MA5, MA20, volatility\_20d, cum\_return\_pct, rel\_volume |

| `mart\_sector\_summary` | Table | avg\_return, avg\_volatility, sector\_signal |



\---



\## ASX Tickers



| Sector | Tickers |

|---|---|

| Financials | CBA, WBC, NAB, ANZ, MQG |

| Materials | BHP |

| Healthcare | CSL |

| Consumer Disc | WES |

| Consumer Stap | WOW |

| Communication | TLS |



\---



\## Local setup



```bash

git clone https://github.com/fahadamjad009/de1-airflow-dbt-duckdb-pipeline.git

cd de1-airflow-dbt-duckdb-pipeline

```



\*\*Start Airflow with Docker:\*\*

```bash

docker compose up airflow-init

docker compose up -d

```



Open \*\*http://localhost:8081\*\* → login admin/admin → trigger `financial\_pipeline` DAG.



\*\*Run Streamlit dashboard:\*\*

```bash

python -m venv venv

venv\\Scripts\\activate

pip install -r requirements.txt

python scripts/ingest\_financial\_data.py

cd dbt\_project \&\& dbt run \&\& cd ..

streamlit run app.py

```



\---



\## Tech stack



Apache Airflow · dbt-core · DuckDB · Docker · Streamlit · Plotly · pandas · Python



\---



\---



\## License



MIT — see `LICENSE`


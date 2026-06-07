FROM apache/airflow:2.9.1
USER root
RUN apt-get update && apt-get install -y gcc && apt-get clean
USER airflow
RUN pip install --no-cache-dir "dbt-core==1.8.7" "dbt-duckdb==1.8.4" "duckdb==1.5.3"
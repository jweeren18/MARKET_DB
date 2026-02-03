"""
Market Pipeline DAG (Kubernetes)

Single DAG that runs the full daily pipeline in sequence:
    1. ingest_market_data      — fetch latest prices via Schwab
    2. calculate_indicators    — compute technical indicators
    3. score_opportunities     — calculate 10x opportunity scores
    4. generate_alerts         — create alerts from score changes

Schedule: Mon-Fri at 4:15 PM ET (after market close)

NOTE: When this DAG is active, the individual K8s DAGs should be paused:
    - data_ingestion_dag
    - calculate_indicators_dag
    - score_opportunities_dag
    - generate_alerts_dag
"""

from datetime import timedelta

from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from airflow.utils.dates import days_ago
from kubernetes.client import models as k8s


# ---------------------------------------------------------------------------
# DAG definition
# ---------------------------------------------------------------------------

default_args = {
    "owner": "market-intelligence",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    "market_pipeline",
    default_args=default_args,
    description="Full daily market pipeline: ingest → indicators → scoring → alerts",
    schedule_interval="15 16 * * 1-5",  # 4:15 PM ET Mon-Fri
    start_date=days_ago(1),
    catchup=False,
    tags=["pipeline", "market-data", "daily"],
)


# ---------------------------------------------------------------------------
# Shared config
# ---------------------------------------------------------------------------

env_vars = {
    "DATABASE_URL": "{{ var.value.database_url }}",
    "SCHWAB_API_KEY": "{{ var.value.schwab_api_key }}",
    "SCHWAB_API_SECRET": "{{ var.value.schwab_api_secret }}",
    "SCHWAB_CALLBACK_URL": "{{ var.value.schwab_callback_url }}",
    "PYTHONUNBUFFERED": "1",
}

# Resource presets — indicators needs the most headroom (252-day lookback × 30 tickers)
SMALL = k8s.V1ResourceRequirements(
    requests={"memory": "256Mi", "cpu": "250m"},
    limits={"memory": "512Mi", "cpu": "500m"},
)
MEDIUM = k8s.V1ResourceRequirements(
    requests={"memory": "512Mi", "cpu": "500m"},
    limits={"memory": "1Gi", "cpu": "1000m"},
)
LARGE = k8s.V1ResourceRequirements(
    requests={"memory": "1Gi", "cpu": "500m"},
    limits={"memory": "2Gi", "cpu": "1000m"},
)

# Common pod kwargs
POD_DEFAULTS = dict(
    namespace="default",
    image="market-intelligence-jobs:latest",
    cmds=["python"],
    env_vars=env_vars,
    get_logs=True,
    is_delete_operator_pod=True,
    in_cluster=False,                       # set True when Airflow itself runs in K8s
    config_file="/path/to/kubeconfig",      # remove when in_cluster=True
    dag=dag,
)


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

ingest_task = KubernetesPodOperator(
    task_id="ingest_market_data",
    name="pipeline-ingest-pod",
    arguments=["jobs/data_ingestion.py", "--all", "--days", "1"],
    container_resources=MEDIUM,
    **POD_DEFAULTS,
)

indicators_task = KubernetesPodOperator(
    task_id="calculate_indicators",
    name="pipeline-indicators-pod",
    arguments=["jobs/calculate_indicators.py", "--all"],
    container_resources=LARGE,
    **POD_DEFAULTS,
)

scoring_task = KubernetesPodOperator(
    task_id="score_opportunities",
    name="pipeline-scoring-pod",
    arguments=["jobs/score_opportunities.py", "--all"],
    container_resources=MEDIUM,
    **POD_DEFAULTS,
)

alerts_task = KubernetesPodOperator(
    task_id="generate_alerts",
    name="pipeline-alerts-pod",
    arguments=["jobs/generate_alerts.py"],
    container_resources=SMALL,
    **POD_DEFAULTS,
)


# ---------------------------------------------------------------------------
# Dependency chain
# ---------------------------------------------------------------------------

ingest_task >> indicators_task >> scoring_task >> alerts_task

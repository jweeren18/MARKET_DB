"""
Calculate Indicators DAG

Calculates technical indicators for all tickers.
Runs at 4:30 PM EST Mon-Fri (after data ingestion).
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from airflow.sensors.external_task import ExternalTaskSensor
from kubernetes.client import models as k8s

# Default arguments
default_args = {
    'owner': 'market-intelligence',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# DAG definition
dag = DAG(
    'calculate_indicators',
    default_args=default_args,
    description='Calculate technical indicators for all tickers',
    schedule='30 16 * * 1-5',  # 4:30 PM Mon-Fri
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['market-data', 'indicators'],
)

# Environment variables
env_vars = {
    'DATABASE_URL': '{{ var.value.database_url }}',
    'PYTHONUNBUFFERED': '1',
}

with dag:

    # Wait for data ingestion to complete
    wait_for_ingestion = ExternalTaskSensor(
        task_id='wait_for_data_ingestion',
        external_dag_id='data_ingestion',
        external_task_id='ingest_market_data',
        allowed_states=['success'],
        failed_states=['failed', 'skipped'],
        mode='reschedule',
        timeout=3600,  # 1 hour timeout
        poke_interval=60,  # Check every minute
    )

    # Calculate indicators task
    calculate_indicators_task = KubernetesPodOperator(
        task_id='calculate_technical_indicators',
        name='calculate-indicators-pod',
        namespace='default',
        image='market-intelligence-jobs:latest',
        cmds=['python'],
        arguments=['jobs/calculate_indicators.py', '--all'],
        env_vars=env_vars,
        get_logs=True,
        is_delete_operator_pod=True,
        in_cluster=False,
        config_file='/path/to/kubeconfig',
        container_resources=k8s.V1ResourceRequirements(
            requests={'memory': '1Gi', 'cpu': '500m'},
            limits={'memory': '2Gi', 'cpu': '1000m'}
        ),
    )

    # Task dependencies
    wait_for_ingestion >> calculate_indicators_task

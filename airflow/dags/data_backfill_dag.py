"""
Historical Data Backfill DAG

One-time or on-demand backfill of historical market data.
This DAG is manually triggered and not scheduled automatically.

Usage:
    - Trigger manually from Airflow UI
    - Configure backfill period using DAG run configuration:
      {
        "days": 365,
        "tickers": "AAPL,MSFT,NVDA"  # Optional, defaults to all active tickers
      }
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from airflow.utils.dates import days_ago
from kubernetes.client import models as k8s

# Default arguments
default_args = {
    'owner': 'market-intelligence',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=10),
}

# DAG definition
dag = DAG(
    'data_backfill_historical',
    default_args=default_args,
    description='Historical market data backfill (manual trigger)',
    schedule_interval=None,  # Manual trigger only
    start_date=days_ago(1),
    catchup=False,
    tags=['market-data', 'backfill', 'historical'],
)

# Environment variables for the pod
env_vars = {
    'DATABASE_URL': '{{ var.value.database_url }}',
    'SCHWAB_API_KEY': '{{ var.value.schwab_api_key }}',
    'SCHWAB_API_SECRET': '{{ var.value.schwab_api_secret }}',
    'SCHWAB_CALLBACK_URL': '{{ var.value.schwab_callback_url }}',
    'PYTHONUNBUFFERED': '1',
}

# Volume mount for shared configuration (optional)
volume_mount = k8s.V1VolumeMount(
    name='config-volume',
    mount_path='/app/config',
    read_only=True
)

volume = k8s.V1Volume(
    name='config-volume',
    config_map=k8s.V1ConfigMapVolumeSource(
        name='market-intelligence-config'
    )
)

# Kubernetes Pod Operator - Historical Backfill
# Fetches historical data based on DAG run configuration
backfill_task = KubernetesPodOperator(
    task_id='backfill_historical_data',
    name='data-backfill-historical-pod',
    namespace='default',  # Change to your namespace
    image='market-intelligence-jobs:latest',  # Your Docker image
    cmds=['python'],
    arguments=[
        'jobs/data_ingestion.py',
        '--all',  # Fetch for all active tickers
        '--days',
        '{{ dag_run.conf.get("days", 365) }}',  # Default to 1 year of history
    ],
    env_vars=env_vars,
    # volumes=[volume],
    # volume_mounts=[volume_mount],
    get_logs=True,
    is_delete_operator_pod=True,  # Clean up pod after completion
    in_cluster=False,  # Set to True when running Airflow in K8s
    config_file='/path/to/kubeconfig',  # Path to your kubeconfig (local dev)
    # For production, remove config_file and set in_cluster=True
    dag=dag,
    container_resources=k8s.V1ResourceRequirements(
        requests={'memory': '1Gi', 'cpu': '1000m'},
        limits={'memory': '2Gi', 'cpu': '2000m'}
    ),
    # Longer timeout for historical data
    execution_timeout=timedelta(hours=2),
)

# Task dependencies (single task in this DAG)
backfill_task

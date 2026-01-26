"""
Data Ingestion DAG

Fetches market data from Schwab API daily after market close.
Runs at 4:00 PM EST Mon-Fri.
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
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# DAG definition
dag = DAG(
    'data_ingestion',
    default_args=default_args,
    description='Ingest market data from Schwab API',
    schedule_interval='0 16 * * 1-5',  # 4 PM Mon-Fri (after market close)
    start_date=days_ago(1),
    catchup=False,
    tags=['market-data', 'ingestion'],
)

# Environment variables for the pod
env_vars = {
    'DATABASE_URL': '{{ var.value.database_url }}',
    'SCHWAB_API_KEY': '{{ var.value.schwab_api_key }}',
    'SCHWAB_API_SECRET': '{{ var.value.schwab_api_secret }}',
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

# Kubernetes Pod Operator
ingest_data_task = KubernetesPodOperator(
    task_id='ingest_market_data',
    name='data-ingestion-pod',
    namespace='default',  # Change to your namespace
    image='market-intelligence-jobs:latest',  # Your Docker image
    cmds=['python'],
    arguments=['jobs/data_ingestion.py', '--all', '--days', '1'],
    env_vars=env_vars,
    # volumes=[volume],
    # volume_mounts=[volume_mount],
    get_logs=True,
    is_delete_operator_pod=True,  # Clean up pod after completion
    in_cluster=False,  # Set to True when running Airflow in K8s
    config_file='/path/to/kubeconfig',  # Path to your kubeconfig (local dev)
    # For production, remove config_file and set in_cluster=True
    dag=dag,
    resources=k8s.V1ResourceRequirements(
        requests={'memory': '512Mi', 'cpu': '500m'},
        limits={'memory': '1Gi', 'cpu': '1000m'}
    ),
)

# Task dependencies (single task in this DAG)
ingest_data_task

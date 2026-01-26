"""
Score Opportunities DAG

Calculates 10x opportunity scores for all tickers.
Runs at 5:00 PM EST Mon-Fri (after indicators are calculated).
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from airflow.sensors.external_task import ExternalTaskSensor
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
    'score_opportunities',
    default_args=default_args,
    description='Calculate 10x opportunity scores',
    schedule_interval='0 17 * * 1-5',  # 5:00 PM Mon-Fri
    start_date=days_ago(1),
    catchup=False,
    tags=['scoring', 'opportunities'],
)

# Environment variables
env_vars = {
    'DATABASE_URL': '{{ var.value.database_url }}',
    'PYTHONUNBUFFERED': '1',
}

# Wait for indicator calculation to complete
wait_for_indicators = ExternalTaskSensor(
    task_id='wait_for_indicators',
    external_dag_id='calculate_indicators',
    external_task_id='calculate_technical_indicators',
    allowed_states=['success'],
    failed_states=['failed', 'skipped'],
    mode='reschedule',
    timeout=3600,
    poke_interval=60,
    dag=dag,
)

# Score opportunities task
score_opportunities_task = KubernetesPodOperator(
    task_id='score_all_opportunities',
    name='score-opportunities-pod',
    namespace='default',
    image='market-intelligence-jobs:latest',
    cmds=['python'],
    arguments=['jobs/score_opportunities.py', '--all'],
    env_vars=env_vars,
    get_logs=True,
    is_delete_operator_pod=True,
    in_cluster=False,
    config_file='/path/to/kubeconfig',
    dag=dag,
    resources=k8s.V1ResourceRequirements(
        requests={'memory': '512Mi', 'cpu': '500m'},
        limits={'memory': '1Gi', 'cpu': '1000m'}
    ),
)

# Task dependencies
wait_for_indicators >> score_opportunities_task

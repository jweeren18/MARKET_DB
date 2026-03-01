"""
Generate Alerts DAG

Generates alerts based on opportunity score changes.
Runs at 5:15 PM EST Mon-Fri (after scoring).
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
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

# DAG definition
dag = DAG(
    'generate_alerts',
    default_args=default_args,
    description='Generate alerts based on score changes',
    schedule='15 17 * * 1-5',  # 5:15 PM Mon-Fri
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['alerts', 'notifications'],
)

# Environment variables
env_vars = {
    'DATABASE_URL': '{{ var.value.database_url }}',
    'PYTHONUNBUFFERED': '1',
}

with dag:

    # Wait for scoring to complete
    wait_for_scoring = ExternalTaskSensor(
        task_id='wait_for_scoring',
        external_dag_id='score_opportunities',
        external_task_id='score_all_opportunities',
        allowed_states=['success'],
        failed_states=['failed', 'skipped'],
        mode='reschedule',
        timeout=3600,
        poke_interval=60,
    )

    # Generate alerts task
    generate_alerts_task = KubernetesPodOperator(
        task_id='generate_dashboard_alerts',
        name='generate-alerts-pod',
        namespace='default',
        image='market-intelligence-jobs:latest',
        cmds=['python'],
        arguments=['jobs/generate_alerts.py'],
        env_vars=env_vars,
        get_logs=True,
        is_delete_operator_pod=True,
        in_cluster=False,
        config_file='/path/to/kubeconfig',
        container_resources=k8s.V1ResourceRequirements(
            requests={'memory': '256Mi', 'cpu': '250m'},
            limits={'memory': '512Mi', 'cpu': '500m'}
        ),
    )

    # Task dependencies
    wait_for_scoring >> generate_alerts_task

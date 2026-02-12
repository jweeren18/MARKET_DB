"""
Market Pipeline DAG (Kubernetes) — staged fan-out

Pipeline shape (per SCHWAB_API_REFERENCE.md scaling analysis):
    Stage 1: Ingest        → single pod  (rate-limit bound: 120 calls/min shared)
    Stage 2: Indicators    → N pods      (CPU bound — fan-out via dynamic task mapping)
    Stage 3: Scoring       → N pods      (CPU bound — fan-out via dynamic task mapping)
    Stage 4: Alerts        → single pod  (lightweight cross-ticker comparison)

Dynamic task mapping (requires Airflow ≥ 2.4):
    - compute_batch_arguments() queries the active-ticker count at run time
      and returns a list of argument vectors, one per batch.
    - KubernetesPodOperator.partial(...).expand(arguments=...) spawns one pod
      per batch for stages 2 and 3.
    - Fan-in between stages is implicit: all mapped instances must complete
      before the next stage starts.

Schedule: Mon-Fri at 4:15 PM ET (after market close)

NOTE: When this DAG is active, the individual K8s DAGs should be paused:
    - data_ingestion_dag
    - calculate_indicators_dag
    - score_opportunities_dag
    - generate_alerts_dag
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.decorators import task
from airflow.models import Variable
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from airflow.providers.cncf.kubernetes.secret import Secret
from kubernetes.client import models as k8s


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Tickers per fan-out pod.  Tune after benchmarks at full-market scale.
BATCH_SIZE = 500

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
    description="Full daily market pipeline with staged fan-out: ingest → indicators → scoring → alerts",
    schedule="15 16 * * 1-5",  # 4:15 PM ET Mon-Fri
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["pipeline", "market-data", "daily"],
)


# ---------------------------------------------------------------------------
# Environment-aware configuration via Airflow Variables
# ---------------------------------------------------------------------------
# Non-sensitive config is read from Airflow Variables (with sane defaults so
# the DAG parses even before Variables are set).
#
# Required Airflow Variables (non-sensitive):
#   k8s_namespace   - K8s namespace for pods         (default: "default")
#   k8s_image       - Container image URI            (default: "market-intelligence-jobs:latest")
#   k8s_in_cluster  - "true" when Airflow runs in K8s (default: "false")
#   k8s_config_file - Path to kubeconfig inside Airflow container (default: "/opt/airflow/kubeconfig")
#
# Sensitive credentials (API keys, tokens, DB URL) are stored in a K8s Secret
# named "market-pipeline-secrets" and mounted as env vars in each pod.
# This avoids storing secrets in Airflow's metadata DB (which is plaintext).
# See kubernetes/secrets.yaml.template for the Secret manifest.
# ---------------------------------------------------------------------------

K8S_NAMESPACE   = Variable.get("k8s_namespace",   default_var="default")
K8S_IMAGE       = Variable.get("k8s_image",        default_var="market-intelligence-jobs:latest")
K8S_IN_CLUSTER  = Variable.get("k8s_in_cluster",   default_var="false").lower() == "true"
K8S_CONFIG_FILE = Variable.get("k8s_config_file",  default_var="/opt/airflow/kubeconfig")
K8S_PULL_POLICY = Variable.get("k8s_pull_policy",  default_var="Never")  # "Never" for Kind, "Always" for ECR/EKS


# ---------------------------------------------------------------------------
# Shared K8s config
# ---------------------------------------------------------------------------

# Non-sensitive env vars passed directly.
ENV_VARS = {
    "PYTHONUNBUFFERED": "1",
}

# Sensitive credentials mounted from K8s Secret "market-pipeline-secrets".
# Each Secret() maps one key in the Secret to one env var in the pod.
POD_SECRETS = [
    Secret("env", "DATABASE_URL",        "market-pipeline-secrets", "DATABASE_URL"),
    Secret("env", "SECRET_KEY",          "market-pipeline-secrets", "SECRET_KEY"),
    Secret("env", "SCHWAB_API_KEY",      "market-pipeline-secrets", "SCHWAB_API_KEY"),
    Secret("env", "SCHWAB_API_SECRET",   "market-pipeline-secrets", "SCHWAB_API_SECRET"),
    Secret("env", "SCHWAB_CALLBACK_URL", "market-pipeline-secrets", "SCHWAB_CALLBACK_URL"),
    Secret("env", "SCHWAB_TOKENS_JSON",  "market-pipeline-secrets", "SCHWAB_TOKENS_JSON"),
]

# Resource presets — tune after benchmarks at full-market scale.
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

# Shared kwargs for every KubernetesPodOperator in this DAG.
# cmds is omitted — set per task:
#   • Single-pod tasks: cmds=["python"], script path in arguments.
#   • Mapped tasks:     cmds=["python", "<script>"], script path baked into cmds
#                       so arguments carries only the varying batch flags that
#                       .expand() maps over.
POD_DEFAULTS = dict(
    namespace=K8S_NAMESPACE,
    image=K8S_IMAGE,
    image_pull_policy=K8S_PULL_POLICY,
    env_vars=ENV_VARS,
    secrets=POD_SECRETS,
    get_logs=True,
    is_delete_operator_pod=True,
    in_cluster=K8S_IN_CLUSTER,
    **({} if K8S_IN_CLUSTER else {"config_file": K8S_CONFIG_FILE}),
)


# ---------------------------------------------------------------------------
# DAG body
# ---------------------------------------------------------------------------

with dag:

    # -----------------------------------------------------------------------
    # Batch-config generator
    # Runs as a PythonOperator in the Airflow worker (not in a K8s pod).
    # Pushes the argument vectors to XCom; consumed by both fan-out stages
    # via .expand().  Implicit dependency: compute_batch_arguments must finish
    # before any mapped task starts.
    # -----------------------------------------------------------------------

    @task
    def compute_batch_arguments() -> list:
        """
        Query active-ticker count and partition into BATCH_SIZE chunks.
        Returns a list of argument vectors — one per pod.  Each vector
        contains only the flags that vary across pods; the script path is
        baked into cmds in the .partial() call.

        This task runs in the Airflow worker (not a K8s pod), so it reads
        DATABASE_URL from the worker's environment (set in docker-compose.yaml).
        """
        import os
        from sqlalchemy import create_engine, text

        db_url = os.environ["DATABASE_URL"]
        engine = create_engine(db_url)
        with engine.connect() as conn:
            ticker_count = conn.execute(
                text("SELECT COUNT(*) FROM tickers WHERE is_active = true")
            ).scalar()
        engine.dispose()

        return [
            ["--all", "--batch-start", str(start), "--batch-size", str(BATCH_SIZE)]
            for start in range(0, ticker_count, BATCH_SIZE)
        ]

    batch_args = compute_batch_arguments()

    # -----------------------------------------------------------------------
    # Stage 1 — Ingest (single pod, rate-limit bound)
    # Built-in 0.5 s sleep between /pricehistory calls keeps throughput safely
    # under Schwab's 120 calls/min cap.
    # -----------------------------------------------------------------------

    ingest_task = KubernetesPodOperator(
        task_id="ingest_market_data",
        name="pipeline-ingest",
        cmds=["python"],
        arguments=["jobs/data_ingestion.py", "--all", "--days", "1"],
        container_resources=MEDIUM,
        **POD_DEFAULTS,
    )

    # -----------------------------------------------------------------------
    # Stage 2 — Indicators (fan-out, CPU bound)
    # Each mapped pod processes a contiguous slice of the sorted ticker list.
    # -----------------------------------------------------------------------

    indicators_batch = KubernetesPodOperator.partial(
        task_id="calculate_indicators_batch",
        name="pipeline-indicators-{{ task_instance.map_index }}",
        cmds=["python", "jobs/calculate_indicators.py"],
        container_resources=LARGE,
        **POD_DEFAULTS,
    ).expand(arguments=batch_args)

    # -----------------------------------------------------------------------
    # Stage 3 — Scoring (fan-out, CPU bound)
    # Uses the same batch partition as indicators so each pod scores exactly
    # the tickers whose indicators it can find freshly written.
    # -----------------------------------------------------------------------

    scoring_batch = KubernetesPodOperator.partial(
        task_id="score_opportunities_batch",
        name="pipeline-scoring-{{ task_instance.map_index }}",
        cmds=["python", "jobs/score_opportunities.py"],
        container_resources=MEDIUM,
        **POD_DEFAULTS,
    ).expand(arguments=batch_args)

    # -----------------------------------------------------------------------
    # Stage 4 — Alerts (single pod, lightweight)
    # Compares today's scores vs yesterday across all tickers — inherently
    # a cross-ticker operation, so no benefit from fan-out.
    # -----------------------------------------------------------------------

    alerts_task = KubernetesPodOperator(
        task_id="generate_alerts",
        name="pipeline-alerts",
        cmds=["python"],
        arguments=["jobs/generate_alerts.py"],
        container_resources=SMALL,
        **POD_DEFAULTS,
    )

    # -----------------------------------------------------------------------
    # Dependency graph
    #
    #   compute_batch_arguments ──┬──→ indicators[0..N] ──┐
    #                             │                        ▼
    #                             └──────────────→ scoring[0..N] ──→ alerts
    #   ingest ───────────────────────────────────→ indicators[0..N]
    #
    # Implicit (XCom from .expand):  compute_batch_arguments → indicators, scoring
    # Explicit (>> below):           ingest → indicators → scoring → alerts
    # Fan-in is implicit: all mapped instances finish before the next >> stage.
    # -----------------------------------------------------------------------

    ingest_task >> indicators_batch >> scoring_batch >> alerts_task

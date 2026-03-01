# Airflow + Kubernetes Setup Guide

This document explains how to set up and run the Market Intelligence platform using Apache Airflow for orchestration and Kubernetes for job execution.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   Apache Airflow 3                           │
│                                                               │
│  market_pipeline_local  (4:15 PM Mon-Fri)                    │
│  ┌──────────┐→┌───────────┐→┌─────────┐→┌────────────┐     │
│  │  Ingest  │ │Indicators │ │ Scoring │ │   Alerts   │     │
│  └──────────┘ └───────────┘ └─────────┘ └────────────┘     │
│        │            │            │            │               │
│        ▼            ▼            ▼            ▼               │
│  ┌──────────────────────────────────────────────────┐       │
│  │   PythonOperator  (local)  /  KubernetesPodOperator  (K8s) │
│  └──────────────────────────────────────────────────┘       │
└───────────────────────────┬──────────────────────────────────┘
                            │
┌───────────────────────────┴──────────────────────────────────┐
│          PostgreSQL + TimescaleDB (Shared State)              │
└───────────────────────────────────────────────────────────────┘
```

## Components

### 1. Airflow DAGs (Orchestration)

A single chained pipeline DAG runs all four stages sequentially at **4:15 PM Mon-Fri**:

| # | Task | What it does |
|---|------|--------------|
| 1 | **Ingest** | Fetch latest prices via Schwab API → `price_data` |
| 2 | **Indicators** | Compute 20+ technical indicators → `technical_indicators` |
| 3 | **Scoring** | Run 10x scoring algorithm → `opportunity_scores` |
| 4 | **Alerts** | Diff scores vs yesterday → `alerts` |

Two DAG variants exist:
- **`market_pipeline_local`** — active; uses `PythonOperator` (no K8s needed, runs in Docker Compose Airflow).
- **`market_pipeline_dag`** — K8s production variant; uses `KubernetesPodOperator` + dynamic task mapping for fan-out. Activate when a K8s cluster is available.

Standalone legacy DAGs (`data_ingestion_dag`, `calculate_indicators_dag`, `score_opportunities_dag`, `generate_alerts_dag`, `data_backfill_dag`) remain in `dags/` for reference but stay paused.

### 2. Kubernetes Jobs

Each DAG spawns Kubernetes pods using `KubernetesPodOperator`:

- **Image**: `market-intelligence-jobs:latest`
- **Base**: Python 3.10
- **Execution**: Standalone Python scripts
- **Dependencies**: Minimal (sqlalchemy, pandas, httpx)

### 3. Database

- **PostgreSQL 15** + **TimescaleDB** for time-series data
- Shared between all jobs and the FastAPI backend
- Stores: portfolios, price data, indicators, scores, alerts

## Local Development Setup

### Prerequisites

1. **Docker Desktop** with Kubernetes enabled
2. **kubectl** configured for local cluster
3. **Python 3.10+** for backend development

### Step 1: Start Local Kubernetes

```bash
# Enable Kubernetes in Docker Desktop
# Settings → Kubernetes → Enable Kubernetes

# Verify it's running
kubectl cluster-info
```

### Step 2: Build Jobs Container

```bash
# Build the jobs Docker image
cd kubernetes
chmod +x build-jobs.sh
./build-jobs.sh latest

# Verify image exists
docker images | grep market-intelligence-jobs
```

### Step 3: Start Airflow

```bash
cd airflow

# Set Airflow UID (Linux/Mac)
echo "AIRFLOW_UID=$(id -u)" > .env

# Windows: Create .env file with
echo "AIRFLOW_UID=50000" > .env

# Start Airflow services
docker compose up -d

# Check services are running
docker compose ps

# View logs
docker compose logs -f
```

Airflow UI will be available at: http://localhost:8080 (no login required — SimpleAuthManager all-admins mode).

### Step 4: Configure Airflow Variables

In the Airflow UI, go to **Admin → Variables** and add:

```
database_url = postgresql://postgres:password@host.docker.internal:5432/market_intelligence
schwab_api_key = your_api_key_here
schwab_api_secret = your_api_secret_here
```

**Note**: Use `host.docker.internal` to access localhost from Docker containers.

### Step 5: Update DAG Kubeconfig Path

Edit each DAG file in `airflow/dags/` and update:

```python
config_file='/path/to/kubeconfig',  # Change this
```

**Windows**: `C:\\Users\\YourName\\.kube\\config`
**Mac/Linux**: `/Users/yourname/.kube/config`

Or mount it in docker-compose (already configured):
```yaml
volumes:
  - ~/.kube/config:/opt/airflow/kubeconfig
```

Then update DAGs:
```python
config_file='/opt/airflow/kubeconfig',
```

### Step 6: Enable DAGs

1. Open Airflow UI: http://localhost:8080
2. Go to DAGs page
3. Toggle each DAG to **ON**:
   - data_ingestion
   - calculate_indicators
   - score_opportunities
   - generate_alerts

### Step 7: Test Run

**Option A: Manual Trigger**

1. Click on `data_ingestion` DAG
2. Click **Trigger DAG** (play button)
3. Watch the task run in real-time
4. Check logs in the task view

**Option B: Wait for Schedule**

The DAGs will run automatically at their scheduled times (Mon-Fri).

## Kubernetes Pod Debugging

### View Running Pods

```bash
# List pods in default namespace
kubectl get pods

# Watch pods in real-time
kubectl get pods -w
```

### View Pod Logs

```bash
# Find the pod name
kubectl get pods | grep data-ingestion

# View logs
kubectl logs data-ingestion-pod-xxxxx

# Follow logs
kubectl logs -f data-ingestion-pod-xxxxx
```

### Manually Run a Job (Testing)

```bash
# Run data ingestion job directly
kubectl run test-ingest \
  --image=market-intelligence-jobs:latest \
  --restart=Never \
  --env="DATABASE_URL=postgresql://postgres:password@host.docker.internal:5432/market_intelligence" \
  -- python jobs/data_ingestion.py --tickers AAPL,MSFT,NVDA --days 1

# View logs
kubectl logs test-ingest

# Clean up
kubectl delete pod test-ingest
```

## Production Deployment

### Cloud Kubernetes (AWS EKS / GCP GKE / Azure AKS)

#### Step 1: Push Image to Registry

```bash
# Set your container registry
export DOCKER_REGISTRY="your-registry.io/your-org"

# Build and push
cd kubernetes
./build-jobs.sh v1.0.0

# Verify
docker images | grep market-intelligence-jobs
```

#### Step 2: Deploy to Production K8s

```bash
# Configure kubectl for production cluster
kubectl config use-context production-cluster

# Create namespace
kubectl create namespace market-intelligence

# Create secrets
kubectl create secret generic db-credentials \
  --from-literal=database_url="postgresql://..." \
  --from-literal=schwab_api_key="..." \
  --from-literal=schwab_api_secret="..." \
  -n market-intelligence

# Update DAGs to use secrets (see airflow/dags/data_ingestion_dag.py)
```

#### Step 3: Update DAGs for Production

Change in each DAG file:

```python
# Remove local config_file
# config_file='/path/to/kubeconfig',  # Delete this line

# Enable in-cluster config
in_cluster=True,  # Change from False to True

# Update namespace
namespace='market-intelligence',  # Change from 'default'

# Update image with registry
image='your-registry.io/your-org/market-intelligence-jobs:v1.0.0',
```

#### Step 4: Use Managed Airflow (Optional)

**AWS MWAA (Managed Workflows for Apache Airflow)**
- Upload DAGs to S3 bucket
- Configure environment variables
- Point to your EKS cluster

**GCP Cloud Composer**
- Upload DAGs to Cloud Storage
- Configure Composer environment
- Point to your GKE cluster

**Azure Data Factory + Airflow**
- Similar managed service approach

### Environment Variables in Production

Use Kubernetes Secrets instead of Airflow Variables:

```python
env_vars = {
    'DATABASE_URL': {'secret_key_ref': {'name': 'db-credentials', 'key': 'database_url'}},
    'SCHWAB_API_KEY': {'secret_key_ref': {'name': 'db-credentials', 'key': 'schwab_api_key'}},
}
```

## Monitoring & Observability

### Airflow Monitoring

- **Airflow UI**: http://localhost:8080
  - DAG run history
  - Task logs
  - SLA misses
  - Task duration metrics

### Kubernetes Monitoring

```bash
# Resource usage
kubectl top pods

# Describe pod (shows events)
kubectl describe pod <pod-name>

# Get pod YAML
kubectl get pod <pod-name> -o yaml
```

### Database Monitoring

```sql
-- Check latest data ingestion
SELECT ticker, MAX(timestamp) as last_updated
FROM price_data
GROUP BY ticker
ORDER BY last_updated DESC;

-- Check indicator calculation
SELECT ticker, indicator_name, COUNT(*) as count
FROM technical_indicators
WHERE timestamp > NOW() - INTERVAL '1 day'
GROUP BY ticker, indicator_name;

-- Check opportunity scores
SELECT ticker, overall_score, confidence_level, timestamp
FROM opportunity_scores
WHERE timestamp > NOW() - INTERVAL '1 day'
ORDER BY overall_score DESC
LIMIT 10;
```

## Troubleshooting

### Common Issues

#### 1. DAG Import Errors

```bash
# Check DAG for syntax errors
cd airflow
python dags/data_ingestion_dag.py
```

#### 2. Pod Image Pull Errors

```bash
# Check if image exists
docker images | grep market-intelligence-jobs

# For local K8s, load image
docker save market-intelligence-jobs:latest | kubectl load -
```

#### 3. Database Connection Errors

```bash
# Test connection from Airflow container
docker exec -it airflow-airflow-scheduler-1 bash
python -c "import psycopg2; conn = psycopg2.connect('postgresql://postgres:password@host.docker.internal:5432/market_intelligence'); print('Connected!')"
```

#### 4. Kubeconfig Permission Errors

```bash
# Check kubeconfig is mounted
docker exec airflow-airflow-scheduler-1 ls -la /opt/airflow/kubeconfig

# Check permissions
chmod 644 ~/.kube/config
```

### Logs

**Airflow logs**: `airflow/logs/`
**Pod logs**: `kubectl logs <pod-name>`
**Database logs**: Check PostgreSQL logs

## Scaling

### Horizontal Pod Autoscaling

```yaml
# kubernetes/manifests/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: market-jobs-hpa
spec:
  scaleTargetRef:
    apiVersion: batch/v1
    kind: Job
    name: data-ingestion
  minReplicas: 1
  maxReplicas: 5
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 80
```

### Parallel Task Execution

To process tickers in parallel, modify DAG:

```python
# Create multiple pods for different ticker batches
tickers = ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN']
batch_size = 2

for i in range(0, len(tickers), batch_size):
    batch = tickers[i:i+batch_size]
    task_id = f'ingest_batch_{i}'

    KubernetesPodOperator(
        task_id=task_id,
        arguments=['jobs/data_ingestion.py', '--tickers', ','.join(batch)],
        ...
    )
```

## Next Steps

1. **Set up monitoring**: Add Prometheus + Grafana for metrics
2. **Configure alerts**: Email/Slack notifications on DAG failures
3. **Implement retry logic**: Exponential backoff for API calls
4. **Add data quality checks**: Validate data before scoring
5. **Optimize resource limits**: Tune CPU/memory based on actual usage

## Resources

- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [KubernetesPodOperator Guide](https://airflow.apache.org/docs/apache-airflow-providers-cncf-kubernetes/stable/operators.html)
- [Kubernetes Documentation](https://kubernetes.io/docs/home/)
- [TimescaleDB Documentation](https://docs.timescale.com/)

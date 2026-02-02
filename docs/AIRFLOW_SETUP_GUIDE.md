# Airflow Setup Guide for Market Intelligence Dashboard

Complete guide to set up Apache Airflow for automated daily market data ingestion.

## Overview

This guide covers:
1. Airflow installation and initialization
2. DAG deployment
3. Configuration and variables
4. Testing and monitoring
5. Production deployment

## Prerequisites

- Python 3.10+
- PostgreSQL running (for Airflow metadata and market data)
- Schwab API credentials configured
- Market data database initialized

## Option 1: Local Development Setup (Recommended for Testing)

### 1. Install Airflow

```bash
# Install Airflow with postgres provider
uv pip install "apache-airflow==2.8.1" \
    "apache-airflow-providers-postgres==5.10.0" \
    "apache-airflow-providers-cncf-kubernetes==8.0.0"

# Or add to pyproject.toml and run:
uv sync
```

### 2. Initialize Airflow

```bash
# Set Airflow home directory
export AIRFLOW_HOME=~/airflow  # Linux/Mac
# OR
set AIRFLOW_HOME=%USERPROFILE%\airflow  # Windows

# Initialize the database
airflow db init

# Create admin user
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password admin
```

### 3. Configure Airflow

Edit `~/airflow/airflow.cfg` (or `%USERPROFILE%\airflow\airflow.cfg` on Windows):

```ini
[core]
# DAGs folder - point to your project
dags_folder = C:\Users\Jake\Desktop\Kaje\Market_DB\airflow\dags

# Don't load examples
load_examples = False

# Executor - use LocalExecutor for development
executor = LocalExecutor

[database]
# Use PostgreSQL for metadata (recommended)
sql_alchemy_conn = postgresql+psycopg2://postgres:password@localhost:5433/airflow_metadata

# OR use SQLite for simple testing
# sql_alchemy_conn = sqlite:///C:/Users/Jake/airflow/airflow.db

[webserver]
# Web UI port
web_server_port = 8080

[scheduler]
# How often to check for new tasks
dag_dir_list_interval = 30
```

### 4. Create Airflow Metadata Database

If using PostgreSQL (recommended):

```bash
# Connect to your PostgreSQL instance
psql -U postgres -h localhost -p 5433

# Create airflow metadata database
CREATE DATABASE airflow_metadata;
\q

# Initialize Airflow with PostgreSQL
airflow db init
```

### 5. Set Airflow Variables

Airflow variables store configuration that DAGs can access.

**Via CLI:**
```bash
# Set required variables
airflow variables set database_url "postgresql://postgres:password@127.0.0.1:5433/market_intelligence"
airflow variables set schwab_api_key "ZqkmVsHYdHZjFFOXLJfwD2Q8titu9lJNsa9lWgAJP3TvtFdz"
airflow variables set schwab_api_secret "DUTHmOZ49BIQgtstAuAEXKM9aCxCbdA4TL4mXJ3RZ851BcQGPM7wiiUDgLvFekcf"
airflow variables set schwab_callback_url "https://127.0.0.1:8000/auth/callback"
```

**Via Web UI:**
1. Start Airflow webserver: `airflow webserver --port 8080`
2. Navigate to http://localhost:8080
3. Go to Admin > Variables
4. Click "+" to add each variable:
   - `database_url`: `postgresql://postgres:password@127.0.0.1:5433/market_intelligence`
   - `schwab_api_key`: Your Schwab API key
   - `schwab_api_secret`: Your Schwab API secret
   - `schwab_callback_url`: `https://127.0.0.1:8000/auth/callback`

### 6. Start Airflow Services

You need two terminals running:

**Terminal 1 - Webserver:**
```bash
airflow webserver --port 8080
```

**Terminal 2 - Scheduler:**
```bash
airflow scheduler
```

Access the UI at http://localhost:8080 (username: `admin`, password: `admin`)

### 7. Deploy DAGs

Your DAGs are already in the correct location:
- `airflow/dags/data_ingestion_dag.py` - Daily ingestion
- `airflow/dags/data_backfill_dag.py` - Historical backfill

Airflow will automatically detect them within ~30 seconds.

### 8. Test the DAG

**Via Web UI:**
1. Go to http://localhost:8080
2. Find `data_ingestion_daily` DAG
3. Toggle it ON (if paused)
4. Click "Trigger DAG" to test manually

**Via CLI:**
```bash
# Test the DAG
airflow dags test data_ingestion_daily 2024-01-27

# Trigger manually
airflow dags trigger data_ingestion_daily

# View logs
airflow tasks logs data_ingestion_daily ingest_daily_market_data <execution_date>
```

## Option 2: Docker Compose Setup (Production-Like)

### 1. Create Docker Compose File

Create `docker-compose-airflow.yml`:

```yaml
version: '3.8'

x-airflow-common:
  &airflow-common
  image: apache/airflow:2.8.1-python3.10
  environment:
    &airflow-common-env
    AIRFLOW__CORE__EXECUTOR: LocalExecutor
    AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres-airflow/airflow
    AIRFLOW__CORE__FERNET_KEY: ''
    AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: 'true'
    AIRFLOW__CORE__LOAD_EXAMPLES: 'false'
    AIRFLOW__WEBSERVER__SECRET_KEY: 'your-secret-key-here'
  volumes:
    - ./airflow/dags:/opt/airflow/dags
    - ./airflow/logs:/opt/airflow/logs
    - ./airflow/plugins:/opt/airflow/plugins
    - ./backend:/opt/airflow/backend
    - ./.env:/opt/airflow/.env
  user: "${AIRFLOW_UID:-50000}:0"
  depends_on:
    &airflow-common-depends-on
    postgres-airflow:
      condition: service_healthy

services:
  postgres-airflow:
    image: postgres:15
    environment:
      POSTGRES_USER: airflow
      POSTGRES_PASSWORD: airflow
      POSTGRES_DB: airflow
    volumes:
      - postgres-airflow-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "airflow"]
      interval: 5s
      retries: 5
    restart: always
    ports:
      - "5434:5432"

  airflow-webserver:
    <<: *airflow-common
    command: webserver
    ports:
      - "8080:8080"
    healthcheck:
      test: ["CMD", "curl", "--fail", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 5
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

  airflow-scheduler:
    <<: *airflow-common
    command: scheduler
    healthcheck:
      test: ["CMD", "curl", "--fail", "http://localhost:8974/health"]
      interval: 30s
      timeout: 10s
      retries: 5
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

  airflow-init:
    <<: *airflow-common
    entrypoint: /bin/bash
    command:
      - -c
      - |
        mkdir -p /sources/logs /sources/dags /sources/plugins
        chown -R "${AIRFLOW_UID}:0" /sources/{logs,dags,plugins}
        exec /entrypoint airflow version
    environment:
      <<: *airflow-common-env
      _AIRFLOW_DB_UPGRADE: 'true'
      _AIRFLOW_WWW_USER_CREATE: 'true'
      _AIRFLOW_WWW_USER_USERNAME: admin
      _AIRFLOW_WWW_USER_PASSWORD: admin
    user: "0:0"
    volumes:
      - ./airflow:/sources

volumes:
  postgres-airflow-data:
```

### 2. Start Airflow with Docker

```bash
# Create necessary directories
mkdir -p airflow/logs airflow/plugins

# Set Airflow UID (Linux/Mac)
echo -e "AIRFLOW_UID=$(id -u)" > .env

# Start services
docker-compose -f docker-compose-airflow.yml up -d

# Check status
docker-compose -f docker-compose-airflow.yml ps

# View logs
docker-compose -f docker-compose-airflow.yml logs -f airflow-scheduler
```

### 3. Configure Variables (Docker)

```bash
# Access airflow container
docker-compose -f docker-compose-airflow.yml exec airflow-webserver bash

# Set variables
airflow variables set database_url "postgresql://postgres:password@host.docker.internal:5433/market_intelligence"
airflow variables set schwab_api_key "your_key"
airflow variables set schwab_api_secret "your_secret"
airflow variables set schwab_callback_url "https://127.0.0.1:8000/auth/callback"

exit
```

## Option 3: For Local Development Without Kubernetes

If you're not ready for Kubernetes, modify the DAGs to use PythonOperator instead:

### Modified DAG for Local Execution

Create `airflow/dags/data_ingestion_local.py`:

```python
"""
Data Ingestion DAG (Local Execution)

Runs data ingestion job directly without Kubernetes.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
import sys
import os
import asyncio

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

def run_data_ingestion():
    """Run the data ingestion job."""
    from jobs.data_ingestion import main
    asyncio.run(main())

# Default arguments
default_args = {
    'owner': 'market-intelligence',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

# DAG definition
dag = DAG(
    'data_ingestion_local',
    default_args=default_args,
    description='Local data ingestion (no Kubernetes)',
    schedule_interval='0 16 * * 1-5',  # 4 PM Mon-Fri
    start_date=days_ago(1),
    catchup=False,
    tags=['market-data', 'ingestion', 'local'],
)

# Task
ingest_task = PythonOperator(
    task_id='ingest_market_data',
    python_callable=run_data_ingestion,
    dag=dag,
)
```

## Monitoring and Troubleshooting

### Check DAG Status

```bash
# List all DAGs
airflow dags list

# Check specific DAG
airflow dags show data_ingestion_daily

# View task instances
airflow tasks list data_ingestion_daily

# Check DAG state
airflow dags state data_ingestion_daily 2024-01-27
```

### View Logs

```bash
# Task logs
airflow tasks logs data_ingestion_daily ingest_daily_market_data 2024-01-27

# Web UI: Click on task > View Log
```

### Common Issues

**Issue: DAG not appearing**
```bash
# Check DAG for errors
python airflow/dags/data_ingestion_dag.py

# Check Airflow can import it
airflow dags list-import-errors
```

**Issue: Task fails with module not found**
```bash
# Ensure backend path is correct in DAG
# Or install dependencies in Airflow environment
cd backend
uv export -o requirements.txt
pip install -r requirements.txt
```

**Issue: Can't connect to database**
```bash
# Test database connection
airflow connections test postgres_default

# Or add connection
airflow connections add postgres_market_db \
    --conn-type postgres \
    --conn-host 127.0.0.1 \
    --conn-port 5433 \
    --conn-login postgres \
    --conn-password password \
    --conn-schema market_intelligence
```

## Production Deployment

### 1. Use Production Executor

Edit `airflow.cfg`:
```ini
[core]
executor = CeleryExecutor  # For distributed execution
# OR
executor = KubernetesExecutor  # For Kubernetes
```

### 2. Set up Redis (for Celery)

```bash
# Install Redis
# Ubuntu/Debian:
sudo apt-get install redis-server

# Mac:
brew install redis

# Start Redis
redis-server
```

### 3. Configure Email Alerts

Edit `airflow.cfg`:
```ini
[smtp]
smtp_host = smtp.gmail.com
smtp_starttls = True
smtp_ssl = False
smtp_user = your-email@gmail.com
smtp_password = your-app-password
smtp_port = 587
smtp_mail_from = your-email@gmail.com
```

Update DAG args:
```python
default_args = {
    'owner': 'market-intelligence',
    'email': ['your-email@gmail.com'],
    'email_on_failure': True,
    'email_on_retry': True,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}
```

### 4. Set up Health Checks

```bash
# Check scheduler health
airflow jobs check --job-type SchedulerJob

# Monitor via HTTP
curl http://localhost:8080/health
```

## Daily Operations

### Morning Checklist

```bash
# 1. Check yesterday's run
airflow dags list-runs -d data_ingestion_daily --state failed

# 2. If failed, check logs
airflow tasks logs data_ingestion_daily ingest_daily_market_data <date>

# 3. Manually trigger if needed
airflow dags trigger data_ingestion_daily

# 4. Verify data quality
uv run python scripts/check_data_quality.py
```

### Weekly Checklist

```bash
# Check for stale DAGs
airflow dags list-runs -d data_ingestion_daily --num-runs 7

# Review logs
ls -lh ~/airflow/logs/

# Clean up old logs (optional)
airflow db clean --clean-before-timestamp "2024-01-01" --yes
```

## Quick Start Commands

```bash
# Start Airflow (local)
airflow webserver --port 8080 &
airflow scheduler &

# Stop Airflow
pkill -f "airflow webserver"
pkill -f "airflow scheduler"

# Restart Airflow
pkill -f "airflow"; sleep 2; airflow webserver --port 8080 & airflow scheduler &

# Manual test run
airflow dags test data_ingestion_daily 2024-01-27

# Trigger for production
airflow dags trigger data_ingestion_daily
```

## Next Steps

1. ✅ Set up Airflow locally
2. ✅ Test daily ingestion DAG
3. ✅ Monitor first few runs
4. 🔄 Deploy to production (Kubernetes/Docker)
5. 🔄 Set up alerting
6. 🔄 Add more DAGs (Phase 1D-1G)

See [AIRFLOW_KUBERNETES.md](AIRFLOW_KUBERNETES.md) for Kubernetes deployment guide (coming soon).

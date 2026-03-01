"""
Data Ingestion DAG (Local Execution)

Runs data ingestion job directly without Kubernetes.
Perfect for local development and testing.

Schedule: Mon-Fri at 4:00 PM EST (after market close)
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import sys
import os

# Add backend to Python path
backend_path = os.path.join(os.path.dirname(__file__), '..', '..', 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

def run_daily_ingestion(**context):
    """
    Run daily market data ingestion.

    Fetches yesterday's data for all active tickers.
    """
    import asyncio
    import logging
    from sqlalchemy.orm import Session
    from app.database import SessionLocal
    from jobs.data_ingestion import DataIngestionJob

    logger = logging.getLogger(__name__)
    logger.info("Starting daily market data ingestion")

    # Create database session
    db = SessionLocal()

    try:
        job = DataIngestionJob(db)

        # Get all active tickers
        tickers = job.get_active_tickers()
        logger.info(f"Fetching data for {len(tickers)} active tickers")

        # Run the ingestion job
        asyncio.run(job.run(tickers, days=1))

        logger.info("Daily ingestion completed successfully")

    except Exception as e:
        logger.error(f"Daily ingestion failed: {e}", exc_info=True)
        raise
    finally:
        db.close()


# Default arguments
default_args = {
    'owner': 'market-intelligence',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(minutes=30),
}

# DAG definition
dag = DAG(
    'data_ingestion_local',
    default_args=default_args,
    description='Local daily market data ingestion (no Kubernetes required)',
    schedule='0 16 * * 1-5',  # 4 PM Mon-Fri (after market close)
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['market-data', 'ingestion', 'local'],
)

with dag:

    # Ingestion task
    ingest_task = PythonOperator(
        task_id='ingest_daily_market_data',
        python_callable=run_daily_ingestion,
    )

"""
Calculate Indicators DAG (Local Execution)

Runs indicator calculation job directly without Kubernetes.
Perfect for local development and testing.

Schedule: Mon-Fri at 4:30 PM EST (30 minutes after data ingestion)
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
import sys
import os

# Add backend to Python path
backend_path = os.path.join(os.path.dirname(__file__), '..', '..', 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)


def run_indicator_calculation(**context):
    """
    Run daily indicator calculation for all active tickers.

    Calculates technical indicators based on latest price data.
    """
    import logging
    from app.database import SessionLocal
    from app.services.signal_engine import SignalEngine

    logger = logging.getLogger(__name__)
    logger.info("Starting daily indicator calculation")

    # Create database session
    db = SessionLocal()

    try:
        signal_engine = SignalEngine(db)

        # Calculate indicators for all tickers
        # Use 252 days lookback (1 trading year)
        result = signal_engine.calculate_indicators_for_all_tickers(
            lookback_days=252,
            force_recalculate=False  # Don't recalculate if already done today
        )

        logger.info(f"Indicator calculation completed")
        logger.info(f"Total tickers: {result['total_tickers']}")
        logger.info(f"Successful: {result['successful']}")
        logger.info(f"Skipped: {result['skipped']}")
        logger.info(f"Failed: {result['failed']}")

        if result['failed'] > 0:
            logger.warning(f"Some tickers failed: {result['errors']}")

    except Exception as e:
        logger.error(f"Indicator calculation failed: {e}", exc_info=True)
        raise
    finally:
        db.close()


# Default arguments
default_args = {
    'owner': 'market-intelligence',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(minutes=45),
}

# DAG definition
dag = DAG(
    'calculate_indicators_local',
    default_args=default_args,
    description='Local daily indicator calculation (no Kubernetes required)',
    schedule_interval='30 16 * * 1-5',  # 4:30 PM Mon-Fri (30 min after data ingestion)
    start_date=days_ago(1),
    catchup=False,
    tags=['indicators', 'technical-analysis', 'local'],
)

# Indicator calculation task
calculate_task = PythonOperator(
    task_id='calculate_technical_indicators',
    python_callable=run_indicator_calculation,
    provide_context=True,
    dag=dag,
)

calculate_task

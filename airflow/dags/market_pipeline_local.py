"""
Market Pipeline DAG (Local Execution)

Single DAG that runs the full daily pipeline in sequence without Kubernetes:
    1. ingest_market_data      — fetch latest prices via Schwab/yfinance
    2. calculate_indicators    — compute technical indicators
    3. score_opportunities     — calculate 10x opportunity scores
    4. generate_alerts         — create alerts from score changes

Schedule: Mon-Fri at 4:15 PM ET (after market close)

NOTE: When this DAG is active, the standalone local DAGs should be paused:
    - data_ingestion_local
    - calculate_indicators_local
    - score_opportunities_local
"""

import sys
import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

# Add backend to Python path so job imports resolve
backend_path = os.path.join(os.path.dirname(__file__), "..", "..", "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)


# ---------------------------------------------------------------------------
# Task callables
# ---------------------------------------------------------------------------


def run_data_ingestion(**context):
    """Fetch latest market data for all active tickers."""
    import asyncio
    import logging

    from app.database import SessionLocal
    from jobs.data_ingestion import DataIngestionJob

    logger = logging.getLogger(__name__)
    db = SessionLocal()
    try:
        job = DataIngestionJob(db)
        tickers = job.get_active_tickers()
        logger.info(f"Fetching data for {len(tickers)} active tickers")
        asyncio.run(job.run(tickers, days=1))
        logger.info("Data ingestion completed")
    except Exception as e:
        logger.error(f"Data ingestion failed: {e}", exc_info=True)
        raise
    finally:
        db.close()


def run_indicator_calculation(**context):
    """Calculate technical indicators for all active tickers."""
    import logging

    from app.database import SessionLocal
    from app.services.signal_engine import SignalEngine

    logger = logging.getLogger(__name__)
    db = SessionLocal()
    try:
        signal_engine = SignalEngine(db)
        result = signal_engine.calculate_indicators_for_all_tickers(
            lookback_days=252,
            force_recalculate=False,
        )
        logger.info(
            f"Indicators done — successful={result['successful']}, "
            f"skipped={result['skipped']}, failed={result['failed']}"
        )
        if result["failed"] > 0:
            raise RuntimeError(f"{result['failed']} tickers failed: {result['errors']}")
    except Exception as e:
        logger.error(f"Indicator calculation failed: {e}", exc_info=True)
        raise
    finally:
        db.close()


def run_opportunity_scoring(**context):
    """Score all active tickers and persist results."""
    import logging
    from decimal import Decimal

    from app.database import SessionLocal
    from app.models import OpportunityScore
    from app.services.opportunity_scorer import OpportunityScorer
    from jobs.score_opportunities import make_json_serializable

    logger = logging.getLogger(__name__)
    db = SessionLocal()
    try:
        scorer = OpportunityScorer(db)
        results = scorer.score_all_tickers(min_confidence=0.0, benchmark_ticker="SPY")

        stored_count = 0
        for score_data in results["scores"]:
            try:
                full_result = scorer.score_ticker(
                    score_data["ticker"], benchmark_ticker="SPY"
                )

                existing = (
                    db.query(OpportunityScore)
                    .filter(
                        OpportunityScore.ticker == score_data["ticker"],
                        OpportunityScore.timestamp >= datetime.now().date(),
                    )
                    .first()
                )

                if existing:
                    existing.overall_score = Decimal(str(full_result["overall_score"]))
                    existing.confidence_level = Decimal(str(full_result["confidence"]))
                    existing.component_scores = make_json_serializable(full_result["components"])
                    existing.explanation = make_json_serializable(full_result)
                    existing.bull_case = Decimal(str(full_result["scenarios"]["bull"]))
                    existing.base_case = Decimal(str(full_result["scenarios"]["base"]))
                    existing.bear_case = Decimal(str(full_result["scenarios"]["bear"]))
                    existing.timestamp = full_result["timestamp"]
                else:
                    db.add(
                        OpportunityScore(
                            ticker=full_result["ticker"],
                            timestamp=full_result["timestamp"],
                            overall_score=Decimal(str(full_result["overall_score"])),
                            confidence_level=Decimal(str(full_result["confidence"])),
                            component_scores=make_json_serializable(full_result["components"]),
                            explanation=make_json_serializable(full_result),
                            bull_case=Decimal(str(full_result["scenarios"]["bull"])),
                            base_case=Decimal(str(full_result["scenarios"]["base"])),
                            bear_case=Decimal(str(full_result["scenarios"]["bear"])),
                        )
                    )
                stored_count += 1
            except Exception as e:
                logger.error(f"Error storing score for {score_data['ticker']}: {e}")

        db.commit()
        logger.info(f"Scoring done — scored={results['scored']}, stored={stored_count}")
    except Exception as e:
        logger.error(f"Opportunity scoring failed: {e}", exc_info=True)
        raise
    finally:
        db.close()


def run_alert_generation(**context):
    """Generate alerts based on score changes."""
    import logging

    from app.database import SessionLocal
    from jobs.generate_alerts import AlertGenerationJob

    logger = logging.getLogger(__name__)
    db = SessionLocal()
    try:
        job = AlertGenerationJob(db)
        job.run()
        logger.info("Alert generation completed")
    except Exception as e:
        logger.error(f"Alert generation failed: {e}", exc_info=True)
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# DAG definition
# ---------------------------------------------------------------------------

default_args = {
    "owner": "market-intelligence",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    "market_pipeline_local",
    default_args=default_args,
    description="Full daily market pipeline — local execution (no Kubernetes)",
    schedule_interval="15 16 * * 1-5",  # 4:15 PM ET Mon-Fri
    start_date=days_ago(1),
    catchup=False,
    tags=["pipeline", "market-data", "local"],
)


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

ingest_task = PythonOperator(
    task_id="ingest_market_data",
    python_callable=run_data_ingestion,
    provide_context=True,
    execution_timeout=timedelta(minutes=30),
    dag=dag,
)

indicators_task = PythonOperator(
    task_id="calculate_indicators",
    python_callable=run_indicator_calculation,
    provide_context=True,
    execution_timeout=timedelta(minutes=45),
    dag=dag,
)

scoring_task = PythonOperator(
    task_id="score_opportunities",
    python_callable=run_opportunity_scoring,
    provide_context=True,
    execution_timeout=timedelta(minutes=60),
    dag=dag,
)

alerts_task = PythonOperator(
    task_id="generate_alerts",
    python_callable=run_alert_generation,
    provide_context=True,
    execution_timeout=timedelta(minutes=15),
    dag=dag,
)


# ---------------------------------------------------------------------------
# Dependency chain
# ---------------------------------------------------------------------------

ingest_task >> indicators_task >> scoring_task >> alerts_task

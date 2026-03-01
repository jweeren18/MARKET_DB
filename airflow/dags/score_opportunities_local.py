"""
Score Opportunities DAG (Local Execution)

Runs opportunity scoring job directly without Kubernetes.
Perfect for local development and testing.

Schedule: Mon-Fri at 5:00 PM EST (1 hour after indicator calculation)
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


def run_opportunity_scoring(**context):
    """
    Run daily opportunity scoring for all active tickers.

    Scores tickers based on:
    - Momentum (price trends, technical indicators)
    - Valuation divergence (price vs bands/ranges)
    - Growth acceleration (momentum strength)
    - Relative strength (vs benchmark)
    - Sector momentum (trend strength)
    """
    import logging
    from app.database import SessionLocal
    from app.services.opportunity_scorer import OpportunityScorer
    from app.models import OpportunityScore
    from decimal import Decimal

    logger = logging.getLogger(__name__)
    logger.info("Starting daily opportunity scoring")

    db = SessionLocal()

    try:
        scorer = OpportunityScorer(db)

        # Score all tickers with minimum confidence of 50%
        results = scorer.score_all_tickers(
            min_confidence=50.0,
            benchmark_ticker="SPY"
        )

        # Store scores in database
        stored_count = 0
        for score_data in results["scores"]:
            try:
                # Get full score details
                full_result = scorer.score_ticker(
                    score_data["ticker"],
                    benchmark_ticker="SPY"
                )

                # Create or update score record
                score_record = OpportunityScore(
                    ticker=full_result["ticker"],
                    timestamp=full_result["timestamp"],
                    overall_score=Decimal(str(full_result["overall_score"])),
                    confidence_level=Decimal(str(full_result["confidence"])),
                    component_scores=full_result["components"],
                    explanation=full_result,
                    bull_case=Decimal(str(full_result["scenarios"]["bull"])),
                    base_case=Decimal(str(full_result["scenarios"]["base"])),
                    bear_case=Decimal(str(full_result["scenarios"]["bear"]))
                )

                # Check if exists
                existing = db.query(OpportunityScore).filter(
                    OpportunityScore.ticker == score_data["ticker"],
                    OpportunityScore.timestamp >= datetime.now().date()
                ).first()

                if existing:
                    existing.overall_score = score_record.overall_score
                    existing.confidence_level = score_record.confidence_level
                    existing.component_scores = score_record.component_scores
                    existing.explanation = score_record.explanation
                    existing.bull_case = score_record.bull_case
                    existing.base_case = score_record.base_case
                    existing.bear_case = score_record.bear_case
                    existing.timestamp = score_record.timestamp
                else:
                    db.add(score_record)

                stored_count += 1

            except Exception as e:
                logger.error(f"Error storing score for {score_data['ticker']}: {e}")

        db.commit()

        logger.info(f"Opportunity scoring completed")
        logger.info(f"Total tickers: {results['total_tickers']}")
        logger.info(f"Successfully scored: {results['scored']}")
        logger.info(f"Stored in database: {stored_count}")
        logger.info(f"Skipped: {results['skipped']}")

        if results["scores"]:
            top_3 = results["scores"][:3]
            top_3_str = ", ".join(f"{s['ticker']} ({s['score']:.1f})" for s in top_3)
            logger.info(f"Top 3 opportunities: {top_3_str}")

        if results['errors']:
            logger.warning(f"Errors encountered: {len(results['errors'])}")

    except Exception as e:
        logger.error(f"Opportunity scoring failed: {e}", exc_info=True)
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
    'execution_timeout': timedelta(minutes=60),
}

# DAG definition
dag = DAG(
    'score_opportunities_local',
    default_args=default_args,
    description='Local daily opportunity scoring (no Kubernetes required)',
    schedule='0 17 * * 1-5',  # 5:00 PM Mon-Fri (1 hour after indicators)
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['opportunities', 'scoring', 'local'],
)

with dag:

    # Scoring task
    score_task = PythonOperator(
        task_id='score_opportunities',
        python_callable=run_opportunity_scoring,
    )

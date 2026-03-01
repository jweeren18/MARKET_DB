#!/usr/bin/env python3
"""
Pipeline Orchestrator

Runs the full daily data pipeline in sequence:
    1. Data Ingestion   — fetch latest market prices
    2. Indicators       — calculate technical indicators
    3. Scoring          — calculate 10x opportunity scores
    4. Alerts           — generate alerts from score changes

Manual trigger for testing and ad-hoc runs.
Scheduled execution is handled by the Airflow DAGs:
    - airflow/dags/market_pipeline_dag.py        (Kubernetes / production)
    - airflow/dags/market_pipeline_local.py      (local Airflow)

Usage:
    python backend/jobs/run_pipeline.py                        # run full pipeline
    python backend/jobs/run_pipeline.py --ingest-days 5        # backfill 5 days of prices
    python backend/jobs/run_pipeline.py --lookback 30 --force  # recalculate with 30-day window
"""

import sys
import asyncio
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Add backend to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("pipeline")


# ---------------------------------------------------------------------------
# Step helpers — each returns True on success, False on failure
# ---------------------------------------------------------------------------

def step_ingest(days: int = 1) -> bool:
    """Fetch latest market data for all active tickers."""
    from data_ingestion import DataIngestionJob

    db = SessionLocal()
    try:
        job = DataIngestionJob(db)
        tickers = job.get_active_tickers()
        logger.info(f"[INGEST] Fetching {days} day(s) of data for {len(tickers)} tickers")
        asyncio.run(job.run(tickers, days))
        logger.info("[INGEST] Completed successfully")
        return True
    except Exception as e:
        logger.error(f"[INGEST] Failed: {e}", exc_info=True)
        return False
    finally:
        db.close()


def step_indicators(lookback_days: int = 252, force: bool = False) -> bool:
    """Calculate technical indicators for all active tickers."""
    from calculate_indicators import calculate_indicators_for_all_tickers

    logger.info(f"[INDICATORS] Calculating (lookback={lookback_days}d, force={force})")
    try:
        results = calculate_indicators_for_all_tickers(
            lookback_days=lookback_days, force=force
        )
        logger.info(
            f"[INDICATORS] Done — successful={results['successful']}, "
            f"skipped={results['skipped']}, failed={results['failed']}"
        )
        return results["failed"] == 0
    except Exception as e:
        logger.error(f"[INDICATORS] Failed: {e}", exc_info=True)
        return False


def step_scoring(benchmark: str = "SPY") -> bool:
    """Score all active tickers."""
    from score_opportunities import score_all_tickers

    logger.info(f"[SCORING] Scoring all tickers (benchmark={benchmark})")
    try:
        results = score_all_tickers(benchmark=benchmark)
        logger.info(
            f"[SCORING] Done — scored={results['scored']}, "
            f"skipped={results['skipped']}"
        )
        return len(results.get("errors", [])) == 0
    except Exception as e:
        logger.error(f"[SCORING] Failed: {e}", exc_info=True)
        return False


def step_alerts() -> bool:
    """Generate alerts based on score changes."""
    from generate_alerts import AlertGenerationJob

    db = SessionLocal()
    try:
        logger.info("[ALERTS] Running alert generation")
        job = AlertGenerationJob(db)
        job.run()
        logger.info("[ALERTS] Completed successfully")
        return True
    except Exception as e:
        logger.error(f"[ALERTS] Failed: {e}", exc_info=True)
        return False
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------

def run_pipeline(ingest_days: int = 1, indicator_lookback: int = 252, force: bool = False):
    """Execute the full pipeline in order. Continues past failures."""
    logger.info("=" * 70)
    logger.info("MARKET PIPELINE START")
    logger.info(f"  Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)

    steps = [
        ("Data Ingestion", lambda: step_ingest(days=ingest_days)),
        ("Indicators",     lambda: step_indicators(lookback_days=indicator_lookback, force=force)),
        ("Scoring",        step_scoring),
        ("Alerts",         step_alerts),
    ]

    results = {}
    for name, fn in steps:
        logger.info(f"\n--- {name} ---")
        start = datetime.now()
        success = fn()
        elapsed = (datetime.now() - start).total_seconds()
        results[name] = {"success": success, "elapsed": elapsed}
        status = "OK" if success else "FAILED"
        logger.info(f"--- {name}: {status} ({elapsed:.1f}s) ---")

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("PIPELINE SUMMARY")
    for name, info in results.items():
        status = "OK" if info["success"] else "FAILED"
        logger.info(f"  {name:20s} {status:8s} ({info['elapsed']:.1f}s)")
    all_ok = all(r["success"] for r in results.values())
    logger.info(f"\nOverall: {'SUCCESS' if all_ok else 'PARTIAL FAILURE'}")
    logger.info(f"  Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)
    return all_ok


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Manual pipeline runner (scheduled runs use Airflow DAGs)"
    )
    parser.add_argument(
        "--ingest-days", type=int, default=1,
        help="Days of price data to ingest (default: 1)",
    )
    parser.add_argument(
        "--lookback", type=int, default=252,
        help="Indicator lookback period in days (default: 252)",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Force indicator recalculation even if already done today",
    )

    args = parser.parse_args()

    run_pipeline(
        ingest_days=args.ingest_days,
        indicator_lookback=args.lookback,
        force=args.force,
    )


if __name__ == "__main__":
    main()

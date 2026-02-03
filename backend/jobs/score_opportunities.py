"""
Score Opportunities Job

Batch job to calculate 10x opportunity scores for all active tickers.
Can be run manually or scheduled via Airflow.

Usage:
    python backend/jobs/score_opportunities.py --all
    python backend/jobs/score_opportunities.py --ticker AAPL
    python backend/jobs/score_opportunities.py --all --min-confidence 60
    python backend/jobs/score_opportunities.py --all --batch-start 0 --batch-size 500
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

import argparse
import logging
from datetime import datetime
from decimal import Decimal

from app.database import SessionLocal
from app.models import OpportunityScore, Ticker
from app.services.opportunity_scorer import OpportunityScorer


def make_json_serializable(obj):
    """Convert datetime objects to ISO format strings for JSON serialization."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
    elif isinstance(obj, Decimal):
        return float(obj)
    else:
        return obj


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def score_and_store_ticker(
    ticker: str,
    benchmark: str = "SPY",
    db_session=None
):
    """Score a ticker and store the result in database."""
    db = db_session or SessionLocal()

    try:
        scorer = OpportunityScorer(db)

        logger.info(f"Scoring {ticker}")
        result = scorer.score_ticker(ticker, benchmark_ticker=benchmark)

        if "error" in result:
            logger.warning(f"[SKIP] {ticker}: {result.get('message', 'Insufficient data')}")
            return None

        # Store in database
        score_record = OpportunityScore(
            ticker=ticker,
            timestamp=result["timestamp"],
            overall_score=Decimal(str(result["overall_score"])),
            confidence_level=Decimal(str(result["confidence"])),
            component_scores=make_json_serializable(result["components"]),
            explanation=make_json_serializable(result),  # Store full explanation as JSON
            bull_case=Decimal(str(result["scenarios"]["bull"])),
            base_case=Decimal(str(result["scenarios"]["base"])),
            bear_case=Decimal(str(result["scenarios"]["bear"]))
        )

        # Check if score already exists for today
        existing = db.query(OpportunityScore).filter(
            OpportunityScore.ticker == ticker,
            OpportunityScore.timestamp >= datetime.now().date()
        ).first()

        if existing:
            # Update existing
            existing.overall_score = score_record.overall_score
            existing.confidence_level = score_record.confidence_level
            existing.component_scores = make_json_serializable(result["components"])
            existing.explanation = make_json_serializable(result)
            existing.bull_case = score_record.bull_case
            existing.base_case = score_record.base_case
            existing.bear_case = score_record.bear_case
            existing.timestamp = score_record.timestamp
        else:
            # Insert new
            db.add(score_record)

        db.commit()

        logger.info(f"[OK] {ticker}: Score={result['overall_score']:.1f}, "
                   f"Confidence={result['confidence']:.1f}%")

        return result

    except Exception as e:
        logger.error(f"[ERROR] {ticker}: {e}", exc_info=True)
        if db_session is None:
            db.close()
        raise

    finally:
        if db_session is None:
            db.close()


def score_all_tickers(
    min_confidence: float = 0.0,
    benchmark: str = "SPY"
):
    """Score all active tickers."""
    db = SessionLocal()

    try:
        scorer = OpportunityScorer(db)

        logger.info("=" * 80)
        logger.info("SCORE OPPORTUNITIES - ALL TICKERS")
        logger.info("=" * 80)
        logger.info(f"Benchmark: {benchmark}")
        logger.info(f"Min confidence: {min_confidence}%")
        logger.info("")

        start_time = datetime.now()

        # Use batch scoring method
        results = scorer.score_all_tickers(
            min_confidence=min_confidence,
            benchmark_ticker=benchmark
        )

        # Store each score
        stored_count = 0
        for score_data in results["scores"]:
            try:
                # Get full score for this ticker
                full_result = scorer.score_ticker(
                    score_data["ticker"],
                    benchmark_ticker=benchmark
                )

                # Store in database
                score_record = OpportunityScore(
                    ticker=full_result["ticker"],
                    timestamp=full_result["timestamp"],
                    overall_score=Decimal(str(full_result["overall_score"])),
                    confidence_level=Decimal(str(full_result["confidence"])),
                    component_scores=make_json_serializable(full_result["components"]),
                    explanation=make_json_serializable(full_result),
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
                    existing.component_scores = make_json_serializable(full_result["components"])
                    existing.explanation = make_json_serializable(full_result)
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

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Print summary
        logger.info("")
        logger.info("=" * 80)
        logger.info("SCORING SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total tickers: {results['total_tickers']}")
        logger.info(f"Successfully scored: {results['scored']}")
        logger.info(f"Stored in database: {stored_count}")
        logger.info(f"Skipped: {results['skipped']}")
        logger.info(f"Duration: {duration:.2f} seconds")

        if results["scores"]:
            logger.info("")
            logger.info("Top 10 Opportunities:")
            for i, score in enumerate(results["scores"][:10], 1):
                logger.info(f"  {i}. {score['ticker']}: {score['score']:.1f} "
                          f"(confidence: {score['confidence']:.0f}%)")

        if results["errors"]:
            logger.info("")
            logger.info("ERRORS:")
            for error in results["errors"]:
                logger.error(f"  {error['ticker']}: {error['error']}")

        logger.info("=" * 80)

        return results

    finally:
        db.close()


def get_active_tickers():
    """Get alphabetically-sorted list of all active tickers."""
    db = SessionLocal()
    try:
        tickers = db.query(Ticker).filter(Ticker.is_active == True).all()
        return sorted([t.ticker for t in tickers])
    finally:
        db.close()


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Calculate 10x opportunity scores for tickers"
    )
    parser.add_argument(
        "--ticker",
        type=str,
        help="Score a specific ticker (e.g., AAPL)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Score all active tickers"
    )
    parser.add_argument(
        "--benchmark",
        type=str,
        default="SPY",
        help="Benchmark ticker for relative strength (default: SPY)"
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.0,
        help="Minimum confidence level to include (default: 0)"
    )
    parser.add_argument(
        "--batch-start",
        type=int,
        default=None,
        help="Start index into sorted active-ticker list (for K8s fan-out)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Number of tickers to process from batch-start (for K8s fan-out)"
    )

    args = parser.parse_args()

    if args.ticker:
        # Score single ticker
        score_and_store_ticker(
            ticker=args.ticker,
            benchmark=args.benchmark
        )
    elif args.all:
        if args.batch_start is not None and args.batch_size is not None:
            # Batched mode — score a slice of the ticker list (K8s fan-out)
            all_tickers = get_active_tickers()
            batch = all_tickers[args.batch_start:args.batch_start + args.batch_size]
            logger.info(f"Batch [{args.batch_start}:{args.batch_start + args.batch_size}] — {len(batch)} tickers")
            for ticker in batch:
                score_and_store_ticker(ticker=ticker, benchmark=args.benchmark)
        else:
            # Full run — all tickers sequentially
            score_all_tickers(
                min_confidence=args.min_confidence,
                benchmark=args.benchmark
            )
    else:
        logger.error("Must specify either --ticker or --all")
        parser.print_help()


if __name__ == "__main__":
    main()

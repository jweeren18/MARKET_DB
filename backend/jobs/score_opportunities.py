"""
Score Opportunities Job

Batch job to calculate 10x opportunity scores for all active tickers.
Can be run manually or scheduled via Airflow.

Usage:
    python backend/jobs/score_opportunities.py --all
    python backend/jobs/score_opportunities.py --ticker AAPL
    python backend/jobs/score_opportunities.py --all --min-confidence 60
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
from app.models import OpportunityScore
from app.services.opportunity_scorer import OpportunityScorer


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
            component_scores=result["components"],
            explanation=result,  # Store full explanation as JSON
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
            existing.component_scores = score_record.component_scores
            existing.explanation = score_record.explanation
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

    args = parser.parse_args()

    if args.ticker:
        # Score single ticker
        score_and_store_ticker(
            ticker=args.ticker,
            benchmark=args.benchmark
        )
    elif args.all:
        # Score all tickers
        score_all_tickers(
            min_confidence=args.min_confidence,
            benchmark=args.benchmark
        )
    else:
        logger.error("Must specify either --ticker or --all")
        parser.print_help()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Score Opportunities Job

Calculates 10x opportunity scores for all tickers.
Runs as a Kubernetes pod triggered by Airflow.

Usage:
    python jobs/score_opportunities.py [--tickers AAPL,MSFT,NVDA]
"""

import argparse
import logging
from datetime import datetime
from typing import List

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Ticker
from app.services.opportunity_scorer import OpportunityScorer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ScoringJob:
    """Job for scoring opportunities."""

    def __init__(self, db: Session):
        self.db = db
        self.scorer = OpportunityScorer(db)

    def get_active_tickers(self) -> List[str]:
        """Get list of active tickers."""
        tickers = self.db.query(Ticker).filter(Ticker.is_active == True).all()
        return [t.ticker for t in tickers]

    def run(self, tickers: List[str]):
        """Run the scoring job."""
        logger.info(f"Starting opportunity scoring for {len(tickers)} tickers")

        success_count = 0
        fail_count = 0

        for symbol in tickers:
            try:
                score_result = self.scorer.score_ticker(symbol)

                if score_result:
                    logger.info(
                        f"{symbol}: Score={score_result['overall_score']:.2f}, "
                        f"Confidence={score_result['confidence_level']:.2f}"
                    )
                    success_count += 1
                else:
                    logger.warning(f"Could not score {symbol} - insufficient data")
                    fail_count += 1

            except Exception as e:
                logger.error(f"Error scoring {symbol}: {e}")
                fail_count += 1
                continue

        logger.info(
            f"Opportunity scoring completed: "
            f"{success_count} successful, {fail_count} failed"
        )


def main():
    """Main entry point for the job."""
    parser = argparse.ArgumentParser(description='Score opportunities')
    parser.add_argument('--tickers', type=str, help='Comma-separated list of tickers')
    parser.add_argument('--all', action='store_true', help='Score all active tickers')

    args = parser.parse_args()

    # Create database session
    db = SessionLocal()

    try:
        job = ScoringJob(db)

        # Determine which tickers to process
        if args.all:
            tickers = job.get_active_tickers()
            logger.info(f"Scoring all {len(tickers)} active tickers")
        elif args.tickers:
            tickers = [t.strip() for t in args.tickers.split(',')]
        else:
            logger.error("Must specify either --tickers or --all")
            return

        # Run the job
        job.run(tickers)

    except Exception as e:
        logger.error(f"Job failed: {e}", exc_info=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

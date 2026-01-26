#!/usr/bin/env python3
"""
Generate Alerts Job

Generates alerts based on opportunity score changes.
Runs as a Kubernetes pod triggered by Airflow.

Usage:
    python jobs/generate_alerts.py
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from app.database import SessionLocal
from app.models import OpportunityScore, Alert, Ticker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AlertGenerationJob:
    """Job for generating alerts."""

    # Alert thresholds
    HIGH_SCORE_THRESHOLD = 75.0
    SCORE_CHANGE_THRESHOLD = 10.0
    MIN_CONFIDENCE = 70.0

    def __init__(self, db: Session):
        self.db = db

    def get_recent_scores(self, days: int = 2) -> List[OpportunityScore]:
        """Get scores from the last N days."""
        cutoff_date = datetime.now() - timedelta(days=days)

        scores = self.db.query(OpportunityScore).filter(
            OpportunityScore.timestamp >= cutoff_date
        ).order_by(desc(OpportunityScore.timestamp)).all()

        return scores

    def get_previous_score(
        self,
        ticker: str,
        current_timestamp: datetime
    ) -> Optional[OpportunityScore]:
        """Get the previous score for a ticker."""
        previous = self.db.query(OpportunityScore).filter(
            and_(
                OpportunityScore.ticker == ticker,
                OpportunityScore.timestamp < current_timestamp
            )
        ).order_by(desc(OpportunityScore.timestamp)).first()

        return previous

    def create_alert(
        self,
        ticker: str,
        alert_type: str,
        severity: str,
        message: str,
        metadata: dict = None
    ):
        """Create a new alert."""
        alert = Alert(
            ticker=ticker,
            alert_type=alert_type,
            severity=severity,
            message=message,
            metadata=metadata,
            is_read=False
        )

        self.db.add(alert)
        self.db.commit()

        logger.info(f"Created {severity} alert for {ticker}: {alert_type}")

    def check_new_high_score(self, score: OpportunityScore):
        """Check for new high-confidence opportunities."""
        if (
            score.overall_score >= self.HIGH_SCORE_THRESHOLD
            and score.confidence_level >= self.MIN_CONFIDENCE
        ):
            # Check if this is a new entry or significant increase
            previous = self.get_previous_score(score.ticker, score.timestamp)

            if not previous or previous.overall_score < self.HIGH_SCORE_THRESHOLD:
                self.create_alert(
                    ticker=score.ticker,
                    alert_type="NEW_HIGH_SCORE",
                    severity="HIGH",
                    message=f"{score.ticker} has a new high opportunity score of {score.overall_score:.1f} (Confidence: {score.confidence_level:.1f}%)",
                    metadata={
                        "score": float(score.overall_score),
                        "confidence": float(score.confidence_level),
                        "previous_score": float(previous.overall_score) if previous else None
                    }
                )

    def check_significant_change(self, score: OpportunityScore):
        """Check for significant score changes."""
        previous = self.get_previous_score(score.ticker, score.timestamp)

        if previous:
            score_change = abs(score.overall_score - previous.overall_score)

            if score_change >= self.SCORE_CHANGE_THRESHOLD:
                direction = "increased" if score.overall_score > previous.overall_score else "decreased"
                severity = "MEDIUM" if score.overall_score > previous.overall_score else "INFO"

                self.create_alert(
                    ticker=score.ticker,
                    alert_type="SIGNIFICANT_CHANGE",
                    severity=severity,
                    message=f"{score.ticker} score {direction} by {score_change:.1f} points (from {previous.overall_score:.1f} to {score.overall_score:.1f})",
                    metadata={
                        "score": float(score.overall_score),
                        "previous_score": float(previous.overall_score),
                        "change": float(score_change),
                        "direction": direction
                    }
                )

    def run(self):
        """Run the alert generation job."""
        logger.info("Starting alert generation")

        # Get recent scores (last 2 days to catch today's scores)
        recent_scores = self.get_recent_scores(days=2)

        # Group by ticker and get most recent score for each
        ticker_scores = {}
        for score in recent_scores:
            if score.ticker not in ticker_scores:
                ticker_scores[score.ticker] = score

        logger.info(f"Processing {len(ticker_scores)} tickers for alert generation")

        alert_count = 0

        for ticker, score in ticker_scores.items():
            try:
                # Check for new high scores
                self.check_new_high_score(score)

                # Check for significant changes
                self.check_significant_change(score)

                alert_count += 1

            except Exception as e:
                logger.error(f"Error generating alerts for {ticker}: {e}")
                continue

        logger.info(f"Alert generation completed for {alert_count} tickers")


def main():
    """Main entry point for the job."""
    # Create database session
    db = SessionLocal()

    try:
        job = AlertGenerationJob(db)
        job.run()

    except Exception as e:
        logger.error(f"Job failed: {e}", exc_info=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

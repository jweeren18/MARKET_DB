"""
SQLAlchemy models for opportunity scoring and alerts.
"""

from sqlalchemy import (
    Column,
    String,
    DECIMAL,
    Boolean,
    DateTime,
    Text,
    Index,
    PrimaryKeyConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from app.database import Base


class OpportunityScore(Base):
    """
    Opportunity score model - stores 10x scoring results.
    This will be converted to a TimescaleDB hypertable partitioned by timestamp.
    """

    __tablename__ = "opportunity_scores"

    ticker = Column(String(20), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    overall_score = Column(DECIMAL(5, 2), nullable=False)  # 0-100
    confidence_level = Column(DECIMAL(5, 2), nullable=False)  # 0-100
    component_scores = Column(JSONB, nullable=False)  # Breakdown by component
    explanation = Column(JSONB, nullable=False)  # Feature contributions
    bull_case = Column(DECIMAL(5, 2))
    base_case = Column(DECIMAL(5, 2))
    bear_case = Column(DECIMAL(5, 2))

    # Composite primary key
    __table_args__ = (
        PrimaryKeyConstraint("ticker", "timestamp"),
        Index(
            "idx_opportunity_score",
            "timestamp",
            "overall_score",
            postgresql_using="btree"
        ),
    )


class Alert(Base):
    """Alert model - stores dashboard alerts for users."""

    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker = Column(String(20), nullable=False)
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)  # 'INFO', 'MEDIUM', 'HIGH'
    message = Column(Text, nullable=False)
    metadata = Column(JSONB)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Indexes
    __table_args__ = (
        Index("idx_alerts_unread", "created_at", "is_read", postgresql_using="btree"),
    )

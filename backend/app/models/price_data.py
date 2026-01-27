"""
SQLAlchemy models for time-series data (price data and technical indicators).
These tables will be converted to TimescaleDB hypertables.
"""

from sqlalchemy import (
    Column,
    String,
    DECIMAL,
    BigInteger,
    DateTime,
    Index,
    PrimaryKeyConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


class PriceData(Base):
    """
    Price data model - stores OHLCV data for tickers.
    This will be converted to a TimescaleDB hypertable partitioned by timestamp.
    """

    __tablename__ = "price_data"

    ticker = Column(String(20), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    open = Column(DECIMAL(18, 4))
    high = Column(DECIMAL(18, 4))
    low = Column(DECIMAL(18, 4))
    close = Column(DECIMAL(18, 4))
    volume = Column(BigInteger)
    adjusted_close = Column(DECIMAL(18, 4))

    # Composite primary key
    __table_args__ = (
        PrimaryKeyConstraint("ticker", "timestamp"),
        Index("idx_price_ticker_time", "ticker", "timestamp", postgresql_using="btree"),
    )


class TechnicalIndicator(Base):
    """
    Technical indicator model - stores calculated indicators.
    This will be converted to a TimescaleDB hypertable partitioned by timestamp.
    """

    __tablename__ = "technical_indicators"

    ticker = Column(String(20), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    indicator_name = Column(String(50), nullable=False)
    value = Column(DECIMAL(18, 6))
    meta = Column(JSONB)  # Store additional context as JSON

    # Composite primary key
    __table_args__ = (
        PrimaryKeyConstraint("ticker", "timestamp", "indicator_name"),
        Index(
            "idx_indicator_ticker_name",
            "ticker",
            "indicator_name",
            "timestamp",
            postgresql_using="btree"
        ),
    )


class FundamentalMetric(Base):
    """
    Fundamental metrics model - stores fundamental data points.
    This will be converted to a TimescaleDB hypertable partitioned by timestamp.
    """

    __tablename__ = "fundamental_metrics"

    ticker = Column(String(20), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    metric_name = Column(String(50), nullable=False)
    value = Column(DECIMAL(18, 6))
    period = Column(String(20))  # e.g., 'Q1 2024', 'FY 2023'
    source = Column(String(50))

    # Composite primary key
    __table_args__ = (
        PrimaryKeyConstraint("ticker", "timestamp", "metric_name"),
    )

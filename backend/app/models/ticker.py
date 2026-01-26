"""
SQLAlchemy model for ticker information.
"""

from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.sql import func

from app.database import Base


class Ticker(Base):
    """Ticker model - represents a stock, ETF, or other tradeable asset."""

    __tablename__ = "tickers"

    ticker = Column(String(20), primary_key=True)
    name = Column(String(255), nullable=False)
    asset_type = Column(String(20), nullable=False)  # 'STOCK', 'ETF', 'CRYPTO'
    sector = Column(String(100))
    industry = Column(String(100))
    market_cap_category = Column(String(20))  # 'LARGE', 'MID', 'SMALL', 'MICRO'
    exchange = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

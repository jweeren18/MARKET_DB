"""
SQLAlchemy models for portfolio management.
Includes Portfolio, Holdings, and Transactions tables.
"""

from sqlalchemy import (
    Column,
    String,
    Text,
    DECIMAL,
    Date,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class Portfolio(Base):
    """Portfolio model - represents a collection of investments."""

    __tablename__ = "portfolios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    holdings = relationship("Holding", back_populates="portfolio", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="portfolio", cascade="all, delete-orphan")


class Holding(Base):
    """Holding model - represents a position in a portfolio."""

    __tablename__ = "holdings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False)
    ticker = Column(String(20), nullable=False)
    quantity = Column(DECIMAL(18, 8), nullable=False)
    cost_basis = Column(DECIMAL(18, 2), nullable=False)
    purchase_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    portfolio = relationship("Portfolio", back_populates="holdings")

    # Indexes
    __table_args__ = (
        Index("idx_portfolio_ticker", "portfolio_id", "ticker"),
    )


class Transaction(Base):
    """Transaction model - records buy/sell transactions."""

    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False)
    ticker = Column(String(20), nullable=False)
    transaction_type = Column(String(10), nullable=False)  # 'BUY' or 'SELL'
    quantity = Column(DECIMAL(18, 8), nullable=False)
    price = Column(DECIMAL(18, 2), nullable=False)
    transaction_date = Column(DateTime(timezone=True), nullable=False)
    fees = Column(DECIMAL(18, 2), default=0)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    portfolio = relationship("Portfolio", back_populates="transactions")

    # Indexes
    __table_args__ = (
        Index("idx_portfolio_date", "portfolio_id", "transaction_date"),
    )

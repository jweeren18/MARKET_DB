"""
Pydantic schemas for portfolio-related API requests and responses.
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


# Portfolio schemas

class PortfolioBase(BaseModel):
    """Base schema for portfolio with common fields."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class PortfolioCreate(PortfolioBase):
    """Schema for creating a new portfolio."""
    pass


class PortfolioUpdate(PortfolioBase):
    """Schema for updating an existing portfolio."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)


class PortfolioResponse(PortfolioBase):
    """Schema for portfolio response."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Holding schemas

class HoldingBase(BaseModel):
    """Base schema for holding with common fields."""
    ticker: str = Field(..., min_length=1, max_length=20)
    quantity: Decimal = Field(..., gt=0)
    cost_basis: Decimal = Field(..., gt=0)
    purchase_date: date


class HoldingCreate(HoldingBase):
    """Schema for creating a new holding."""
    pass


class HoldingUpdate(BaseModel):
    """Schema for updating an existing holding."""
    quantity: Optional[Decimal] = Field(None, gt=0)
    cost_basis: Optional[Decimal] = Field(None, gt=0)
    purchase_date: Optional[date] = None


class HoldingResponse(HoldingBase):
    """Schema for holding response."""
    id: UUID
    portfolio_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Transaction schemas

class TransactionBase(BaseModel):
    """Base schema for transaction with common fields."""
    ticker: str = Field(..., min_length=1, max_length=20)
    transaction_type: str = Field(..., pattern="^(BUY|SELL)$")
    quantity: Decimal = Field(..., gt=0)
    price: Decimal = Field(..., gt=0)
    transaction_date: datetime
    fees: Optional[Decimal] = Field(default=0, ge=0)
    notes: Optional[str] = None


class TransactionCreate(TransactionBase):
    """Schema for creating a new transaction."""
    pass


class TransactionResponse(TransactionBase):
    """Schema for transaction response."""
    id: UUID
    portfolio_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# List response schemas

class PortfolioListResponse(BaseModel):
    """Schema for list of portfolios."""
    portfolios: list[PortfolioResponse]
    total: int


class HoldingListResponse(BaseModel):
    """Schema for list of holdings."""
    holdings: list[HoldingResponse]
    total: int


class TransactionListResponse(BaseModel):
    """Schema for list of transactions."""
    transactions: list[TransactionResponse]
    total: int

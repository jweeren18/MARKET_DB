"""
API routes for portfolio management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.services.portfolio_service import PortfolioService
from app.schemas.portfolio import (
    PortfolioResponse,
    PortfolioCreate,
    PortfolioUpdate,
    PortfolioListResponse,
    HoldingResponse,
    HoldingCreate,
    HoldingUpdate,
    HoldingListResponse,
    TransactionResponse,
    TransactionCreate,
    TransactionListResponse,
)

router = APIRouter()

# Portfolio endpoints


@router.get("", response_model=PortfolioListResponse)
def list_portfolios(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    """List all portfolios with pagination."""
    portfolios = PortfolioService.get_portfolios(db, skip=skip, limit=limit)
    return PortfolioListResponse(portfolios=portfolios, total=len(portfolios))


@router.post("", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
def create_portfolio(portfolio: PortfolioCreate, db: Session = Depends(get_db)):
    """Create a new portfolio."""
    return PortfolioService.create_portfolio(db, portfolio)


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
def get_portfolio(portfolio_id: UUID, db: Session = Depends(get_db)):
    """Get a specific portfolio by ID."""
    portfolio = PortfolioService.get_portfolio(db, portfolio_id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found"
        )
    return portfolio


@router.put("/{portfolio_id}", response_model=PortfolioResponse)
def update_portfolio(
    portfolio_id: UUID, portfolio: PortfolioUpdate, db: Session = Depends(get_db)
):
    """Update an existing portfolio."""
    updated_portfolio = PortfolioService.update_portfolio(db, portfolio_id, portfolio)
    if not updated_portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found"
        )
    return updated_portfolio


@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio(portfolio_id: UUID, db: Session = Depends(get_db)):
    """Delete a portfolio."""
    success = PortfolioService.delete_portfolio(db, portfolio_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found"
        )


# Holdings endpoints


@router.get("/{portfolio_id}/holdings", response_model=HoldingListResponse)
def list_holdings(portfolio_id: UUID, db: Session = Depends(get_db)):
    """Get all holdings for a portfolio."""
    # Verify portfolio exists
    portfolio = PortfolioService.get_portfolio(db, portfolio_id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found"
        )

    holdings = PortfolioService.get_holdings(db, portfolio_id)
    return HoldingListResponse(holdings=holdings, total=len(holdings))


@router.post(
    "/{portfolio_id}/holdings",
    response_model=HoldingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_holding(
    portfolio_id: UUID, holding: HoldingCreate, db: Session = Depends(get_db)
):
    """Add a new holding to a portfolio."""
    # Verify portfolio exists
    portfolio = PortfolioService.get_portfolio(db, portfolio_id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found"
        )

    return PortfolioService.create_holding(db, portfolio_id, holding)


@router.put("/holdings/{holding_id}", response_model=HoldingResponse)
def update_holding(
    holding_id: UUID, holding: HoldingUpdate, db: Session = Depends(get_db)
):
    """Update an existing holding."""
    updated_holding = PortfolioService.update_holding(db, holding_id, holding)
    if not updated_holding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Holding not found"
        )
    return updated_holding


@router.delete("/holdings/{holding_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_holding(holding_id: UUID, db: Session = Depends(get_db)):
    """Delete a holding."""
    success = PortfolioService.delete_holding(db, holding_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Holding not found"
        )


# Transaction endpoints


@router.get("/{portfolio_id}/transactions", response_model=TransactionListResponse)
def list_transactions(portfolio_id: UUID, db: Session = Depends(get_db)):
    """Get all transactions for a portfolio."""
    # Verify portfolio exists
    portfolio = PortfolioService.get_portfolio(db, portfolio_id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found"
        )

    transactions = PortfolioService.get_transactions(db, portfolio_id)
    return TransactionListResponse(transactions=transactions, total=len(transactions))


@router.post(
    "/{portfolio_id}/transactions",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_transaction(
    portfolio_id: UUID, transaction: TransactionCreate, db: Session = Depends(get_db)
):
    """Add a new transaction to a portfolio."""
    # Verify portfolio exists
    portfolio = PortfolioService.get_portfolio(db, portfolio_id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found"
        )

    return PortfolioService.create_transaction(db, portfolio_id, transaction)

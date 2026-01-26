"""
Portfolio service - business logic for portfolio management.
Handles CRUD operations for portfolios, holdings, and transactions.
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.models import Portfolio, Holding, Transaction
from app.schemas.portfolio import (
    PortfolioCreate,
    PortfolioUpdate,
    HoldingCreate,
    HoldingUpdate,
    TransactionCreate,
)


class PortfolioService:
    """Service class for portfolio operations."""

    @staticmethod
    def get_portfolios(db: Session, skip: int = 0, limit: int = 100) -> List[Portfolio]:
        """Get all portfolios with pagination."""
        return db.query(Portfolio).offset(skip).limit(limit).all()

    @staticmethod
    def get_portfolio(db: Session, portfolio_id: UUID) -> Optional[Portfolio]:
        """Get a single portfolio by ID."""
        return db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()

    @staticmethod
    def create_portfolio(db: Session, portfolio: PortfolioCreate) -> Portfolio:
        """Create a new portfolio."""
        db_portfolio = Portfolio(**portfolio.model_dump())
        db.add(db_portfolio)
        db.commit()
        db.refresh(db_portfolio)
        return db_portfolio

    @staticmethod
    def update_portfolio(
        db: Session, portfolio_id: UUID, portfolio: PortfolioUpdate
    ) -> Optional[Portfolio]:
        """Update an existing portfolio."""
        db_portfolio = PortfolioService.get_portfolio(db, portfolio_id)
        if not db_portfolio:
            return None

        update_data = portfolio.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_portfolio, field, value)

        db.commit()
        db.refresh(db_portfolio)
        return db_portfolio

    @staticmethod
    def delete_portfolio(db: Session, portfolio_id: UUID) -> bool:
        """Delete a portfolio."""
        db_portfolio = PortfolioService.get_portfolio(db, portfolio_id)
        if not db_portfolio:
            return False

        db.delete(db_portfolio)
        db.commit()
        return True

    # Holdings methods

    @staticmethod
    def get_holdings(db: Session, portfolio_id: UUID) -> List[Holding]:
        """Get all holdings for a portfolio."""
        return db.query(Holding).filter(Holding.portfolio_id == portfolio_id).all()

    @staticmethod
    def get_holding(db: Session, holding_id: UUID) -> Optional[Holding]:
        """Get a single holding by ID."""
        return db.query(Holding).filter(Holding.id == holding_id).first()

    @staticmethod
    def create_holding(
        db: Session, portfolio_id: UUID, holding: HoldingCreate
    ) -> Holding:
        """Create a new holding."""
        db_holding = Holding(portfolio_id=portfolio_id, **holding.model_dump())
        db.add(db_holding)
        db.commit()
        db.refresh(db_holding)
        return db_holding

    @staticmethod
    def update_holding(
        db: Session, holding_id: UUID, holding: HoldingUpdate
    ) -> Optional[Holding]:
        """Update an existing holding."""
        db_holding = PortfolioService.get_holding(db, holding_id)
        if not db_holding:
            return None

        update_data = holding.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_holding, field, value)

        db.commit()
        db.refresh(db_holding)
        return db_holding

    @staticmethod
    def delete_holding(db: Session, holding_id: UUID) -> bool:
        """Delete a holding."""
        db_holding = PortfolioService.get_holding(db, holding_id)
        if not db_holding:
            return False

        db.delete(db_holding)
        db.commit()
        return True

    # Transaction methods

    @staticmethod
    def get_transactions(db: Session, portfolio_id: UUID) -> List[Transaction]:
        """Get all transactions for a portfolio."""
        return (
            db.query(Transaction)
            .filter(Transaction.portfolio_id == portfolio_id)
            .order_by(Transaction.transaction_date.desc())
            .all()
        )

    @staticmethod
    def create_transaction(
        db: Session, portfolio_id: UUID, transaction: TransactionCreate
    ) -> Transaction:
        """Create a new transaction."""
        db_transaction = Transaction(
            portfolio_id=portfolio_id, **transaction.model_dump()
        )
        db.add(db_transaction)
        db.commit()
        db.refresh(db_transaction)
        return db_transaction

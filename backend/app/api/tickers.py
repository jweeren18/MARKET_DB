"""
Tickers/Market Data API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
from datetime import datetime, timedelta

from app.database import get_db
from app.models import Ticker, PriceData

router = APIRouter(prefix="/api/tickers", tags=["tickers"])


@router.get("")
def list_tickers(
    search: Optional[str] = Query(None, description="Search by ticker or name"),
    asset_type: Optional[str] = Query(None, description="Filter by asset type"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    is_active: bool = Query(True, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=500, description="Maximum results to return"),
    db: Session = Depends(get_db)
):
    """
    List/search tickers with filtering.

    Returns ticker information including symbol, name, sector, market cap, etc.
    """
    try:
        query = db.query(Ticker)

        # Apply filters
        if is_active is not None:
            query = query.filter(Ticker.is_active == is_active)

        if asset_type:
            query = query.filter(Ticker.asset_type == asset_type)

        if sector:
            query = query.filter(Ticker.sector == sector)

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Ticker.ticker.ilike(search_pattern),
                    Ticker.name.ilike(search_pattern)
                )
            )

        # Order by ticker symbol
        query = query.order_by(Ticker.ticker)

        # Apply limit
        tickers = query.limit(limit).all()

        return {
            "tickers": [
                {
                    "ticker": t.ticker,
                    "name": t.name,
                    "asset_type": t.asset_type,
                    "sector": t.sector,
                    "industry": t.industry,
                    "market_cap_category": t.market_cap_category,
                    "exchange": t.exchange,
                    "is_active": t.is_active
                }
                for t in tickers
            ],
            "count": len(tickers)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch tickers: {str(e)}")


@router.get("/{symbol}")
def get_ticker(
    symbol: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information for a specific ticker.
    """
    try:
        ticker = db.query(Ticker).filter(Ticker.ticker == symbol.upper()).first()

        if not ticker:
            raise HTTPException(status_code=404, detail=f"Ticker {symbol} not found")

        return {
            "ticker": ticker.ticker,
            "name": ticker.name,
            "asset_type": ticker.asset_type,
            "sector": ticker.sector,
            "industry": ticker.industry,
            "market_cap_category": ticker.market_cap_category,
            "exchange": ticker.exchange,
            "is_active": ticker.is_active,
            "created_at": ticker.created_at,
            "updated_at": ticker.updated_at
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch ticker: {str(e)}")


@router.get("/{symbol}/price")
def get_current_price(
    symbol: str,
    db: Session = Depends(get_db)
):
    """
    Get the most recent price for a ticker.
    """
    try:
        # Get most recent price data
        price = db.query(PriceData).filter(
            PriceData.ticker == symbol.upper()
        ).order_by(PriceData.timestamp.desc()).first()

        if not price:
            raise HTTPException(status_code=404, detail=f"No price data found for {symbol}")

        return {
            "ticker": price.ticker,
            "timestamp": price.timestamp,
            "open": float(price.open) if price.open else None,
            "high": float(price.high) if price.high else None,
            "low": float(price.low) if price.low else None,
            "close": float(price.close) if price.close else None,
            "volume": int(price.volume) if price.volume else None,
            "adjusted_close": float(price.adjusted_close) if price.adjusted_close else None
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch price: {str(e)}")


@router.get("/{symbol}/history")
def get_price_history(
    symbol: str,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    days: Optional[int] = Query(None, ge=1, le=730, description="Number of days to fetch (alternative to start_date)"),
    interval: str = Query("daily", description="Data interval (only 'daily' supported)"),
    db: Session = Depends(get_db)
):
    """
    Get historical price data for a ticker.

    You can specify either:
    - start_date and end_date (YYYY-MM-DD format)
    - days (number of days from today)
    """
    try:
        query = db.query(PriceData).filter(PriceData.ticker == symbol.upper())

        # Handle date filtering
        if days:
            # Get last N days
            cutoff_date = datetime.now() - timedelta(days=days)
            query = query.filter(PriceData.timestamp >= cutoff_date)
        elif start_date:
            # Parse start date
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(PriceData.timestamp >= start_dt)

            if end_date:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                query = query.filter(PriceData.timestamp <= end_dt)

        # Order by date ascending
        query = query.order_by(PriceData.timestamp)

        prices = query.all()

        if not prices:
            raise HTTPException(status_code=404, detail=f"No price data found for {symbol}")

        return {
            "ticker": symbol.upper(),
            "count": len(prices),
            "history": [
                {
                    "timestamp": p.timestamp.isoformat(),
                    "open": float(p.open) if p.open else None,
                    "high": float(p.high) if p.high else None,
                    "low": float(p.low) if p.low else None,
                    "close": float(p.close) if p.close else None,
                    "volume": int(p.volume) if p.volume else None,
                    "adjusted_close": float(p.adjusted_close) if p.adjusted_close else None
                }
                for p in prices
            ]
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch price history: {str(e)}")

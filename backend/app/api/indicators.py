"""
Technical Indicators API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta

from app.database import get_db
from app.services.signal_engine import SignalEngine

router = APIRouter(prefix="/api/indicators", tags=["indicators"])


@router.get("/tickers/{ticker}/latest")
def get_latest_indicators(
    ticker: str,
    db: Session = Depends(get_db)
):
    """
    Get the most recent indicator values for a ticker.

    Returns all calculated indicators as of the latest date.
    """
    signal_engine = SignalEngine(db)

    try:
        indicators = signal_engine.get_latest_indicators(ticker)

        if not indicators:
            raise HTTPException(
                status_code=404,
                detail=f"No indicators found for ticker {ticker}"
            )

        return {
            "ticker": ticker,
            "indicators": indicators,
            "count": len(indicators)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch indicators: {str(e)}")


@router.get("/tickers/{ticker}/history")
def get_indicator_history(
    ticker: str,
    indicator_name: Optional[str] = Query(None, description="Indicator name (e.g., 'rsi_14', 'macd'). If not provided, returns all indicators."),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date (default: today)"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    db: Session = Depends(get_db)
):
    """
    Get historical values for indicator(s).

    If indicator_name is provided, returns history for that specific indicator.
    If not provided, returns history for all indicators.
    """
    signal_engine = SignalEngine(db)

    try:
        if indicator_name:
            # Get specific indicator history
            history = signal_engine.get_indicator_history(
                ticker=ticker,
                indicator_name=indicator_name,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )

            if not history:
                raise HTTPException(
                    status_code=404,
                    detail=f"No history found for {ticker}/{indicator_name}"
                )

            return {
                "ticker": ticker,
                "indicator_name": indicator_name,
                "data_points": len(history),
                "history": history
            }
        else:
            # Get all indicators history
            from app.models import TechnicalIndicator
            from sqlalchemy import desc

            query = db.query(TechnicalIndicator).filter(
                TechnicalIndicator.ticker == ticker
            )

            if start_date:
                query = query.filter(TechnicalIndicator.timestamp >= start_date)
            if end_date:
                query = query.filter(TechnicalIndicator.timestamp <= end_date)

            query = query.order_by(desc(TechnicalIndicator.timestamp))

            # Only apply limit if no date filters are specified
            # When date filters are provided, they already limit the data effectively
            if not start_date and not end_date:
                query = query.limit(limit * 20)  # Allow more records for multiple indicators

            results = query.all()

            if not results:
                raise HTTPException(
                    status_code=404,
                    detail=f"No indicator history found for {ticker}"
                )

            # Group by indicator name
            history_by_indicator = {}
            for record in results:
                if record.indicator_name not in history_by_indicator:
                    history_by_indicator[record.indicator_name] = []
                history_by_indicator[record.indicator_name].append({
                    "timestamp": record.timestamp,
                    "value": float(record.value) if record.value else None,
                    "meta": record.meta
                })

            return {
                "ticker": ticker,
                "indicator_names": list(history_by_indicator.keys()),
                "data_points": len(results),
                "history": history_by_indicator
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch indicator history: {str(e)}")


@router.get("/tickers/{ticker}/summary")
def get_indicator_summary(
    ticker: str,
    db: Session = Depends(get_db)
):
    """
    Get a summary of available indicators for a ticker.

    Returns metadata about which indicators are available and their data ranges.
    """
    signal_engine = SignalEngine(db)

    try:
        summary = signal_engine.get_indicator_summary(ticker)

        if summary["total_indicators"] == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No indicators found for ticker {ticker}"
            )

        return summary

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch indicator summary: {str(e)}")


@router.get("/tickers/{ticker}/signals")
def detect_signals(
    ticker: str,
    db: Session = Depends(get_db)
):
    """
    Detect trading signals based on technical indicators.

    Analyzes current indicator values and returns actionable signals
    (oversold/overbought, bullish/bearish, trending, etc.)
    """
    signal_engine = SignalEngine(db)

    try:
        signals = signal_engine.detect_signals(ticker)

        return signals

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to detect signals: {str(e)}")


@router.post("/calculate")
def calculate_indicators(
    tickers: Optional[List[str]] = Query(None, description="List of tickers (if not provided, calculates for all)"),
    lookback_days: int = Query(252, ge=30, le=1000, description="Days of historical data to use"),
    force: bool = Query(False, description="Force recalculation even if already calculated today"),
    db: Session = Depends(get_db)
):
    """
    Manually trigger indicator calculation for specific tickers or all tickers.

    This endpoint is useful for:
    - Recalculating indicators after data updates
    - Forcing calculation even if already done today
    - Calculating indicators for new tickers

    Returns a summary of the calculation results.
    """
    signal_engine = SignalEngine(db)

    try:
        if tickers:
            # Calculate for specific tickers
            results = {
                "total_tickers": len(tickers),
                "successful": 0,
                "skipped": 0,
                "failed": 0,
                "details": []
            }

            for ticker in tickers:
                result = signal_engine.calculate_indicators_for_ticker(
                    ticker=ticker,
                    lookback_days=lookback_days,
                    force_recalculate=force
                )

                if result["status"] == "success":
                    results["successful"] += 1
                elif result["status"] == "skipped":
                    results["skipped"] += 1
                else:
                    results["failed"] += 1

                results["details"].append({
                    "ticker": ticker,
                    "status": result["status"],
                    "reason": result.get("reason"),
                    "indicators_count": len(result.get("indicators_calculated", []))
                })

            return results

        else:
            # Calculate for all active tickers
            results = signal_engine.calculate_indicators_for_all_tickers(
                lookback_days=lookback_days,
                force_recalculate=force
            )

            return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate indicators: {str(e)}")


@router.get("/tickers/{ticker}/date/{date}")
def get_indicators_for_date(
    ticker: str,
    date: str = Path(..., description="Date in YYYY-MM-DD format"),
    db: Session = Depends(get_db)
):
    """
    Get all indicator values for a specific date.

    Useful for historical analysis and backtesting.
    """
    signal_engine = SignalEngine(db)

    try:
        # Parse date
        target_date = datetime.strptime(date, "%Y-%m-%d")

        indicators = signal_engine.get_indicators_for_date(ticker, target_date)

        if not indicators:
            raise HTTPException(
                status_code=404,
                detail=f"No indicators found for {ticker} on {date}"
            )

        return {
            "ticker": ticker,
            "date": date,
            "indicators": indicators,
            "count": len(indicators)
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch indicators: {str(e)}")


@router.get("/available")
def get_available_indicators():
    """
    Get a list of all available indicator types.

    Returns indicator names, descriptions, and typical use cases.
    """
    indicators = {
        "moving_averages": {
            "indicators": ["sma_20", "sma_50", "sma_200", "ema_12", "ema_26"],
            "description": "Simple and Exponential Moving Averages",
            "use_case": "Trend identification and support/resistance levels"
        },
        "momentum": {
            "indicators": ["rsi_14", "macd", "macd_signal", "macd_histogram", "roc_12"],
            "description": "Momentum and oscillator indicators",
            "use_case": "Identify overbought/oversold conditions and momentum shifts"
        },
        "volatility": {
            "indicators": ["bb_upper", "bb_middle", "bb_lower", "atr_14"],
            "description": "Volatility and price bands",
            "use_case": "Measure price volatility and identify breakouts"
        },
        "volume": {
            "indicators": ["volume_sma_20", "volume_spike", "obv"],
            "description": "Volume-based indicators",
            "use_case": "Confirm price movements and detect accumulation/distribution"
        },
        "trend": {
            "indicators": ["adx_14", "williams_r", "golden_cross", "death_cross"],
            "description": "Trend strength and direction indicators",
            "use_case": "Identify trend strength and major trend changes"
        },
        "stochastic": {
            "indicators": ["stochastic_k", "stochastic_d"],
            "description": "Stochastic oscillator",
            "use_case": "Identify overbought/oversold conditions"
        }
    }

    return {
        "categories": indicators,
        "total_indicator_types": sum(len(cat["indicators"]) for cat in indicators.values())
    }

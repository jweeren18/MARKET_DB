"""
Opportunities API endpoints - 10x Investment Opportunity Scoring.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import Optional, List
from datetime import datetime, timedelta

from app.database import get_db
from app.services.opportunity_scorer import OpportunityScorer
from app.models import OpportunityScore

router = APIRouter(prefix="/api/opportunities", tags=["opportunities"])


@router.get("")
def list_opportunities(
    min_score: float = Query(0, ge=0, le=100, description="Minimum opportunity score"),
    min_confidence: float = Query(0, ge=0, le=100, description="Minimum confidence level"),
    limit: int = Query(50, ge=1, le=500, description="Maximum results to return"),
    sort_by: str = Query("score", description="Sort by: score, confidence, ticker"),
    db: Session = Depends(get_db)
):
    """
    List all scored opportunities with filtering and sorting.

    Returns the most recent scores for all tickers meeting the criteria.
    """
    try:
        # Get latest scores for each ticker
        subquery = db.query(
            OpportunityScore.ticker,
            func.max(OpportunityScore.timestamp).label('max_timestamp')
        ).group_by(OpportunityScore.ticker).subquery()

        query = db.query(OpportunityScore).join(
            subquery,
            (OpportunityScore.ticker == subquery.c.ticker) &
            (OpportunityScore.timestamp == subquery.c.max_timestamp)
        )

        # Apply filters
        query = query.filter(OpportunityScore.overall_score >= min_score)
        query = query.filter(OpportunityScore.confidence_level >= min_confidence)

        # Apply sorting
        if sort_by == "score":
            query = query.order_by(desc(OpportunityScore.overall_score))
        elif sort_by == "confidence":
            query = query.order_by(desc(OpportunityScore.confidence_level))
        else:  # ticker
            query = query.order_by(OpportunityScore.ticker)

        # Apply limit
        opportunities = query.limit(limit).all()

        return {
            "opportunities": [
                {
                    "ticker": opp.ticker,
                    "score": float(opp.overall_score),
                    "confidence": float(opp.confidence_level),
                    "timestamp": opp.timestamp,
                    "bull_case": float(opp.bull_case) if opp.bull_case else None,
                    "base_case": float(opp.base_case) if opp.base_case else None,
                    "bear_case": float(opp.bear_case) if opp.bear_case else None,
                }
                for opp in opportunities
            ],
            "count": len(opportunities),
            "filters": {
                "min_score": min_score,
                "min_confidence": min_confidence,
                "limit": limit,
                "sort_by": sort_by
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch opportunities: {str(e)}")


@router.get("/{ticker}")
def get_opportunity(
    ticker: str,
    include_history: bool = Query(False, description="Include historical scores"),
    history_days: int = Query(30, ge=1, le=365, description="Days of history to include"),
    db: Session = Depends(get_db)
):
    """
    Get detailed opportunity score for a specific ticker.

    Includes full explainability, component breakdown, scenarios, and drivers/risks.
    """
    try:
        # Get latest score
        latest_score = db.query(OpportunityScore).filter(
            OpportunityScore.ticker == ticker
        ).order_by(desc(OpportunityScore.timestamp)).first()

        if not latest_score:
            raise HTTPException(
                status_code=404,
                detail=f"No opportunity score found for ticker {ticker}"
            )

        response = {
            "ticker": latest_score.ticker,
            "score": float(latest_score.overall_score),
            "confidence": float(latest_score.confidence_level),
            "timestamp": latest_score.timestamp,
            "scenarios": {
                "bull": float(latest_score.bull_case) if latest_score.bull_case else None,
                "base": float(latest_score.base_case) if latest_score.base_case else None,
                "bear": float(latest_score.bear_case) if latest_score.bear_case else None,
            },
            "components": latest_score.component_scores,
            "explanation": latest_score.explanation,
        }

        # Include history if requested
        if include_history:
            cutoff_date = datetime.now() - timedelta(days=history_days)
            historical_scores = db.query(OpportunityScore).filter(
                OpportunityScore.ticker == ticker,
                OpportunityScore.timestamp >= cutoff_date
            ).order_by(desc(OpportunityScore.timestamp)).all()

            response["history"] = [
                {
                    "timestamp": score.timestamp,
                    "score": float(score.overall_score),
                    "confidence": float(score.confidence_level)
                }
                for score in historical_scores
            ]

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch opportunity: {str(e)}")


@router.get("/{ticker}/components")
def get_opportunity_components(
    ticker: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed component breakdown for a ticker's opportunity score.

    Returns each scoring component with its contribution and details.
    """
    try:
        latest_score = db.query(OpportunityScore).filter(
            OpportunityScore.ticker == ticker
        ).order_by(desc(OpportunityScore.timestamp)).first()

        if not latest_score:
            raise HTTPException(
                status_code=404,
                detail=f"No opportunity score found for ticker {ticker}"
            )

        return {
            "ticker": latest_score.ticker,
            "overall_score": float(latest_score.overall_score),
            "timestamp": latest_score.timestamp,
            "components": latest_score.component_scores
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch components: {str(e)}")


@router.get("/{ticker}/explainability")
def get_opportunity_explainability(
    ticker: str,
    db: Session = Depends(get_db)
):
    """
    Get full explainability for a ticker's opportunity score.

    Returns key drivers, risks, and detailed reasoning for the score.
    """
    try:
        latest_score = db.query(OpportunityScore).filter(
            OpportunityScore.ticker == ticker
        ).order_by(desc(OpportunityScore.timestamp)).first()

        if not latest_score:
            raise HTTPException(
                status_code=404,
                detail=f"No opportunity score found for ticker {ticker}"
            )

        explanation = latest_score.explanation or {}

        return {
            "ticker": latest_score.ticker,
            "score": float(latest_score.overall_score),
            "confidence": float(latest_score.confidence_level),
            "timestamp": latest_score.timestamp,
            "key_drivers": explanation.get("key_drivers", []),
            "risks": explanation.get("risks", []),
            "components": explanation.get("components", {}),
            "scenarios": explanation.get("scenarios", {})
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch explainability: {str(e)}")


@router.post("/calculate")
def calculate_opportunities(
    tickers: Optional[List[str]] = Query(None, description="List of tickers to score (if not provided, scores all)"),
    benchmark: str = Query("SPY", description="Benchmark ticker for relative strength"),
    min_confidence: float = Query(0.0, ge=0, le=100, description="Minimum confidence to include"),
    db: Session = Depends(get_db)
):
    """
    Manually trigger opportunity scoring for specific tickers or all tickers.

    This endpoint is useful for:
    - Recalculating scores after data updates
    - Getting fresh scores on-demand
    - Scoring new tickers

    Returns a summary of the scoring results.
    """
    try:
        scorer = OpportunityScorer(db)

        if tickers:
            # Score specific tickers
            results = {
                "total_tickers": len(tickers),
                "scored": 0,
                "skipped": 0,
                "details": []
            }

            for ticker in tickers:
                result = scorer.score_ticker(ticker, benchmark_ticker=benchmark)

                if "error" not in result and result.get("confidence", 0) >= min_confidence:
                    results["scored"] += 1
                    results["details"].append({
                        "ticker": ticker,
                        "score": result["overall_score"],
                        "confidence": result["confidence"]
                    })
                else:
                    results["skipped"] += 1
                    results["details"].append({
                        "ticker": ticker,
                        "error": result.get("message", "Low confidence or insufficient data")
                    })

            return results

        else:
            # Score all active tickers
            results = scorer.score_all_tickers(
                min_confidence=min_confidence,
                benchmark_ticker=benchmark
            )

            return {
                "total_tickers": results["total_tickers"],
                "scored": results["scored"],
                "skipped": results["skipped"],
                "top_opportunities": results["scores"][:10],  # Top 10
                "errors": results.get("errors", [])
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate opportunities: {str(e)}")


@router.get("/history/{ticker}")
def get_opportunity_history(
    ticker: str,
    days: int = Query(30, ge=1, le=365, description="Days of history to retrieve"),
    db: Session = Depends(get_db)
):
    """
    Get historical opportunity scores for a ticker.

    Useful for tracking how a ticker's opportunity rating has changed over time.
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=days)

        scores = db.query(OpportunityScore).filter(
            OpportunityScore.ticker == ticker,
            OpportunityScore.timestamp >= cutoff_date
        ).order_by(OpportunityScore.timestamp).all()

        if not scores:
            raise HTTPException(
                status_code=404,
                detail=f"No historical scores found for ticker {ticker}"
            )

        return {
            "ticker": ticker,
            "period_days": days,
            "data_points": len(scores),
            "history": [
                {
                    "timestamp": score.timestamp,
                    "score": float(score.overall_score),
                    "confidence": float(score.confidence_level),
                    "bull_case": float(score.bull_case) if score.bull_case else None,
                    "base_case": float(score.base_case) if score.base_case else None,
                    "bear_case": float(score.bear_case) if score.bear_case else None,
                }
                for score in scores
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {str(e)}")


@router.get("/top/{category}")
def get_top_opportunities(
    category: str,
    limit: int = Query(10, ge=1, le=100, description="Number of results to return"),
    min_confidence: float = Query(50.0, ge=0, le=100, description="Minimum confidence level"),
    db: Session = Depends(get_db)
):
    """
    Get top opportunities by category.

    Categories:
    - highest_score: Top scores overall
    - highest_confidence: Most confident scores
    - best_bull_case: Best bull case scenarios
    - momentum: Best momentum component scores
    - growth: Best growth acceleration scores
    """
    try:
        # Get latest scores for each ticker
        subquery = db.query(
            OpportunityScore.ticker,
            func.max(OpportunityScore.timestamp).label('max_timestamp')
        ).group_by(OpportunityScore.ticker).subquery()

        query = db.query(OpportunityScore).join(
            subquery,
            (OpportunityScore.ticker == subquery.c.ticker) &
            (OpportunityScore.timestamp == subquery.c.max_timestamp)
        ).filter(OpportunityScore.confidence_level >= min_confidence)

        # Apply category-specific sorting
        if category == "highest_score":
            query = query.order_by(desc(OpportunityScore.overall_score))
        elif category == "highest_confidence":
            query = query.order_by(desc(OpportunityScore.confidence_level))
        elif category == "best_bull_case":
            query = query.order_by(desc(OpportunityScore.bull_case))
        elif category in ["momentum", "growth"]:
            # For component-specific categories, we'd need to parse the JSON
            # For now, just return by overall score
            query = query.order_by(desc(OpportunityScore.overall_score))
        else:
            raise HTTPException(status_code=400, detail=f"Invalid category: {category}")

        opportunities = query.limit(limit).all()

        return {
            "category": category,
            "min_confidence": min_confidence,
            "count": len(opportunities),
            "opportunities": [
                {
                    "ticker": opp.ticker,
                    "score": float(opp.overall_score),
                    "confidence": float(opp.confidence_level),
                    "bull_case": float(opp.bull_case) if opp.bull_case else None,
                    "timestamp": opp.timestamp
                }
                for opp in opportunities
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch top opportunities: {str(e)}")

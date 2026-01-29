"""
Opportunity Scorer Service - 10x Investment Opportunity Identification

Implements rule-based scoring algorithm with full explainability.

Scoring Components (Weighted):
1. Momentum Score (25%): Price trends, volume, technical signals
2. Valuation Divergence (20%): Price vs historical averages (fundamentals deferred)
3. Growth Acceleration (25%): Price momentum and trend strength
4. Relative Strength (15%): Performance vs market benchmark
5. Sector Momentum (15%): Sector relative performance

Returns scores 0-100 with:
- Component breakdowns
- Confidence levels
- Bull/Base/Bear scenarios
- Full explainability (why this score)
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import logging
import numpy as np

from app.models import PriceData, TechnicalIndicator, Ticker, OpportunityScore
from app.services.signal_engine import SignalEngine

logger = logging.getLogger(__name__)


class OpportunityScorer:
    """Service class for scoring investment opportunities."""

    # Scoring weights
    WEIGHTS = {
        "momentum": 0.25,
        "valuation_divergence": 0.20,
        "growth_acceleration": 0.25,
        "relative_strength": 0.15,
        "sector_momentum": 0.15
    }

    def __init__(self, db: Session):
        self.db = db
        self.signal_engine = SignalEngine(db)

    # ==================== Main Scoring Method ====================

    def score_ticker(
        self,
        ticker: str,
        benchmark_ticker: str = "SPY"
    ) -> Dict[str, Any]:
        """
        Calculate opportunity score for a ticker with full explainability.

        Args:
            ticker: Stock ticker symbol
            benchmark_ticker: Market benchmark for comparison (default: SPY)

        Returns:
            Dictionary with score, confidence, components, scenarios, and explainability
        """
        logger.info(f"Scoring opportunity for {ticker}")

        # Get required data
        indicators = self.signal_engine.get_latest_indicators(ticker)
        price_data = self._get_recent_price_data(ticker, days=252)
        benchmark_data = self._get_recent_price_data(benchmark_ticker, days=252)

        if not indicators or len(price_data) < 50:
            return self._insufficient_data_response(ticker)

        # Calculate each component
        momentum_score, momentum_details = self._calculate_momentum_score(
            ticker, indicators, price_data
        )

        valuation_score, valuation_details = self._calculate_valuation_divergence(
            ticker, indicators, price_data
        )

        growth_score, growth_details = self._calculate_growth_acceleration(
            ticker, indicators, price_data
        )

        relative_score, relative_details = self._calculate_relative_strength(
            ticker, price_data, benchmark_data
        )

        sector_score, sector_details = self._calculate_sector_momentum(
            ticker, price_data
        )

        # Calculate overall score
        overall_score = (
            momentum_score * self.WEIGHTS["momentum"] +
            valuation_score * self.WEIGHTS["valuation_divergence"] +
            growth_score * self.WEIGHTS["growth_acceleration"] +
            relative_score * self.WEIGHTS["relative_strength"] +
            sector_score * self.WEIGHTS["sector_momentum"]
        )

        # Calculate confidence
        confidence = self._calculate_confidence(
            indicators, price_data, [
                momentum_details, valuation_details, growth_details,
                relative_details, sector_details
            ]
        )

        # Build component breakdown
        components = {
            "momentum": {
                "score": round(momentum_score, 2),
                "weight": self.WEIGHTS["momentum"],
                "contribution": round(momentum_score * self.WEIGHTS["momentum"], 2),
                "details": momentum_details
            },
            "valuation_divergence": {
                "score": round(valuation_score, 2),
                "weight": self.WEIGHTS["valuation_divergence"],
                "contribution": round(valuation_score * self.WEIGHTS["valuation_divergence"], 2),
                "details": valuation_details
            },
            "growth_acceleration": {
                "score": round(growth_score, 2),
                "weight": self.WEIGHTS["growth_acceleration"],
                "contribution": round(growth_score * self.WEIGHTS["growth_acceleration"], 2),
                "details": growth_details
            },
            "relative_strength": {
                "score": round(relative_score, 2),
                "weight": self.WEIGHTS["relative_strength"],
                "contribution": round(relative_score * self.WEIGHTS["relative_strength"], 2),
                "details": relative_details
            },
            "sector_momentum": {
                "score": round(sector_score, 2),
                "weight": self.WEIGHTS["sector_momentum"],
                "contribution": round(sector_score * self.WEIGHTS["sector_momentum"], 2),
                "details": sector_details
            }
        }

        # Generate scenarios
        scenarios = self._calculate_scenarios(components)

        # Generate key drivers and risks
        key_drivers = self._identify_key_drivers(components)
        risks = self._identify_risks(components)

        return {
            "ticker": ticker,
            "overall_score": round(overall_score, 2),
            "confidence": round(confidence, 2),
            "timestamp": datetime.now(),
            "components": components,
            "scenarios": scenarios,
            "key_drivers": key_drivers,
            "risks": risks,
            "benchmark": benchmark_ticker
        }

    # ==================== Component Scoring Methods ====================

    def _calculate_momentum_score(
        self,
        ticker: str,
        indicators: Dict[str, float],
        price_data: List[Dict]
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate momentum score (0-100).

        Components:
        - Price vs 50-day MA: +10 if above, -10 if below
        - Price vs 200-day MA: +15 if above, -15 if below
        - 3-month return: +10 to -10 (normalized)
        - Volume trend: +5 to -5

        Max: 25 points (normalized to 0-100)
        """
        score = 50  # Start neutral
        details = {}

        current_price = price_data[-1]['close'] if price_data else 0

        # Price vs 50-day MA
        if 'sma_50' in indicators and current_price > 0:
            sma_50 = indicators['sma_50']
            pct_diff = ((current_price - sma_50) / sma_50) * 100

            if pct_diff > 5:
                points = 10
                reason = f"Price {pct_diff:.1f}% above 50-day MA (bullish)"
            elif pct_diff < -5:
                points = -10
                reason = f"Price {pct_diff:.1f}% below 50-day MA (bearish)"
            else:
                points = pct_diff * 2  # Scale: -10 to +10
                reason = f"Price near 50-day MA ({pct_diff:.1f}%)"

            score += points
            details['price_vs_50ma'] = {"value": round(points, 2), "reason": reason}

        # Price vs 200-day MA
        if 'sma_200' in indicators and current_price > 0:
            sma_200 = indicators['sma_200']
            pct_diff = ((current_price - sma_200) / sma_200) * 100

            if pct_diff > 10:
                points = 15
                reason = f"Price {pct_diff:.1f}% above 200-day MA (strong bullish)"
            elif pct_diff < -10:
                points = -15
                reason = f"Price {pct_diff:.1f}% below 200-day MA (strong bearish)"
            else:
                points = pct_diff * 1.5  # Scale: -15 to +15
                reason = f"Price vs 200-day MA: {pct_diff:.1f}%"

            score += points
            details['price_vs_200ma'] = {"value": round(points, 2), "reason": reason}

        # 3-month return
        if len(price_data) >= 63:  # ~3 months trading days
            price_3m_ago = price_data[-63]['close']
            return_3m = ((current_price - price_3m_ago) / price_3m_ago) * 100

            # Normalize to -10 to +10 (assume ±30% is extreme)
            points = np.clip(return_3m / 3, -10, 10)
            reason = f"3-month return: {return_3m:.1f}%"

            score += points
            details['return_3m'] = {"value": round(points, 2), "reason": reason}

        # Volume trend
        if 'volume_sma_20' in indicators and len(price_data) >= 20:
            current_volume = price_data[-1]['volume']
            avg_volume = indicators['volume_sma_20']

            if current_volume > avg_volume * 1.5:
                points = 5
                reason = f"Volume {(current_volume/avg_volume - 1)*100:.0f}% above average (strong interest)"
            elif current_volume < avg_volume * 0.7:
                points = -3
                reason = "Volume below average (weak interest)"
            else:
                points = 0
                reason = "Volume near average"

            score += points
            details['volume_trend'] = {"value": round(points, 2), "reason": reason}

        return max(0, min(100, score)), details

    def _calculate_valuation_divergence(
        self,
        ticker: str,
        indicators: Dict[str, float],
        price_data: List[Dict]
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate valuation divergence score (0-100).

        Uses price bands and volatility as proxy for valuation (fundamentals deferred).

        Components:
        - Bollinger Bands position: Lower band = undervalued (+10), Upper = overvalued (-10)
        - Price vs 52-week range: Near low = undervalued (+10), Near high = overvalued (-10)

        Max: 20 points (normalized to 0-100)
        """
        score = 50  # Start neutral
        details = {}

        current_price = price_data[-1]['close'] if price_data else 0

        # Bollinger Bands position
        if all(k in indicators for k in ['bb_upper', 'bb_lower', 'bb_middle']):
            bb_upper = indicators['bb_upper']
            bb_lower = indicators['bb_lower']
            bb_middle = indicators['bb_middle']
            bb_range = bb_upper - bb_lower

            if bb_range > 0:
                position = (current_price - bb_lower) / bb_range  # 0 to 1

                if position < 0.2:
                    points = 10
                    reason = f"Price near lower Bollinger Band (potentially undervalued)"
                elif position > 0.8:
                    points = -10
                    reason = f"Price near upper Bollinger Band (potentially overvalued)"
                else:
                    # Linear scale: 0.2 -> +5, 0.5 -> 0, 0.8 -> -5
                    points = 10 - (position * 20)
                    reason = f"Price in middle of Bollinger Bands"

                score += points
                details['bollinger_position'] = {"value": round(points, 2), "reason": reason}

        # 52-week range position
        if len(price_data) >= 252:
            prices_52w = [p['close'] for p in price_data[-252:]]
            high_52w = max(prices_52w)
            low_52w = min(prices_52w)
            range_52w = high_52w - low_52w

            if range_52w > 0:
                position = (current_price - low_52w) / range_52w  # 0 to 1

                if position < 0.2:
                    points = 10
                    reason = f"Price near 52-week low (potentially undervalued)"
                elif position > 0.8:
                    points = -10
                    reason = f"Price near 52-week high (potentially overvalued)"
                else:
                    points = 10 - (position * 20)
                    reason = f"Price at {position*100:.0f}% of 52-week range"

                score += points
                details['range_52w_position'] = {"value": round(points, 2), "reason": reason}

        return max(0, min(100, score)), details

    def _calculate_growth_acceleration(
        self,
        ticker: str,
        indicators: Dict[str, float],
        price_data: List[Dict]
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate growth acceleration score (0-100).

        Uses price momentum as proxy for growth (fundamentals deferred).

        Components:
        - RSI trend: Rising RSI indicates strengthening momentum
        - MACD momentum: Positive and increasing indicates acceleration
        - Rate of Change: Increasing ROC shows acceleration

        Max: 25 points (normalized to 0-100)
        """
        score = 50  # Start neutral
        details = {}

        # RSI analysis
        if 'rsi_14' in indicators:
            rsi = indicators['rsi_14']

            if 40 < rsi < 60:
                points = 10
                reason = f"RSI at {rsi:.1f} (balanced momentum, room to grow)"
            elif rsi > 70:
                points = -5
                reason = f"RSI at {rsi:.1f} (overbought, momentum may fade)"
            elif rsi < 30:
                points = 5
                reason = f"RSI at {rsi:.1f} (oversold, potential reversal)"
            else:
                points = 0
                reason = f"RSI at {rsi:.1f} (neutral)"

            score += points
            details['rsi_momentum'] = {"value": round(points, 2), "reason": reason}

        # MACD analysis
        if all(k in indicators for k in ['macd', 'macd_signal', 'macd_histogram']):
            macd = indicators['macd']
            signal = indicators['macd_signal']
            histogram = indicators['macd_histogram']

            if macd > signal and histogram > 0:
                points = 8 if abs(histogram) > 1 else 5
                reason = f"MACD bullish crossover (histogram: {histogram:.2f})"
            elif macd < signal and histogram < 0:
                points = -8 if abs(histogram) > 1 else -5
                reason = f"MACD bearish crossover (histogram: {histogram:.2f})"
            else:
                points = 0
                reason = "MACD neutral"

            score += points
            details['macd_acceleration'] = {"value": round(points, 2), "reason": reason}

        # Rate of Change
        if 'roc_12' in indicators:
            roc = indicators['roc_12']

            if roc > 10:
                points = 7
                reason = f"Strong positive momentum (ROC: {roc:.1f}%)"
            elif roc < -10:
                points = -7
                reason = f"Strong negative momentum (ROC: {roc:.1f}%)"
            else:
                points = roc * 0.5  # Scale to -5 to +5
                reason = f"ROC: {roc:.1f}%"

            score += points
            details['rate_of_change'] = {"value": round(points, 2), "reason": reason}

        return max(0, min(100, score)), details

    def _calculate_relative_strength(
        self,
        ticker: str,
        price_data: List[Dict],
        benchmark_data: List[Dict]
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate relative strength score (0-100).

        Measures performance vs market benchmark.

        Max: 15 points (normalized to 0-100)
        """
        score = 50  # Start neutral
        details = {}

        if not price_data or not benchmark_data:
            return score, {"error": "Insufficient data"}

        # Calculate returns for different periods
        periods = [21, 63, 126]  # 1 month, 3 months, 6 months

        for period_days in periods:
            if len(price_data) >= period_days and len(benchmark_data) >= period_days:
                ticker_return = ((price_data[-1]['close'] - price_data[-period_days]['close'])
                               / price_data[-period_days]['close']) * 100
                benchmark_return = ((benchmark_data[-1]['close'] - benchmark_data[-period_days]['close'])
                                  / benchmark_data[-period_days]['close']) * 100

                outperformance = ticker_return - benchmark_return

                # Weight recent performance more
                weight = 1.0 if period_days == 21 else (0.7 if period_days == 63 else 0.5)

                if outperformance > 5:
                    points = 5 * weight
                    reason = f"Outperforming benchmark by {outperformance:.1f}% ({period_days} days)"
                elif outperformance < -5:
                    points = -5 * weight
                    reason = f"Underperforming benchmark by {abs(outperformance):.1f}% ({period_days} days)"
                else:
                    points = outperformance * 0.5 * weight
                    reason = f"Relative performance: {outperformance:+.1f}% ({period_days} days)"

                score += points
                details[f'relative_{period_days}d'] = {"value": round(points, 2), "reason": reason}

        return max(0, min(100, score)), details

    def _calculate_sector_momentum(
        self,
        ticker: str,
        price_data: List[Dict]
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate sector momentum score (0-100).

        For now, uses ADX as trend strength proxy (sector data deferred).

        Max: 15 points (normalized to 0-100)
        """
        score = 50  # Start neutral
        details = {}

        # Get ticker metadata
        ticker_obj = self.db.query(Ticker).filter(Ticker.ticker == ticker).first()

        if ticker_obj and ticker_obj.sector:
            details['sector'] = ticker_obj.sector

        # Use ADX as trend strength indicator (proxy for sector momentum)
        indicators = self.signal_engine.get_latest_indicators(ticker)

        if 'adx_14' in indicators:
            adx = indicators['adx_14']

            if adx > 40:
                points = 15
                reason = f"Strong trend (ADX: {adx:.1f})"
            elif adx > 25:
                points = 10
                reason = f"Moderate trend (ADX: {adx:.1f})"
            else:
                points = 0
                reason = f"Weak/no trend (ADX: {adx:.1f})"

            score += points
            details['trend_strength'] = {"value": round(points, 2), "reason": reason}

        return max(0, min(100, score)), details

    # ==================== Supporting Methods ====================

    def _calculate_confidence(
        self,
        indicators: Dict[str, float],
        price_data: List[Dict],
        component_details: List[Dict]
    ) -> float:
        """
        Calculate confidence level (0-100).

        Based on:
        - Data completeness: Full indicators = 100%, missing = penalty
        - Data freshness: Recent data = 100%, stale = penalty
        - Signal consistency: Aligned signals = high confidence
        """
        confidence = 100.0

        # Data completeness penalty
        expected_indicators = 15  # Approximate number of key indicators
        actual_indicators = len(indicators)
        if actual_indicators < expected_indicators:
            confidence -= ((expected_indicators - actual_indicators) / expected_indicators) * 20

        # Data freshness penalty (assume data should be from last 2 days)
        if price_data:
            latest_date = price_data[-1]['timestamp']
            days_old = (datetime.now() - latest_date).days
            if days_old > 2:
                confidence -= min(days_old * 3, 20)

        # Data quantity penalty
        if len(price_data) < 100:
            confidence -= (100 - len(price_data)) * 0.3

        return max(0, min(100, confidence))

    def _calculate_scenarios(
        self,
        components: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Calculate bull/base/bear case scenarios.

        Bull: Top quartile performance for each component
        Base: Current scores
        Bear: Bottom quartile performance for each component
        """
        base_score = sum(c["contribution"] for c in components.values())

        # Bull case: Add 20% to each positive component
        bull_adjustments = sum(
            c["contribution"] * 0.2 if c["score"] > 50 else 0
            for c in components.values()
        )
        bull_score = base_score + bull_adjustments

        # Bear case: Reduce 20% from each component
        bear_adjustments = sum(
            c["contribution"] * 0.2
            for c in components.values()
        )
        bear_score = base_score - bear_adjustments

        return {
            "bull": round(min(bull_score, 100), 2),
            "base": round(base_score, 2),
            "bear": round(max(bear_score, 0), 2)
        }

    def _identify_key_drivers(
        self,
        components: Dict[str, Any]
    ) -> List[str]:
        """Identify top 3-5 key drivers (positive factors)."""
        drivers = []

        for comp_name, comp_data in components.items():
            if comp_data["score"] > 60:  # Strong positive
                # Get best detail from component
                details = comp_data["details"]
                for detail_name, detail_data in details.items():
                    if detail_data.get("value", 0) > 3:
                        drivers.append(detail_data["reason"])

        return drivers[:5]  # Top 5

    def _identify_risks(
        self,
        components: Dict[str, Any]
    ) -> List[str]:
        """Identify top 3-5 risks (negative factors)."""
        risks = []

        for comp_name, comp_data in components.items():
            if comp_data["score"] < 40:  # Weak/negative
                # Get worst detail from component
                details = comp_data["details"]
                for detail_name, detail_data in details.items():
                    if detail_data.get("value", 0) < -3:
                        risks.append(detail_data["reason"])

        return risks[:5]  # Top 5

    def _get_recent_price_data(
        self,
        ticker: str,
        days: int
    ) -> List[Dict]:
        """Get recent price data for a ticker."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        price_records = self.db.query(PriceData).filter(
            PriceData.ticker == ticker,
            PriceData.timestamp >= start_date,
            PriceData.timestamp <= end_date
        ).order_by(PriceData.timestamp).all()

        return [
            {
                "timestamp": p.timestamp,
                "open": float(p.open),
                "high": float(p.high),
                "low": float(p.low),
                "close": float(p.close),
                "volume": int(p.volume) if p.volume else 0
            }
            for p in price_records
        ]

    def _insufficient_data_response(self, ticker: str) -> Dict[str, Any]:
        """Return response when insufficient data available."""
        return {
            "ticker": ticker,
            "overall_score": 0,
            "confidence": 0,
            "timestamp": datetime.now(),
            "error": "Insufficient data for scoring",
            "message": "Ticker needs more price data and calculated indicators"
        }

    # ==================== Batch Scoring ====================

    def score_all_tickers(
        self,
        min_confidence: float = 50.0,
        benchmark_ticker: str = "SPY"
    ) -> Dict[str, Any]:
        """
        Score all active tickers.

        Args:
            min_confidence: Minimum confidence to include in results
            benchmark_ticker: Benchmark for relative strength

        Returns:
            Dictionary with scoring results and summary
        """
        logger.info("Scoring all active tickers")

        tickers = self.db.query(Ticker).filter(Ticker.is_active == True).all()

        results = {
            "total_tickers": len(tickers),
            "scored": 0,
            "skipped": 0,
            "errors": [],
            "scores": []
        }

        for ticker_obj in tickers:
            try:
                score_result = self.score_ticker(
                    ticker=ticker_obj.ticker,
                    benchmark_ticker=benchmark_ticker
                )

                if "error" in score_result:
                    results["skipped"] += 1
                    continue

                # Filter by confidence
                if score_result["confidence"] >= min_confidence:
                    results["scored"] += 1
                    results["scores"].append({
                        "ticker": score_result["ticker"],
                        "score": score_result["overall_score"],
                        "confidence": score_result["confidence"],
                        "timestamp": score_result["timestamp"]
                    })
                else:
                    results["skipped"] += 1

            except Exception as e:
                logger.error(f"Error scoring {ticker_obj.ticker}: {e}")
                results["errors"].append({
                    "ticker": ticker_obj.ticker,
                    "error": str(e)
                })

        # Sort by score descending
        results["scores"].sort(key=lambda x: x["score"], reverse=True)

        logger.info(f"Scored {results['scored']} tickers, skipped {results['skipped']}")

        return results

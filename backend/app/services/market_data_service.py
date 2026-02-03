"""
Market Data Service

Fetches market data exclusively from the Schwab API.
Raises on startup if SCHWAB_API_KEY / SCHWAB_API_SECRET are not configured.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.config import settings

logger = logging.getLogger(__name__)

# Interval string → (frequencyType, periodType) for Schwab /pricehistory
_FREQUENCY_MAP = {
    "1m":  ("minute",  "day"),
    "5m":  ("minute",  "day"),
    "15m": ("minute",  "day"),
    "30m": ("minute",  "day"),
    "1h":  ("minute",  "day"),
    "1d":  ("daily",   "month"),
    "1wk": ("weekly",  "year"),
    "1mo": ("monthly", "year"),
}


class MarketDataService:
    """Schwab-backed market data service."""

    def __init__(self):
        if not settings.schwab_api_key or not settings.schwab_api_secret:
            raise RuntimeError(
                "Schwab API credentials not configured. "
                "Set SCHWAB_API_KEY and SCHWAB_API_SECRET in your .env file."
            )
        logger.info("Market Data Service initialized (Schwab)")

    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get real-time quote for a symbol from Schwab."""
        from app.services.schwab_client import schwab_client
        return await schwab_client.get_quote(symbol)

    async def get_price_history(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = "1d",
    ) -> List[Dict[str, Any]]:
        """
        Get historical price data from Schwab and return as a list of
        standardised OHLCV dicts keyed by 'datetime'.
        """
        from app.services.schwab_client import schwab_client

        frequency_type, period_type = _FREQUENCY_MAP.get(interval, ("daily", "month"))

        response = await schwab_client.get_price_history(
            symbol=symbol,
            period_type=period_type,
            start_date=start_date,
            end_date=end_date,
            frequency_type=frequency_type,
            frequency=1,
        )

        candles = []
        if response and "candles" in response:
            for candle in response["candles"]:
                candles.append({
                    "datetime":      datetime.fromtimestamp(candle["datetime"] / 1000),
                    "open":          candle["open"],
                    "high":          candle["high"],
                    "low":           candle["low"],
                    "close":         candle["close"],
                    "volume":        candle["volume"],
                    "adjusted_close": candle["close"],
                })

        logger.info(f"Fetched {len(candles)} candles for {symbol} from Schwab")
        return candles


# Global instance — raises immediately if creds are missing
market_data_service = MarketDataService()

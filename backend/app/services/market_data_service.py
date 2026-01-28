"""
Market Data Service

Abstracts market data fetching to support multiple providers.
Switches between Schwab API (production) and yfinance (development).
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import asyncio

from app.config import settings

logger = logging.getLogger(__name__)


class MarketDataService:
    """
    Unified market data service supporting multiple providers.

    Providers:
    - Schwab API (production) - requires authentication
    - yfinance (development) - free, no auth required
    """

    def __init__(self, provider: str = "auto"):
        """
        Initialize market data service.

        Args:
            provider: "schwab", "yfinance", or "auto" (auto-detect based on credentials)
        """
        self.provider = self._determine_provider(provider)
        logger.info(f"Market Data Service initialized with provider: {self.provider}")

    def _determine_provider(self, provider: str) -> str:
        """Determine which provider to use."""
        if provider != "auto":
            return provider

        # Auto-detect: use Schwab if credentials are configured
        if settings.schwab_api_key and settings.schwab_api_secret:
            return "schwab"
        else:
            logger.warning("Schwab API credentials not configured, using yfinance for development")
            return "yfinance"

    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Get real-time quote for a symbol.

        Args:
            symbol: Stock symbol (e.g., "AAPL")

        Returns:
            Quote data with standardized format
        """
        if self.provider == "schwab":
            return await self._get_quote_schwab(symbol)
        else:
            return await self._get_quote_yfinance(symbol)

    async def get_price_history(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = "1d"
    ) -> List[Dict[str, Any]]:
        """
        Get historical price data.

        Args:
            symbol: Stock symbol
            start_date: Start date for historical data
            end_date: End date for historical data
            interval: Data interval ('1d', '1wk', '1mo')

        Returns:
            List of OHLCV data points
        """
        if self.provider == "schwab":
            return await self._get_price_history_schwab(symbol, start_date, end_date, interval)
        else:
            return await self._get_price_history_yfinance(symbol, start_date, end_date, interval)

    async def get_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """
        Get fundamental data for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Fundamental metrics
        """
        if self.provider == "schwab":
            return await self._get_fundamentals_schwab(symbol)
        else:
            return await self._get_fundamentals_yfinance(symbol)

    # Schwab API implementations (placeholder)

    async def _get_quote_schwab(self, symbol: str) -> Dict[str, Any]:
        """Get quote from Schwab API."""
        from app.services.schwab_client import schwab_client
        return await schwab_client.get_quote(symbol)

    async def _get_price_history_schwab(
        self,
        symbol: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        interval: str
    ) -> List[Dict[str, Any]]:
        """Get price history from Schwab API."""
        from app.services.schwab_client import schwab_client

        # Map interval to Schwab API frequency types and period types
        frequency_map = {
            "1m": ("minute", "day"),
            "5m": ("minute", "day"),
            "15m": ("minute", "day"),
            "30m": ("minute", "day"),
            "1h": ("minute", "day"),
            "1d": ("daily", "month"),  # For daily data, use month or year periodType
            "1wk": ("weekly", "year"),
            "1mo": ("monthly", "year")
        }

        frequency_type, period_type = frequency_map.get(interval, ("daily", "month"))

        # Get the raw API response
        # For daily data with custom date ranges, use periodType=month or year
        response = await schwab_client.get_price_history(
            symbol=symbol,
            period_type=period_type,
            start_date=start_date,
            end_date=end_date,
            frequency_type=frequency_type,
            frequency=1
        )

        # Convert Schwab API response to standardized format
        candles = []
        if response and "candles" in response:
            for candle in response["candles"]:
                # Convert epoch milliseconds to datetime
                timestamp = datetime.fromtimestamp(candle["datetime"] / 1000)
                candles.append({
                    "datetime": timestamp,
                    "open": candle["open"],
                    "high": candle["high"],
                    "low": candle["low"],
                    "close": candle["close"],
                    "volume": candle["volume"],
                    "adjusted_close": candle["close"]  # Schwab doesn't provide adjusted close separately
                })

        logger.info(f"Fetched {len(candles)} candles for {symbol} from Schwab API")
        return candles

    async def _get_fundamentals_schwab(self, symbol: str) -> Dict[str, Any]:
        """Get fundamentals from Schwab API."""
        from app.services.schwab_client import schwab_client
        return await schwab_client.get_fundamentals(symbol)

    # yfinance implementations

    async def _get_quote_yfinance(self, symbol: str) -> Dict[str, Any]:
        """Get quote using yfinance."""
        try:
            import yfinance as yf

            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Get current price from fast_info (more reliable)
            try:
                current_price = ticker.fast_info.last_price
                prev_close = ticker.fast_info.previous_close
            except:
                current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
                prev_close = info.get('previousClose', current_price)

            change = current_price - prev_close
            change_percent = (change / prev_close * 100) if prev_close else 0

            return {
                "symbol": symbol,
                "lastPrice": current_price,
                "previousClose": prev_close,
                "change": change,
                "changePercent": change_percent,
                "volume": info.get('volume', 0),
                "marketCap": info.get('marketCap', 0),
                "timestamp": datetime.now().isoformat(),
                "provider": "yfinance"
            }
        except Exception as e:
            logger.error(f"Error fetching quote for {symbol} from yfinance: {e}")
            raise

    async def _get_price_history_yfinance(
        self,
        symbol: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        interval: str
    ) -> List[Dict[str, Any]]:
        """Get price history using yfinance."""
        try:
            import yfinance as yf

            if not start_date:
                start_date = datetime.now() - timedelta(days=365)
            if not end_date:
                end_date = datetime.now()

            ticker = yf.Ticker(symbol)

            # Download historical data
            df = ticker.history(
                start=start_date,
                end=end_date,
                interval=interval
            )

            # Convert to list of dicts
            candles = []
            for timestamp, row in df.iterrows():
                candles.append({
                    "datetime": timestamp,
                    "open": float(row['Open']),
                    "high": float(row['High']),
                    "low": float(row['Low']),
                    "close": float(row['Close']),
                    "volume": int(row['Volume']),
                    "adjusted_close": float(row['Close'])  # yfinance already adjusts
                })

            logger.info(f"Fetched {len(candles)} candles for {symbol} from yfinance")
            return candles

        except Exception as e:
            logger.error(f"Error fetching price history for {symbol} from yfinance: {e}")
            raise

    async def _get_fundamentals_yfinance(self, symbol: str) -> Dict[str, Any]:
        """Get fundamentals using yfinance."""
        try:
            import yfinance as yf

            ticker = yf.Ticker(symbol)
            info = ticker.info

            return {
                "symbol": symbol,
                "name": info.get('longName', symbol),
                "sector": info.get('sector', 'Unknown'),
                "industry": info.get('industry', 'Unknown'),
                "marketCap": info.get('marketCap', 0),
                "peRatio": info.get('trailingPE', 0),
                "forwardPE": info.get('forwardPE', 0),
                "priceToSales": info.get('priceToSalesTrailing12Months', 0),
                "priceToBook": info.get('priceToBook', 0),
                "dividendYield": info.get('dividendYield', 0),
                "beta": info.get('beta', 1.0),
                "eps": info.get('trailingEps', 0),
                "revenue": info.get('totalRevenue', 0),
                "profitMargin": info.get('profitMargins', 0),
                "operatingMargin": info.get('operatingMargins', 0),
                "returnOnEquity": info.get('returnOnEquity', 0),
                "debtToEquity": info.get('debtToEquity', 0),
                "provider": "yfinance"
            }

        except Exception as e:
            logger.error(f"Error fetching fundamentals for {symbol} from yfinance: {e}")
            raise


# Global instance
market_data_service = MarketDataService()

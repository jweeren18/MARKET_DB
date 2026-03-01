"""
Schwab API Client for fetching market data.

This client handles:
- OAuth 2.0 authentication with Schwab API
- Token storage and refresh
- Fetching historical price data
- Fetching real-time quotes
- Rate limiting and error handling
"""

import httpx
import logging
import json
import os
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from pathlib import Path
from authlib.integrations.httpx_client import OAuth2Client

from app.config import settings

logger = logging.getLogger(__name__)


class SchwabAPIError(Exception):
    """Base exception for Schwab API errors."""
    pass


class SchwabClient:
    """
    Client for interacting with Schwab Developer API.

    Schwab API Documentation: https://developer.schwab.com/products/trader-api--individual
    Uses OAuth 2.0 Authorization Code flow for authentication.
    """

    BASE_URL = "https://api.schwabapi.com/marketdata/v1"
    AUTH_URL = "https://api.schwabapi.com/v1/oauth/authorize"
    TOKEN_URL = "https://api.schwabapi.com/v1/oauth/token"

    def __init__(self):
        """Initialize Schwab API client."""
        self.api_key = settings.schwab_api_key
        self.api_secret = settings.schwab_api_secret
        self.callback_url = settings.schwab_callback_url

        # Token storage file (use resolve() to get absolute path)
        self.token_file = Path(__file__).resolve().parent.parent.parent.parent / ".schwab_tokens.json"

        # OAuth client
        self.oauth_client: Optional[OAuth2Client] = None

        if not self.api_key or not self.api_secret:
            logger.warning("Schwab API credentials not configured")
        else:
            self._load_tokens()

    def _load_tokens(self) -> None:
        """Load stored OAuth tokens from environment variable or file.

        Checks SCHWAB_TOKENS_JSON env var first (used by K8s pods where the
        token file isn't available), then falls back to the on-disk file.
        """
        token_data = None
        source = None

        # Prefer env var (K8s Secrets mount tokens this way)
        tokens_json = os.environ.get("SCHWAB_TOKENS_JSON")
        if tokens_json:
            try:
                token_data = json.loads(tokens_json)
                source = "environment variable"
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse SCHWAB_TOKENS_JSON: {e}")

        # Fall back to on-disk file (local dev)
        if token_data is None and self.token_file.exists():
            try:
                with open(self.token_file, "r") as f:
                    token_data = json.load(f)
                source = "token file"
            except Exception as e:
                logger.error(f"Failed to load tokens from file: {e}")

        if token_data:
            self.oauth_client = OAuth2Client(
                client_id=self.api_key,
                client_secret=self.api_secret,
                token_endpoint=self.TOKEN_URL,
                token=token_data,
            )
            logger.info(f"Loaded Schwab OAuth tokens from {source}")
        else:
            logger.info("No stored tokens found - OAuth flow required")

    def _save_tokens(self, token: Dict[str, Any]) -> None:
        """Save OAuth tokens to file."""
        try:
            with open(self.token_file, "w") as f:
                json.dump(token, f, indent=2)
            logger.info("Saved Schwab OAuth tokens")
        except Exception as e:
            logger.error(f"Failed to save tokens: {e}")

    def get_authorization_url(self) -> str:
        """
        Get the OAuth authorization URL for user login.

        Returns:
            Authorization URL to redirect user to
        """
        params = {
            "response_type": "code",
            "client_id": self.api_key,
            "redirect_uri": self.callback_url,
            "scope": "readonly",  # Adjust scope as needed
        }

        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        auth_url = f"{self.AUTH_URL}?{query_string}"

        logger.info(f"Authorization URL: {auth_url}")
        return auth_url

    async def exchange_code_for_token(self, authorization_code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.

        Args:
            authorization_code: Code received from OAuth callback

        Returns:
            Token response containing access_token, refresh_token, etc.
        """
        try:
            # Create OAuth client
            self.oauth_client = OAuth2Client(
                client_id=self.api_key,
                client_secret=self.api_secret,
                token_endpoint=self.TOKEN_URL,
            )

            # Exchange code for token (fetch_token is synchronous, run in thread pool)
            import asyncio
            token = await asyncio.to_thread(
                self.oauth_client.fetch_token,
                url=self.TOKEN_URL,
                grant_type="authorization_code",
                code=authorization_code,
                redirect_uri=self.callback_url,
            )

            # Save tokens
            self._save_tokens(token)

            logger.info("Successfully obtained access token")
            return token

        except Exception as e:
            logger.error(f"Failed to exchange code for token: {e}")
            raise SchwabAPIError(f"Token exchange failed: {str(e)}")

    async def _ensure_valid_token(self) -> None:
        """Ensure we have a valid access token, refreshing if necessary."""
        if not self.oauth_client:
            raise SchwabAPIError(
                "Not authenticated. Please complete OAuth flow first. "
                "Call get_authorization_url() to start."
            )

        # Check if token needs refresh
        token = self.oauth_client.token
        if token and "expires_at" in token:
            expires_at = datetime.fromtimestamp(token["expires_at"])
            # Refresh if token expires in less than 5 minutes
            if datetime.now() >= expires_at - timedelta(minutes=5):
                logger.info("Access token expired or expiring soon, refreshing...")
                try:
                    import asyncio
                    new_token = await asyncio.to_thread(
                        self.oauth_client.refresh_token,
                        url=self.TOKEN_URL,
                    )
                    self._save_tokens(new_token)
                    logger.info("Token refreshed successfully")
                except Exception as e:
                    logger.error(f"Token refresh failed: {e}")
                    raise SchwabAPIError(f"Token refresh failed: {str(e)}")

    async def _make_request(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make an authenticated request to Schwab API.

        Args:
            endpoint: API endpoint (e.g., "/pricehistory")
            params: Query parameters

        Returns:
            API response as dictionary
        """
        await self._ensure_valid_token()

        try:
            url = f"{self.BASE_URL}{endpoint}"

            # Use OAuth client to make authenticated request (synchronous, run in thread pool)
            import asyncio
            response = await asyncio.to_thread(
                self.oauth_client.get,
                url,
                params=params,
                timeout=30.0
            )
            response.raise_for_status()

            return response.json()

        except httpx.HTTPStatusError as e:
            error_detail = e.response.text
            logger.error(f"Schwab API HTTP error: {e.response.status_code} - {error_detail}")

            # Parse error response if JSON
            try:
                error_json = e.response.json()
                if "errors" in error_json:
                    error_messages = [err.get("detail", err.get("title", "Unknown error"))
                                    for err in error_json["errors"]]
                    error_detail = "; ".join(error_messages)
            except:
                pass

            raise SchwabAPIError(f"HTTP {e.response.status_code}: {error_detail}")

        except Exception as e:
            logger.error(f"Schwab API request failed: {e}")
            raise SchwabAPIError(f"Request failed: {str(e)}")

    async def get_quote(self, symbol: str, fields: Optional[str] = None) -> Dict[str, Any]:
        """
        Get real-time quote for a symbol.

        Args:
            symbol: Stock symbol (e.g., "AAPL")
            fields: Comma-separated list of fields to include

        Returns:
            Quote data including price, volume, etc.
        """
        logger.info(f"Fetching quote for {symbol}")

        params = {}
        if fields:
            params["fields"] = fields

        endpoint = f"/quotes/{symbol}"
        return await self._make_request(endpoint, params)

    async def get_price_history(
        self,
        symbol: str,
        period_type: Optional[str] = None,
        period: Optional[int] = None,
        frequency_type: Optional[str] = None,
        frequency: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        need_extended_hours: bool = False,
        need_previous_close: bool = True,
    ) -> Dict[str, Any]:
        """
        Get historical price data for a symbol.

        Args:
            symbol: Stock symbol (e.g., "AAPL")
            period_type: Chart period type (day, month, year, ytd)
            period: Number of periods
            frequency_type: Time frequency type (minute, daily, weekly, monthly)
            frequency: Time frequency duration
            start_date: Start date (datetime object)
            end_date: End date (datetime object)
            need_extended_hours: Include extended hours data
            need_previous_close: Include previous close price/date

        Returns:
            Price history with candles array containing OHLCV data

        Example response:
            {
              "symbol": "AAPL",
              "empty": false,
              "previousClose": 174.56,
              "previousCloseDate": 1639029600000,
              "candles": [
                {
                  "open": 175.01,
                  "high": 175.15,
                  "low": 175.01,
                  "close": 175.04,
                  "volume": 10719,
                  "datetime": 1639137600000
                }
              ]
            }
        """
        logger.info(f"Fetching price history for {symbol}")

        params = {"symbol": symbol}

        # Add optional parameters
        if period_type:
            params["periodType"] = period_type
        if period is not None:
            params["period"] = period
        if frequency_type:
            params["frequencyType"] = frequency_type
        if frequency is not None:
            params["frequency"] = frequency
        if start_date:
            # Convert to EPOCH milliseconds
            params["startDate"] = int(start_date.timestamp() * 1000)
        if end_date:
            # Convert to EPOCH milliseconds
            params["endDate"] = int(end_date.timestamp() * 1000)
        if need_extended_hours:
            params["needExtendedHoursData"] = "true"
        if need_previous_close:
            params["needPreviousClose"] = "true"

        endpoint = "/pricehistory"
        return await self._make_request(endpoint, params)

    async def get_price_history_daily(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Convenience method to get daily price history.

        Args:
            symbol: Stock symbol
            start_date: Start date (defaults to 1 year ago)
            end_date: End date (defaults to today)

        Returns:
            List of daily candles with OHLCV data
        """
        if not start_date:
            start_date = datetime.now() - timedelta(days=365)
        if not end_date:
            end_date = datetime.now()

        response = await self.get_price_history(
            symbol=symbol,
            period_type="year",
            period=1,
            frequency_type="daily",
            frequency=1,
            start_date=start_date,
            end_date=end_date,
        )

        return response.get("candles", [])

    async def get_instruments(
        self, symbol: str, projection: str = "symbol-search"
    ) -> Dict[str, Any]:
        """
        Search for instruments by symbol or description.

        Args:
            symbol: Symbol or search query
            projection: Type of search (symbol-search, symbol-regex, desc-search, etc.)

        Returns:
            Instrument data
        """
        logger.info(f"Searching instruments for: {symbol}")

        params = {"symbol": symbol, "projection": projection}
        endpoint = "/instruments"
        return await self._make_request(endpoint, params)

    def is_authenticated(self) -> bool:
        """Check if client is authenticated with valid token."""
        if not self.oauth_client or not self.oauth_client.token:
            return False

        token = self.oauth_client.token
        if "expires_at" in token:
            expires_at = datetime.fromtimestamp(token["expires_at"])
            return datetime.now() < expires_at

        return True


# Global client instance
schwab_client = SchwabClient()

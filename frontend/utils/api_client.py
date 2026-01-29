"""
API client for communicating with the FastAPI backend.
"""

import httpx
import streamlit as st
from typing import Dict, List, Optional, Any
from .config import get_api_url


class APIClient:
    """Client for making requests to the backend API."""

    def __init__(self, base_url: Optional[str] = None):
        """Initialize API client.

        Args:
            base_url: Base URL for the API. Defaults to environment config.
        """
        self.base_url = base_url or get_api_url()
        self.timeout = httpx.Timeout(30.0)

    def _handle_response(self, response: httpx.Response) -> Any:
        """Handle API response and errors.

        Args:
            response: httpx Response object

        Returns:
            Response JSON data

        Raises:
            Exception: If response status is not successful
        """
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            st.error(f"Resource not found: {response.url}")
            return None
        else:
            st.error(f"API Error ({response.status_code}): {response.text}")
            return None

    # Portfolio APIs
    def get_portfolios(self) -> Optional[List[Dict]]:
        """Get all portfolios."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(f"{self.base_url}/api/portfolios")
                return self._handle_response(response)
        except httpx.ConnectError:
            st.error(f"Cannot connect to backend API at {self.base_url}")
            return None
        except Exception as e:
            st.error(f"Error fetching portfolios: {str(e)}")
            return None

    def get_portfolio(self, portfolio_id: str) -> Optional[Dict]:
        """Get portfolio by ID."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(f"{self.base_url}/api/portfolios/{portfolio_id}")
                return self._handle_response(response)
        except Exception as e:
            st.error(f"Error fetching portfolio: {str(e)}")
            return None

    def create_portfolio(self, name: str, description: Optional[str] = None) -> Optional[Dict]:
        """Create a new portfolio."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/api/portfolios",
                    json={"name": name, "description": description}
                )
                return self._handle_response(response)
        except Exception as e:
            st.error(f"Error creating portfolio: {str(e)}")
            return None

    # Market Data APIs
    def get_ticker_info(self, symbol: str) -> Optional[Dict]:
        """Get ticker information."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(f"{self.base_url}/api/tickers/{symbol}")
                return self._handle_response(response)
        except Exception as e:
            st.error(f"Error fetching ticker info: {str(e)}")
            return None

    def get_price_history(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Optional[List[Dict]]:
        """Get price history for a ticker."""
        try:
            params = {}
            if start_date:
                params["start_date"] = start_date
            if end_date:
                params["end_date"] = end_date

            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    f"{self.base_url}/api/tickers/{symbol}/history",
                    params=params
                )
                result = self._handle_response(response)
                # Extract the history list from the response
                if result and isinstance(result, dict) and "history" in result:
                    return result["history"]
                return result
        except Exception as e:
            st.error(f"Error fetching price history: {str(e)}")
            return None

    # Analytics APIs
    def get_portfolio_analytics(self, portfolio_id: str) -> Optional[Dict]:
        """Get portfolio analytics (P&L, returns, risk metrics)."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(f"{self.base_url}/api/portfolios/{portfolio_id}/analytics")
                return self._handle_response(response)
        except Exception as e:
            st.error(f"Error fetching portfolio analytics: {str(e)}")
            return None

    # Indicator APIs
    def get_latest_indicators(self, ticker: str) -> Optional[Dict]:
        """Get latest indicator values for a ticker."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(f"{self.base_url}/api/indicators/tickers/{ticker}/latest")
                return self._handle_response(response)
        except Exception as e:
            st.error(f"Error fetching indicators: {str(e)}")
            return None

    def get_indicator_history(
        self,
        ticker: str,
        indicator_name: Optional[str] = None,
        days: int = 30
    ) -> Optional[List[Dict]]:
        """Get historical indicator values."""
        try:
            params = {"days": days}
            if indicator_name:
                params["indicator_name"] = indicator_name
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    f"{self.base_url}/api/indicators/tickers/{ticker}/history",
                    params=params
                )
                return self._handle_response(response)
        except Exception as e:
            st.error(f"Error fetching indicator history: {str(e)}")
            return None

    def get_indicator_summary(self, ticker: str) -> Optional[Dict]:
        """Get indicator summary with latest values."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(f"{self.base_url}/api/indicators/tickers/{ticker}/summary")
                return self._handle_response(response)
        except Exception as e:
            st.error(f"Error fetching indicator summary: {str(e)}")
            return None

    def detect_signals(self, ticker: str) -> Optional[Dict]:
        """Detect trading signals for a ticker."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(f"{self.base_url}/api/indicators/tickers/{ticker}/signals")
                return self._handle_response(response)
        except Exception as e:
            st.error(f"Error detecting signals: {str(e)}")
            return None

    # Opportunity APIs
    def list_opportunities(
        self,
        min_score: float = 0,
        min_confidence: float = 0,
        limit: int = 50,
        sort_by: str = "score"
    ) -> Optional[Dict]:
        """List all scored opportunities with filtering."""
        try:
            params = {
                "min_score": min_score,
                "min_confidence": min_confidence,
                "limit": limit,
                "sort_by": sort_by
            }
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(f"{self.base_url}/api/opportunities", params=params)
                return self._handle_response(response)
        except Exception as e:
            st.error(f"Error fetching opportunities: {str(e)}")
            return None

    def get_opportunity(
        self,
        ticker: str,
        include_history: bool = False,
        history_days: int = 30
    ) -> Optional[Dict]:
        """Get detailed opportunity score for a ticker."""
        try:
            params = {
                "include_history": include_history,
                "history_days": history_days
            }
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(f"{self.base_url}/api/opportunities/{ticker}", params=params)
                return self._handle_response(response)
        except Exception as e:
            st.error(f"Error fetching opportunity: {str(e)}")
            return None

    def get_opportunity_components(self, ticker: str) -> Optional[Dict]:
        """Get detailed component breakdown for a ticker."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(f"{self.base_url}/api/opportunities/{ticker}/components")
                return self._handle_response(response)
        except Exception as e:
            st.error(f"Error fetching components: {str(e)}")
            return None

    def get_opportunity_explainability(self, ticker: str) -> Optional[Dict]:
        """Get full explainability (key drivers, risks, reasoning)."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(f"{self.base_url}/api/opportunities/{ticker}/explainability")
                return self._handle_response(response)
        except Exception as e:
            st.error(f"Error fetching explainability: {str(e)}")
            return None

    def get_opportunity_history(self, ticker: str, days: int = 30) -> Optional[Dict]:
        """Get historical opportunity scores."""
        try:
            params = {"days": days}
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    f"{self.base_url}/api/opportunities/history/{ticker}",
                    params=params
                )
                return self._handle_response(response)
        except Exception as e:
            st.error(f"Error fetching opportunity history: {str(e)}")
            return None

    def get_top_opportunities(
        self,
        category: str = "highest_score",
        limit: int = 10,
        min_confidence: float = 50.0
    ) -> Optional[Dict]:
        """Get top opportunities by category."""
        try:
            params = {
                "limit": limit,
                "min_confidence": min_confidence
            }
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    f"{self.base_url}/api/opportunities/top/{category}",
                    params=params
                )
                return self._handle_response(response)
        except Exception as e:
            st.error(f"Error fetching top opportunities: {str(e)}")
            return None

    # Health check
    def health_check(self) -> bool:
        """Check if backend API is healthy."""
        try:
            with httpx.Client(timeout=httpx.Timeout(5.0)) as client:
                response = client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except:
            return False


@st.cache_resource
def get_api_client() -> APIClient:
    """Get cached API client instance."""
    return APIClient()

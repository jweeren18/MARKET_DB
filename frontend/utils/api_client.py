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
                return self._handle_response(response)
        except Exception as e:
            st.error(f"Error fetching price history: {str(e)}")
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

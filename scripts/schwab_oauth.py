"""
Schwab API OAuth 2.0 Authentication Helper Script

This script helps you complete the initial OAuth flow to get an access token.

Usage:
    python scripts/schwab_oauth.py
"""

import sys
import os
from pathlib import Path

# Add backend to path
BACKEND_PATH = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(BACKEND_PATH))

import asyncio
from app.services.schwab_client import schwab_client, SchwabAPIError


async def main():
    """Run the OAuth flow."""

    print("=" * 70)
    print("Schwab API OAuth 2.0 Authentication")
    print("=" * 70)
    print()

    # Check if already authenticated
    if schwab_client.is_authenticated():
        print("[OK] Already authenticated with valid token!")
        print()
        print("Token file location:", schwab_client.token_file)
        print()
        print("You can now use the Schwab API for data ingestion.")
        return

    # Check if credentials are configured
    if not schwab_client.api_key or not schwab_client.api_secret:
        print("[ERROR] Schwab API credentials not configured!")
        print()
        print("Please add your credentials to the .env file:")
        print("  SCHWAB_API_KEY=your_app_key_here")
        print("  SCHWAB_API_SECRET=your_app_secret_here")
        print("  SCHWAB_CALLBACK_URL=http://localhost:8000/auth/callback")
        print()
        return

    print("Starting OAuth flow...")
    print()

    # Step 1: Get authorization URL
    try:
        auth_url = schwab_client.get_authorization_url()
    except Exception as e:
        print(f"[ERROR] Failed to generate authorization URL: {e}")
        return

    print("STEP 1: Authorize Your Application")
    print("-" * 70)
    print()
    print("Please visit the following URL in your browser:")
    print()
    print(auth_url)
    print()
    print("This will:")
    print("  1. Redirect you to Schwab's login page")
    print("  2. Ask you to log in with your Schwab credentials")
    print("  3. Ask you to authorize your application")
    print("  4. Redirect you to the callback URL with an authorization code")
    print()

    # Step 2: Get authorization code from user
    print("STEP 2: Enter Authorization Code")
    print("-" * 70)
    print()
    print("After authorizing, you'll be redirected to:")
    print(f"  {schwab_client.callback_url}?code=AUTHORIZATION_CODE")
    print()
    print("Copy the 'code' parameter from the URL and paste it below.")
    print()

    auth_code = input("Authorization code: ").strip()

    if not auth_code:
        print("[ERROR] No authorization code provided!")
        return

    # Step 3: Exchange code for token
    print()
    print("STEP 3: Exchanging Code for Token")
    print("-" * 70)
    print()

    try:
        token = await schwab_client.exchange_code_for_token(auth_code)
        print("[OK] Successfully obtained access token!")
        print()
        print("Token details:")
        print(f"  - Access token: {token['access_token'][:20]}...")
        print(f"  - Token type: {token.get('token_type', 'Bearer')}")
        if 'expires_in' in token:
            print(f"  - Expires in: {token['expires_in']} seconds")
        if 'refresh_token' in token:
            print(f"  - Refresh token: {token['refresh_token'][:20]}...")
        print()
        print(f"Token saved to: {schwab_client.token_file}")
        print()
        print("[SUCCESS] Authentication complete!")
        print()
        print("You can now use the Schwab API. The token will be automatically")
        print("refreshed when it expires.")
        print()
        print("Next steps:")
        print("  1. Run data ingestion:")
        print("     uv run python backend/jobs/data_ingestion.py --tickers AAPL --days 7")
        print()

    except SchwabAPIError as e:
        print(f"[ERROR] Authentication failed: {e}")
        print()
        print("Common issues:")
        print("  - Make sure the authorization code is correct and not expired")
        print("  - Check that your callback URL matches your Schwab app settings")
        print("  - Verify your API key and secret are correct in .env")
        print()
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")


if __name__ == "__main__":
    asyncio.run(main())

"""Quick Schwab OAuth - Run this directly and paste code immediately!"""
import sys
import os
from pathlib import Path

BACKEND_PATH = Path(__file__).parent / "backend"
sys.path.insert(0, str(BACKEND_PATH))

import asyncio
from app.services.schwab_client import schwab_client

AUTH_URL = f"https://api.schwabapi.com/v1/oauth/authorize?response_type=code&client_id={schwab_client.api_key}&redirect_uri={schwab_client.callback_url}&scope=readonly"

async def main():
    print("=" * 70)
    print("Schwab OAuth - Quick Authentication")
    print("=" * 70)
    print()
    print("STEP 1: Open this URL in your browser:")
    print(AUTH_URL)
    print()
    print("STEP 2: After authorizing, paste the FULL redirect URL below")
    print("Example: https://127.0.0.1:8000/auth/callback?code=ABC123&session=xyz")
    print()

    redirect_url = input("Paste redirect URL: ").strip()

    # Extract code from URL
    if "code=" in redirect_url:
        from urllib.parse import unquote
        code_start = redirect_url.find("code=") + 5
        code_end = redirect_url.find("&", code_start)
        if code_end == -1:
            code = redirect_url[code_start:]
        else:
            code = redirect_url[code_start:code_end]

        # URL-decode the code (convert %40 to @, etc.)
        code = unquote(code)

        print()
        print(f"Extracted code: {code[:30]}...")
        print("Exchanging for token...")
        print()

        try:
            token = await schwab_client.exchange_code_for_token(code)
            print("[SUCCESS] Authentication complete!")
            print(f"  Token saved to: {schwab_client.token_file}")
            print(f"  Expires in: {token['expires_in']} seconds")
            print()
            print("Test it now:")
            print("  uv run python backend/jobs/data_ingestion.py --tickers AAPL --days 7")
        except Exception as e:
            print(f"[ERROR] {e}")
    else:
        print("[ERROR] No code found in URL")

if __name__ == "__main__":
    asyncio.run(main())

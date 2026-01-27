# Schwab API Setup Guide

Complete guide for setting up the Charles Schwab Developer API for production market data.

## Prerequisites

- ✅ Schwab Developer account approved
- ✅ Schwab Developer App created
- ✅ App Key (Client ID) and App Secret received

## Step 1: Configure Your Schwab App

1. Log in to [Schwab Developer Portal](https://developer.schwab.com/)
2. Navigate to your application
3. Configure the **Callback URL** (Redirect URI):
   ```
   http://localhost:8000/auth/callback
   ```
   **Important:** This must match exactly with what's in your `.env` file

4. Note your credentials:
   - **App Key** (also called Consumer Key or Client ID)
   - **App Secret** (also called Consumer Secret or Client Secret)

## Step 2: Add Credentials to .env

Update your `.env` file with your Schwab credentials:

```env
# Schwab API
SCHWAB_API_KEY=your_app_key_here
SCHWAB_API_SECRET=your_app_secret_here
SCHWAB_CALLBACK_URL=http://localhost:8000/auth/callback
```

**Security Note:** Never commit the `.env` file or share your credentials.

## Step 3: Complete OAuth Authentication

Run the OAuth helper script to get your access token:

```bash
uv run python scripts/schwab_oauth.py
```

This script will:
1. Generate an authorization URL
2. Prompt you to visit the URL and authorize your app
3. Ask you to paste the authorization code
4. Exchange the code for an access token
5. Save the token to `.schwab_tokens.json`

### OAuth Flow Details

1. **Visit Authorization URL**
   - The script will print a URL starting with `https://api.schwabapi.com/v1/oauth/authorize`
   - Open this URL in your browser

2. **Log In to Schwab**
   - You'll be redirected to Schwab's login page
   - Log in with your Schwab credentials (not your developer account)

3. **Authorize the Application**
   - Schwab will ask you to authorize your app
   - Click "Allow" or "Authorize"

4. **Copy Authorization Code**
   - You'll be redirected to: `http://localhost:8000/auth/callback?code=AUTHORIZATION_CODE`
   - The page may show an error (that's okay if you don't have the backend running)
   - Copy the `code` parameter from the URL
   - Example: If the URL is `http://localhost:8000/auth/callback?code=abc123xyz`, copy `abc123xyz`

5. **Paste Code into Script**
   - Return to the terminal where the script is running
   - Paste the authorization code when prompted
   - Press Enter

6. **Token Saved**
   - The script will exchange the code for an access token
   - Token is saved to `.schwab_tokens.json` (automatically ignored by git)
   - You're now authenticated!

## Step 4: Test the Connection

Test that everything is working:

```bash
# Fetch 7 days of price data for AAPL
uv run python backend/jobs/data_ingestion.py --tickers AAPL --days 7
```

If successful, you'll see:
```
[DATA_INGESTION] Starting market data ingestion
[DATA_INGESTION] Using provider: schwab
[SCHWAB] Fetching price history for AAPL
[OK] Fetched 7 days of data for AAPL
```

## Token Management

### Token Expiration

- Access tokens expire after a certain period (check your token response)
- The client automatically refreshes tokens using the refresh token
- Refresh tokens are long-lived but can expire

### Token Storage

- Tokens are stored in `.schwab_tokens.json` in the project root
- This file is automatically ignored by git
- **Do not share this file** - it contains sensitive credentials

### Re-authentication

If your tokens expire or become invalid:

```bash
# Re-run the OAuth flow
uv run python scripts/schwab_oauth.py
```

## API Endpoints Available

### 1. Price History

Get historical OHLCV data:

```python
from backend.app.services.schwab_client import schwab_client

# Get daily price history
candles = await schwab_client.get_price_history_daily(
    symbol="AAPL",
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now()
)

# Get custom frequency
response = await schwab_client.get_price_history(
    symbol="AAPL",
    period_type="month",
    period=1,
    frequency_type="daily",
    frequency=1
)
```

### 2. Real-Time Quotes

Get current price data:

```python
quote = await schwab_client.get_quote("AAPL")
```

### 3. Instrument Search

Search for symbols:

```python
results = await schwab_client.get_instruments("AAPL", projection="symbol-search")
```

## Schwab API vs yfinance

| Feature | Schwab API | yfinance |
|---------|-----------|----------|
| **Data Source** | Official Schwab data | Yahoo Finance (unofficial) |
| **Data Delay** | Real-time (market data) | 15-20 min delay |
| **Reliability** | High (official API) | Medium (web scraping) |
| **Rate Limits** | Yes (documented) | Yes (undocumented) |
| **Authentication** | OAuth 2.0 required | None |
| **Cost** | Free | Free |
| **Best For** | Production | Development/testing |

The platform automatically uses **yfinance** for development when Schwab credentials are not configured, and switches to **Schwab API** when credentials are detected.

## Troubleshooting

### Issue: "Not authenticated" Error

**Solution:** Run the OAuth flow:
```bash
uv run python scripts/schwab_oauth.py
```

### Issue: "Invalid callback URL" Error

**Solution:** Ensure your Schwab app's callback URL matches your `.env`:
- Schwab app: `http://localhost:8000/auth/callback`
- .env: `SCHWAB_CALLBACK_URL=http://localhost:8000/auth/callback`

### Issue: "Invalid client credentials" Error

**Solution:** Double-check your API key and secret in `.env`:
- Make sure there are no extra spaces
- Verify the credentials match your Schwab Developer app

### Issue: Token Expired

**Solution:** Tokens are automatically refreshed. If refresh fails, re-run OAuth:
```bash
# Delete old tokens
rm .schwab_tokens.json

# Re-authenticate
uv run python scripts/schwab_oauth.py
```

### Issue: "HTTP 429 Too Many Requests"

**Solution:** You've hit rate limits. Wait and try again later. Consider:
- Reducing API call frequency
- Implementing request caching
- Using batch requests where possible

## Rate Limits

Schwab API has rate limits (exact limits depend on your account tier):
- **Requests per second**: Check your developer portal
- **Requests per day**: Check your developer portal

The client implements:
- Automatic retry with exponential backoff
- Error handling for rate limit responses
- Request caching (future enhancement)

## Production Considerations

### 1. Token Security

For production deployments:
- **Do not store tokens in files** - use a secure secret manager
- Consider using environment variables or encrypted storage
- Implement token rotation policies

### 2. Error Handling

The client handles common errors:
- Token expiration (automatic refresh)
- Rate limiting (with backoff)
- Network errors (with retry)
- Invalid symbols (clear error messages)

### 3. Monitoring

Monitor your API usage:
- Log all API calls
- Track rate limit headers
- Alert on authentication failures
- Monitor token expiration

## Support

- **Schwab Developer Documentation**: https://developer.schwab.com/
- **API Status**: Check developer portal for outages
- **Issues**: Create an issue in this repository

## Next Steps

Once authenticated:
1. ✅ Test data ingestion with Schwab API
2. Fetch historical data for all seeded tickers
3. Proceed to Phase 1C: Analytics Service
4. Build Streamlit dashboard with real-time data

---

**Last Updated**: 2026-01-27

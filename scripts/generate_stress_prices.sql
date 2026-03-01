-- Generate synthetic price data for stress testing.
-- Creates 30 days of fake OHLCV data for all active tickers.
-- 30 days is enough for most technical indicators (SMA20, RSI14, etc.)

INSERT INTO price_data (ticker, timestamp, open, high, low, close, volume, adjusted_close)
SELECT
    t.ticker,
    d.ts,
    -- Deterministic but varied prices based on ticker hash
    100.0 + (abs(hashtext(t.ticker)) % 900) + (random() * 5 - 2.5),
    100.0 + (abs(hashtext(t.ticker)) % 900) + (random() * 5),
    100.0 + (abs(hashtext(t.ticker)) % 900) - (random() * 5),
    100.0 + (abs(hashtext(t.ticker)) % 900) + (random() * 3 - 1.5),
    (abs(hashtext(t.ticker)) % 10000000 + 100000)::bigint,
    100.0 + (abs(hashtext(t.ticker)) % 900) + (random() * 3 - 1.5)
FROM tickers t
CROSS JOIN (
    SELECT generate_series(
        NOW() - INTERVAL '30 days',
        NOW(),
        INTERVAL '1 day'
    ) AS ts
) d
WHERE t.is_active = true
ON CONFLICT (ticker, timestamp) DO NOTHING;

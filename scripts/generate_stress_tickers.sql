-- Generate ~4,000 synthetic tickers for stress testing fan-out.
-- Uses letter combinations to create realistic-looking ticker symbols.
-- This is additive — existing real tickers (AAPL, MSFT, etc.) are preserved.

INSERT INTO tickers (ticker, name, asset_type, sector, industry, market_cap_category, exchange, is_active)
SELECT
    symbol,
    'Stress Test Corp ' || symbol,
    'STOCK',
    CASE (row_number() OVER (ORDER BY symbol)) % 5
        WHEN 0 THEN 'Technology'
        WHEN 1 THEN 'Finance'
        WHEN 2 THEN 'Healthcare'
        WHEN 3 THEN 'Energy'
        WHEN 4 THEN 'Consumer Cyclical'
    END,
    'Stress Test Industry',
    CASE (row_number() OVER (ORDER BY symbol)) % 3
        WHEN 0 THEN 'LARGE'
        WHEN 1 THEN 'MID'
        WHEN 2 THEN 'SMALL'
    END,
    CASE (row_number() OVER (ORDER BY symbol)) % 2
        WHEN 0 THEN 'NYSE'
        WHEN 1 THEN 'NASDAQ'
    END,
    true
FROM (
    -- Generate 4-letter symbols: AA00 through ZZ99 style, but letters only
    -- Using 2-letter prefix + 2-letter suffix = 26*26*26 = 17,576 possible
    -- We limit to ~4,000 with LIMIT
    SELECT
        chr(65 + (n / 26 / 26) % 26) ||
        chr(65 + (n / 26) % 26) ||
        chr(65 + n % 26) AS symbol
    FROM generate_series(0, 17575) AS n
    ORDER BY 1
    LIMIT 4000
) AS syms
ON CONFLICT (ticker) DO NOTHING;

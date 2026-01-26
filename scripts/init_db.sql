-- Database initialization script for Market Intelligence Platform
-- This script sets up PostgreSQL + TimescaleDB and creates all necessary tables

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create core tables (already managed by SQLAlchemy, but included here for reference)

-- Portfolios table
CREATE TABLE IF NOT EXISTS portfolios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Holdings table
CREATE TABLE IF NOT EXISTS holdings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID REFERENCES portfolios(id) ON DELETE CASCADE,
    ticker VARCHAR(20) NOT NULL,
    quantity DECIMAL(18, 8) NOT NULL,
    cost_basis DECIMAL(18, 2) NOT NULL,
    purchase_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_portfolio_ticker ON holdings(portfolio_id, ticker);

-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID REFERENCES portfolios(id) ON DELETE CASCADE,
    ticker VARCHAR(20) NOT NULL,
    transaction_type VARCHAR(10) NOT NULL CHECK (transaction_type IN ('BUY', 'SELL')),
    quantity DECIMAL(18, 8) NOT NULL,
    price DECIMAL(18, 2) NOT NULL,
    transaction_date TIMESTAMP WITH TIME ZONE NOT NULL,
    fees DECIMAL(18, 2) DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_portfolio_date ON transactions(portfolio_id, transaction_date);

-- Tickers table
CREATE TABLE IF NOT EXISTS tickers (
    ticker VARCHAR(20) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    asset_type VARCHAR(20) NOT NULL CHECK (asset_type IN ('STOCK', 'ETF', 'CRYPTO')),
    sector VARCHAR(100),
    industry VARCHAR(100),
    market_cap_category VARCHAR(20) CHECK (market_cap_category IN ('LARGE', 'MID', 'SMALL', 'MICRO')),
    exchange VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Time-series tables (to be converted to hypertables)

-- Price data table
CREATE TABLE IF NOT EXISTS price_data (
    ticker VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    open DECIMAL(18, 4),
    high DECIMAL(18, 4),
    low DECIMAL(18, 4),
    close DECIMAL(18, 4),
    volume BIGINT,
    adjusted_close DECIMAL(18, 4),
    PRIMARY KEY (ticker, timestamp)
);

-- Convert to hypertable (only if not already a hypertable)
SELECT create_hypertable('price_data', 'timestamp',
    if_not_exists => TRUE,
    chunk_time_interval => INTERVAL '7 days'
);

CREATE INDEX IF NOT EXISTS idx_price_ticker_time ON price_data(ticker, timestamp DESC);

-- Technical indicators table
CREATE TABLE IF NOT EXISTS technical_indicators (
    ticker VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    indicator_name VARCHAR(50) NOT NULL,
    value DECIMAL(18, 6),
    metadata JSONB,
    PRIMARY KEY (ticker, timestamp, indicator_name)
);

-- Convert to hypertable
SELECT create_hypertable('technical_indicators', 'timestamp',
    if_not_exists => TRUE,
    chunk_time_interval => INTERVAL '7 days'
);

CREATE INDEX IF NOT EXISTS idx_indicator_ticker_name ON technical_indicators(ticker, indicator_name, timestamp DESC);

-- Fundamental metrics table
CREATE TABLE IF NOT EXISTS fundamental_metrics (
    ticker VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    metric_name VARCHAR(50) NOT NULL,
    value DECIMAL(18, 6),
    period VARCHAR(20),
    source VARCHAR(50),
    PRIMARY KEY (ticker, timestamp, metric_name)
);

-- Convert to hypertable
SELECT create_hypertable('fundamental_metrics', 'timestamp',
    if_not_exists => TRUE,
    chunk_time_interval => INTERVAL '30 days'
);

-- Opportunity scores table
CREATE TABLE IF NOT EXISTS opportunity_scores (
    ticker VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    overall_score DECIMAL(5, 2) NOT NULL CHECK (overall_score >= 0 AND overall_score <= 100),
    confidence_level DECIMAL(5, 2) NOT NULL CHECK (confidence_level >= 0 AND confidence_level <= 100),
    component_scores JSONB NOT NULL,
    explanation JSONB NOT NULL,
    bull_case DECIMAL(5, 2),
    base_case DECIMAL(5, 2),
    bear_case DECIMAL(5, 2),
    PRIMARY KEY (ticker, timestamp)
);

-- Convert to hypertable
SELECT create_hypertable('opportunity_scores', 'timestamp',
    if_not_exists => TRUE,
    chunk_time_interval => INTERVAL '7 days'
);

CREATE INDEX IF NOT EXISTS idx_opportunity_score ON opportunity_scores(timestamp DESC, overall_score DESC);

-- Alerts table
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker VARCHAR(20) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('INFO', 'MEDIUM', 'HIGH')),
    message TEXT NOT NULL,
    metadata JSONB,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alerts_unread ON alerts(created_at DESC, is_read);

-- Create retention policies for hypertables (optional - keeps data for 2 years)
-- Uncomment if you want automatic data retention

-- SELECT add_retention_policy('price_data', INTERVAL '2 years', if_not_exists => TRUE);
-- SELECT add_retention_policy('technical_indicators', INTERVAL '2 years', if_not_exists => TRUE);
-- SELECT add_retention_policy('fundamental_metrics', INTERVAL '2 years', if_not_exists => TRUE);
-- SELECT add_retention_policy('opportunity_scores', INTERVAL '2 years', if_not_exists => TRUE);

-- Create continuous aggregates for common queries (optional - improves performance)
-- Example: Daily OHLCV aggregates

-- CREATE MATERIALIZED VIEW IF NOT EXISTS price_data_daily
-- WITH (timescaledb.continuous) AS
-- SELECT
--     ticker,
--     time_bucket('1 day', timestamp) AS day,
--     first(open, timestamp) AS open,
--     max(high) AS high,
--     min(low) AS low,
--     last(close, timestamp) AS close,
--     sum(volume) AS volume
-- FROM price_data
-- GROUP BY ticker, day;

COMMIT;

/**
 * TypeScript type definitions for Market Intelligence Dashboard
 */

// Portfolio types

export interface Portfolio {
  id: string
  name: string
  description?: string
  created_at: string
  updated_at: string
}

export interface Holding {
  id: string
  portfolio_id: string
  ticker: string
  quantity: number
  cost_basis: number
  purchase_date: string
  created_at: string
  updated_at: string
}

export interface Transaction {
  id: string
  portfolio_id: string
  ticker: string
  transaction_type: 'BUY' | 'SELL'
  quantity: number
  price: number
  transaction_date: string
  fees: number
  notes?: string
  created_at: string
}

// Ticker types

export interface Ticker {
  ticker: string
  name: string
  asset_type: 'STOCK' | 'ETF' | 'CRYPTO'
  sector?: string
  industry?: string
  market_cap_category?: 'LARGE' | 'MID' | 'SMALL' | 'MICRO'
  exchange?: string
  is_active: boolean
}

export interface PriceData {
  ticker: string
  timestamp: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  adjusted_close: number
}

// Opportunity types

export interface OpportunityScore {
  ticker: string
  timestamp: string
  overall_score: number
  confidence_level: number
  component_scores: ComponentScores
  explanation: Explanation
  bull_case: number
  base_case: number
  bear_case: number
}

export interface ComponentScores {
  momentum: ComponentDetail
  valuation_divergence: ComponentDetail
  growth_acceleration: ComponentDetail
  relative_strength: ComponentDetail
  sector_momentum: ComponentDetail
}

export interface ComponentDetail {
  score: number
  weight: number
  contribution: number
  details: Record<string, DetailItem>
}

export interface DetailItem {
  value: number
  reason: string
}

export interface Explanation {
  ticker: string
  overall_score: number
  confidence: number
  components: ComponentScores
  scenarios: {
    bull: number
    base: number
    bear: number
  }
  key_drivers: string[]
  risks: string[]
}

// Alert types

export interface Alert {
  id: string
  ticker: string
  alert_type: string
  severity: 'INFO' | 'MEDIUM' | 'HIGH'
  message: string
  metadata?: Record<string, any>
  is_read: boolean
  created_at: string
}

// Analytics types

export interface PortfolioAnalytics {
  total_value: number
  total_cost: number
  total_return: number
  total_return_percent: number
  daily_pl: number
  daily_pl_percent: number
  allocations: {
    by_sector: AllocationItem[]
    by_market_cap: AllocationItem[]
    by_asset_type: AllocationItem[]
  }
  risk_metrics: RiskMetrics
}

export interface AllocationItem {
  label: string
  value: number
  percentage: number
}

export interface RiskMetrics {
  volatility: number
  beta: number
  sharpe_ratio: number
  max_drawdown: number
}

// API Response types

export interface ApiResponse<T> {
  data: T
  error?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
}

/**
 * API client for Market Intelligence Dashboard
 * Handles all communication with the backend API
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export class APIError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'APIError'
  }
}

async function fetchAPI<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`

  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new APIError(response.status, error.detail || 'An error occurred')
  }

  return response.json()
}

// Portfolio APIs

export const portfolioAPI = {
  list: () => fetchAPI<{ portfolios: any[]; total: number }>('/api/portfolios'),

  get: (id: string) => fetchAPI<any>(`/api/portfolios/${id}`),

  create: (data: { name: string; description?: string }) =>
    fetchAPI<any>('/api/portfolios', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (id: string, data: { name?: string; description?: string }) =>
    fetchAPI<any>(`/api/portfolios/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  delete: (id: string) =>
    fetchAPI<void>(`/api/portfolios/${id}`, { method: 'DELETE' }),

  // Holdings
  listHoldings: (portfolioId: string) =>
    fetchAPI<{ holdings: any[]; total: number }>(`/api/portfolios/${portfolioId}/holdings`),

  createHolding: (portfolioId: string, data: any) =>
    fetchAPI<any>(`/api/portfolios/${portfolioId}/holdings`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  updateHolding: (holdingId: string, data: any) =>
    fetchAPI<any>(`/api/portfolios/holdings/${holdingId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  deleteHolding: (holdingId: string) =>
    fetchAPI<void>(`/api/portfolios/holdings/${holdingId}`, { method: 'DELETE' }),

  // Transactions
  listTransactions: (portfolioId: string) =>
    fetchAPI<{ transactions: any[]; total: number }>(`/api/portfolios/${portfolioId}/transactions`),

  createTransaction: (portfolioId: string, data: any) =>
    fetchAPI<any>(`/api/portfolios/${portfolioId}/transactions`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
}

// Ticker APIs (to be implemented)

export const tickerAPI = {
  get: (symbol: string) => fetchAPI<any>(`/api/tickers/${symbol}`),

  getHistory: (symbol: string, params?: { start_date?: string; end_date?: string }) => {
    const queryParams = new URLSearchParams(params as any).toString()
    return fetchAPI<any>(`/api/tickers/${symbol}/history?${queryParams}`)
  },

  getIndicators: (symbol: string) =>
    fetchAPI<any>(`/api/tickers/${symbol}/indicators`),

  getFundamentals: (symbol: string) =>
    fetchAPI<any>(`/api/tickers/${symbol}/fundamentals`),
}

// Opportunity APIs (to be implemented)

export const opportunityAPI = {
  list: (params?: { min_score?: number; min_confidence?: number }) => {
    const queryParams = new URLSearchParams(params as any).toString()
    return fetchAPI<any>(`/api/opportunities?${queryParams}`)
  },

  get: (symbol: string) => fetchAPI<any>(`/api/opportunities/${symbol}`),
}

// Alert APIs (to be implemented)

export const alertAPI = {
  list: (params?: { is_read?: boolean; severity?: string }) => {
    const queryParams = new URLSearchParams(params as any).toString()
    return fetchAPI<any>(`/api/alerts?${queryParams}`)
  },

  markAsRead: (id: string) =>
    fetchAPI<any>(`/api/alerts/${id}/read`, { method: 'PUT' }),
}

'use client'

import { useState, useEffect } from 'react'
import { portfolioAPI } from '@/lib/api'
import type { Portfolio } from '@/lib/types'

export default function PortfolioPage() {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newPortfolio, setNewPortfolio] = useState({ name: '', description: '' })

  // Fetch portfolios on mount
  useEffect(() => {
    fetchPortfolios()
  }, [])

  async function fetchPortfolios() {
    try {
      setLoading(true)
      const data = await portfolioAPI.list()
      setPortfolios(data.portfolios)
    } catch (err: any) {
      setError(err.message || 'Failed to fetch portfolios')
    } finally {
      setLoading(false)
    }
  }

  async function handleCreatePortfolio(e: React.FormEvent) {
    e.preventDefault()
    try {
      await portfolioAPI.create(newPortfolio)
      setShowCreateModal(false)
      setNewPortfolio({ name: '', description: '' })
      fetchPortfolios()
    } catch (err: any) {
      alert(err.message || 'Failed to create portfolio')
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading portfolios...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="card max-w-2xl mx-auto">
        <div className="text-danger mb-4">{error}</div>
        <button onClick={fetchPortfolios} className="btn-primary">
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Portfolios</h1>
          <p className="text-gray-600 mt-1">Manage your investment portfolios</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn-primary"
        >
          + Create Portfolio
        </button>
      </div>

      {/* Portfolio list */}
      {portfolios.length === 0 ? (
        <div className="card text-center py-12">
          <svg
            className="mx-auto h-12 w-12 text-gray-400 mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
            />
          </svg>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No portfolios yet</h3>
          <p className="text-gray-600 mb-4">
            Get started by creating your first portfolio
          </p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn-primary"
          >
            Create Portfolio
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {portfolios.map((portfolio) => (
            <div key={portfolio.id} className="card hover:shadow-md transition-shadow cursor-pointer">
              <div className="flex items-start justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">{portfolio.name}</h3>
                <span className="text-xs text-gray-500">
                  {new Date(portfolio.created_at).toLocaleDateString()}
                </span>
              </div>
              {portfolio.description && (
                <p className="text-sm text-gray-600 mb-4">{portfolio.description}</p>
              )}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <div className="text-gray-500">Value</div>
                  <div className="font-semibold">$0.00</div>
                </div>
                <div>
                  <div className="text-gray-500">Return</div>
                  <div className="font-semibold">0.00%</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Portfolio Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Create Portfolio</h2>
            <form onSubmit={handleCreatePortfolio}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Name
                </label>
                <input
                  type="text"
                  value={newPortfolio.name}
                  onChange={(e) =>
                    setNewPortfolio({ ...newPortfolio, name: e.target.value })
                  }
                  className="input w-full"
                  placeholder="My Portfolio"
                  required
                />
              </div>
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description (optional)
                </label>
                <textarea
                  value={newPortfolio.description}
                  onChange={(e) =>
                    setNewPortfolio({ ...newPortfolio, description: e.target.value })
                  }
                  className="input w-full"
                  rows={3}
                  placeholder="Long-term growth portfolio"
                />
              </div>
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

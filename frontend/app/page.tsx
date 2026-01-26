import Link from 'next/link'

export default function Home() {
  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Welcome to Market Intelligence Dashboard
        </h1>
        <p className="text-gray-600">
          Your personal investment intelligence platform for portfolio analytics and opportunity identification
        </p>
      </div>

      {/* Quick stats cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="card">
          <div className="text-sm text-gray-600 mb-1">Total Portfolio Value</div>
          <div className="text-2xl font-bold text-gray-900">$0.00</div>
          <div className="text-sm text-gray-500 mt-1">No portfolios yet</div>
        </div>

        <div className="card">
          <div className="text-sm text-gray-600 mb-1">Total Return</div>
          <div className="text-2xl font-bold text-gray-900">$0.00</div>
          <div className="text-sm text-gray-500 mt-1">0.00%</div>
        </div>

        <div className="card">
          <div className="text-sm text-gray-600 mb-1">Opportunities</div>
          <div className="text-2xl font-bold text-gray-900">0</div>
          <div className="text-sm text-gray-500 mt-1">High-confidence</div>
        </div>

        <div className="card">
          <div className="text-sm text-gray-600 mb-1">Unread Alerts</div>
          <div className="text-2xl font-bold text-gray-900">0</div>
          <div className="text-sm text-gray-500 mt-1">Last 24 hours</div>
        </div>
      </div>

      {/* Getting started section */}
      <div className="card mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Getting Started</h2>
        <div className="space-y-4">
          <div className="flex items-start">
            <div className="flex-shrink-0 w-8 h-8 bg-primary text-white rounded-full flex items-center justify-center font-semibold mr-3">
              1
            </div>
            <div>
              <h3 className="font-medium text-gray-900">Create a Portfolio</h3>
              <p className="text-sm text-gray-600 mt-1">
                Start by creating your first portfolio to track your investments
              </p>
              <Link href="/portfolio" className="text-primary hover:text-primary-600 text-sm mt-2 inline-block">
                Create Portfolio →
              </Link>
            </div>
          </div>

          <div className="flex items-start">
            <div className="flex-shrink-0 w-8 h-8 bg-gray-300 text-gray-700 rounded-full flex items-center justify-center font-semibold mr-3">
              2
            </div>
            <div>
              <h3 className="font-medium text-gray-900">Add Holdings</h3>
              <p className="text-sm text-gray-600 mt-1">
                Add your current stock positions with cost basis and quantity
              </p>
            </div>
          </div>

          <div className="flex items-start">
            <div className="flex-shrink-0 w-8 h-8 bg-gray-300 text-gray-700 rounded-full flex items-center justify-center font-semibold mr-3">
              3
            </div>
            <div>
              <h3 className="font-medium text-gray-900">Explore Opportunities</h3>
              <p className="text-sm text-gray-600 mt-1">
                Browse the opportunity radar for high-confidence 10x opportunities
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Feature highlights */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <div className="text-lg font-semibold text-gray-900 mb-2">Portfolio Analytics</div>
          <p className="text-sm text-gray-600">
            Track performance, P&L, returns (TWR/MWR), allocations, and risk metrics
          </p>
        </div>

        <div className="card">
          <div className="text-lg font-semibold text-gray-900 mb-2">10x Opportunity Scoring</div>
          <p className="text-sm text-gray-600">
            Rule-based scoring with full explainability for identifying high-potential investments
          </p>
        </div>

        <div className="card">
          <div className="text-lg font-semibold text-gray-900 mb-2">Technical Signals</div>
          <p className="text-sm text-gray-600">
            Automated calculation of moving averages, RSI, MACD, and volume analysis
          </p>
        </div>
      </div>
    </div>
  )
}

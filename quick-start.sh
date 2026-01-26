#!/bin/bash
# Quick Start Script for Market Intelligence Dashboard
# This script helps you get the platform running locally

set -e

echo "🚀 Market Intelligence Dashboard - Quick Start"
echo "================================================"
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker Desktop."
    exit 1
fi
echo "✅ Docker found"

# Check kubectl
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed. Please enable Kubernetes in Docker Desktop."
    exit 1
fi
echo "✅ kubectl found"

# Check Kubernetes is running
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Kubernetes is not running. Please enable it in Docker Desktop."
    exit 1
fi
echo "✅ Kubernetes is running"

echo ""
echo "📦 Step 1: Building Jobs Container"
echo "-----------------------------------"
cd kubernetes
chmod +x build-jobs.sh
./build-jobs.sh latest
cd ..

echo ""
echo "🗄️  Step 2: Starting Database"
echo "-----------------------------------"
docker run -d --name market-db \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=market_intelligence \
  timescale/timescaledb:latest-pg15 || echo "Database already running"

echo "Waiting for database to start..."
sleep 10

echo "Initializing database schema..."
docker exec -i market-db psql -U postgres -d market_intelligence < scripts/init_db.sql

echo ""
echo "🌪️  Step 3: Starting Airflow"
echo "-----------------------------------"
cd airflow

# Create .env file
if [ ! -f .env ]; then
    echo "AIRFLOW_UID=50000" > .env
fi

echo "Starting Airflow services..."
docker-compose up -d

echo "Waiting for Airflow to start..."
sleep 30

echo ""
echo "✅ Setup Complete!"
echo "=================="
echo ""
echo "🌐 Access Points:"
echo "  - Airflow UI:    http://localhost:8080 (airflow/airflow)"
echo "  - API Docs:      http://localhost:8000/docs (when backend is running)"
echo "  - Frontend:      http://localhost:3000 (when frontend is running)"
echo ""
echo "📝 Next Steps:"
echo "  1. Configure Airflow variables at http://localhost:8080/variable/list/"
echo "     - database_url = postgresql://postgres:password@host.docker.internal:5432/market_intelligence"
echo "     - schwab_api_key = your_api_key"
echo "     - schwab_api_secret = your_api_secret"
echo ""
echo "  2. Enable DAGs in Airflow UI"
echo ""
echo "  3. Start the backend:"
echo "     cd backend"
echo "     uv run uvicorn app.main:app --reload --port 8000"
echo ""
echo "  4. Start the frontend:"
echo "     cd frontend"
echo "     npm install"
echo "     npm run dev"
echo ""
echo "📖 For more details, see:"
echo "  - README.md"
echo "  - AIRFLOW_SETUP.md"

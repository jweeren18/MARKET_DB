"""
FastAPI application entry point for Market Intelligence Platform.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.config import settings
from app.database import init_db

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Market Intelligence API",
    description="Personal investment intelligence platform for portfolio analytics and opportunity identification",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Starting Market Intelligence API...")

    # Initialize database tables
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Market Intelligence API...")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Market Intelligence API",
        "version": "0.1.0",
        "environment": settings.env,
    }


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "message": "Welcome to Market Intelligence API",
        "docs": "/docs",
        "health": "/health",
    }


# Import and include API routers
from app.api import portfolio

app.include_router(portfolio.router, prefix="/api/portfolios", tags=["portfolios"])

# Additional routers to be added:
# from app.api import market_data, analytics, opportunities
# app.include_router(market_data.router, prefix="/api/tickers", tags=["tickers"])
# app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
# app.include_router(opportunities.router, prefix="/api/opportunities", tags=["opportunities"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.backend_port,
        reload=settings.env == "development",
    )

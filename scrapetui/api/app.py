"""FastAPI application for WebScrape-TUI REST API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..config import get_config
from ..core.database import init_db, check_database_exists
from ..core.auth import cleanup_expired_sessions
from ..utils.logging import get_logger
from .middleware import RateLimitMiddleware, RequestLoggingMiddleware, ErrorHandlingMiddleware

# Import routers (will be created)
from .routers import articles, scrapers, users, tags, ai
from . import auth

logger = get_logger(__name__)
config = get_config()

# Create FastAPI app
app = FastAPI(
    title="WebScrape-TUI API",
    description="REST API for web scraping, article management, and AI-powered content analysis. "
                "Supports multi-user authentication, RBAC, advanced AI features, and background tasks.",
    version="2.2.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    contact={
        "name": "WebScrape-TUI",
        "url": "https://github.com/doublegate/WebScrape-TUI"
    },
    license_info={
        "name": "MIT",
    }
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on config.api_cors_origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    RateLimitMiddleware,
    max_requests=config.api_rate_limit_per_minute,
    window_seconds=60
)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Starting WebScrape-TUI API server...")

    # Initialize database if needed
    if not check_database_exists():
        logger.info("Database not found, initializing...")
        init_db()
    else:
        logger.info("Database found, checking schema...")
        # Ensure schema is up to date (migrations handled in init_db)
        try:
            init_db()
        except Exception as e:
            logger.warning(f"Schema initialization skipped: {e}")

    # Clean up expired sessions
    cleanup_expired_sessions()

    logger.info("API server startup complete")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down WebScrape-TUI API server...")
    cleanup_expired_sessions()
    logger.info("API server shutdown complete")


# Register routers (v1 API)
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(articles.router, prefix="/api/v1/articles", tags=["Articles"])
app.include_router(scrapers.router, prefix="/api/v1/scrapers", tags=["Scrapers"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(tags.router, prefix="/api/v1/tags", tags=["Tags"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["AI Features"])

# Legacy routes (no version prefix for backward compatibility)
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication (Legacy)"], include_in_schema=False)
app.include_router(articles.router, prefix="/api/articles", tags=["Articles (Legacy)"], include_in_schema=False)
app.include_router(scrapers.router, prefix="/api/scrapers", tags=["Scrapers (Legacy)"], include_in_schema=False)
app.include_router(users.router, prefix="/api/users", tags=["Users (Legacy)"], include_in_schema=False)
app.include_router(tags.router, prefix="/api/tags", tags=["Tags (Legacy)"], include_in_schema=False)
app.include_router(ai.router, prefix="/api/ai", tags=["AI (Legacy)"], include_in_schema=False)


# Root endpoint
@app.get("/")
async def root():
    """API root endpoint with version information."""
    return {
        "name": "WebScrape-TUI API",
        "version": "2.2.0",
        "api_version": "v1",
        "description": "REST API for web scraping, article management, and AI-powered content analysis",
        "features": [
            "Multi-user authentication with RBAC",
            "Advanced AI features (NER, Q&A, topic modeling, similarity search)",
            "Background task processing",
            "Rate limiting (100 req/min standard, 10 req/min AI endpoints)"
        ],
        "documentation": {
            "swagger": "/api/docs",
            "redoc": "/api/redoc",
            "openapi_json": "/api/openapi.json"
        },
        "endpoints": {
            "v1": "/api/v1",
            "legacy": "/api"
        }
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check database connection
        from ..core.database import get_db_connection
        with get_db_connection() as conn:
            conn.execute("SELECT 1").fetchone()

        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


# Main entry point for running with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "scrapetui.api.app:app",
        host=config.api_host,
        port=config.api_port,
        reload=True,
        log_level="info"
    )

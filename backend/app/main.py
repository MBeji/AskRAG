import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# Rate Limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
# from app.core.security import SecurityMiddleware # Custom security middleware if any
from app.api.v1.api import api_router
from app.db.connection import init_db, close_db_connection

# Configure logging
logging.basicConfig(level=settings.LOG_LEVEL.upper(), format=settings.LOG_FORMAT)
logger = logging.getLogger(__name__)

# Initialize Rate Limiter using settings from config.py
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.DEFAULT_RATE_LIMIT])

@asynccontextmanager
async def lifespan(app_instance: FastAPI): # Renamed app to app_instance to avoid type hint conflict
    # Startup
    logger.info("AskRAG API starting up...")
    try:
        await init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        # raise e
    yield
    # Shutdown
    logger.info("AskRAG API shutting down...")
    await close_db_connection()
    logger.info("Database connection closed.")

# Create FastAPI instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="RAG (Retrieval-Augmented Generation) API for document-based Q&A",
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Add Rate Limiter state and exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Import and add SecurityHeadersMiddleware
from app.core.security import SecurityHeadersMiddleware
app.add_middleware(SecurityHeadersMiddleware)

# Set up CORS
if settings.BACKEND_CORS_ORIGINS: # This uses the property method from config.py
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS, # Already a List[str]
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add other custom security middleware if needed (e.g., from app.core.security)
# Example: from app.core.security import SecurityHeadersMiddleware
# app.add_middleware(SecurityHeadersMiddleware)


# Add trusted host middleware for production
# Ensure TRUSTED_HOSTS is defined in config.py and loaded correctly if this is used.
# if settings.ENVIRONMENT == "production" and settings.TRUSTED_HOSTS:
#     app.add_middleware(
#         TrustedHostMiddleware,
#         allowed_hosts=settings.TRUSTED_HOSTS
#     )

# Include API router - all routes included here will have the default rate limit applied.
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
@limiter.exempt # Exempt root path from default rate limiting
async def root():
    """Root endpoint with API information."""
    return {
        "message": f"{settings.PROJECT_NAME} is running!",
        "version": settings.VERSION,
        "status": "running",
        "docs_url": "/docs",
        "openapi_url": app.openapi_url, # FastAPI populates this
        "api_v1_prefix": settings.API_V1_STR,
    }

@app.get("/health", tags=["Health"])
@limiter.limit(settings.HEALTH_CHECK_RATE_LIMIT) # Apply specific limit from config
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }

if __name__ == "__main__":
    import uvicorn
    
    # Use host and port from settings
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development", # Enable reload only in development
        log_level=settings.LOG_LEVEL.lower()
    )

"""
AskRAG FastAPI Application

Main entry point for the AskRAG backend API.
"""

import logging
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import settings
from app.core.security import SecurityMiddleware, RateLimitMiddleware
from app.api.v1.api import api_router
from app.db.mock_database import get_mock_database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="RAG (Retrieval-Augmented Generation) API for document-based Q&A",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Add startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize mock database on startup"""
    try:
        logger.info("Starting AskRAG API with Mock Database...")
        mock_db = get_mock_database()
        
        # Créer des données de test si la base est vide
        if mock_db.count_documents("users") == 0:
            # Créer un utilisateur admin
            admin_user = {
                "email": "admin@askrag.com",
                "username": "admin",
                "full_name": "Administrator",
                "is_active": True,
                "is_admin": True
            }
            mock_db.insert_one("users", admin_user)
            logger.info("Created admin user")
            
            # Créer un document de demo
            demo_doc = {
                "filename": "demo.pdf",
                "title": "Document de démonstration",
                "content": "Ceci est un document de test pour AskRAG.",
                "file_type": "pdf",
                "user_id": admin_user["_id"]
            }
            mock_db.insert_one("documents", demo_doc)
            logger.info("Created demo document")
        
        logger.info("Mock database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Save mock database on shutdown"""
    try:
        logger.info("Shutting down AskRAG API...")
        mock_db = get_mock_database()
        mock_db.save_to_file()
        logger.info("Mock database saved")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security middleware
app.add_middleware(SecurityMiddleware)
app.add_middleware(RateLimitMiddleware)

# Add trusted host middleware for production
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=settings.BACKEND_CORS_ORIGINS
    )

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "AskRAG API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "api_v1": settings.API_V1_STR,
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check mock database
        mock_db = get_mock_database()
        user_count = mock_db.count_documents("users")
        
        return {
            "status": "healthy",
            "service": "askrag-api",
            "database": "mock",
            "users_count": user_count,
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "askrag-api",
            "database": "mock",
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )

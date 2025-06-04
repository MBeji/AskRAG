"""
Serveur principal AskRAG avec support d'authentification et d'upload de documents
Étape 10: Document Ingestion
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import uvicorn

from app.core.config import get_settings
from app.api.v1.endpoints import auth, documents, database, users
from app.services.auth_service import AuthService, get_auth_service
from app.db.repositories.mock_repositories import get_mock_user_repository, MockUserRepository
from app.db.repositories.user_repository import UserRepository

settings = get_settings()
security = HTTPBearer()

# Create upload directory at startup
upload_path = Path(settings.UPLOAD_DIR)
upload_path.mkdir(exist_ok=True)

# Create FastAPI app
app = FastAPI(
    title="AskRAG API",
    description="Document ingestion and RAG API",
    version="1.0.0"
)

# Dependency overrides for mock repositories
def get_user_repository() -> MockUserRepository:
    """Get mock user repository"""
    return MockUserRepository()

# Override the UserRepository dependency with mock repository
app.dependency_overrides[UserRepository] = get_user_repository

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication dependency
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
    user_repo = Depends(get_mock_user_repository)
):
    """Get current authenticated user"""
    try:
        token = credentials.credentials
        payload = auth_service.verify_access_token(token)
        user_email = payload.get("sub")
        
        if user_email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = await user_repo.get_by_email(user_email)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "service": "askrag-api",
        "status": "healthy",
        "timestamp": "2025-05-28T12:00:00.000000",
        "version": "1.0.0",
        "features": ["authentication", "document_ingestion"]
    }

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(
    documents.router, 
    prefix="/api/v1/documents", 
    tags=["documents"],
    dependencies=[Depends(get_current_user)]
)
app.include_router(database.router, prefix="/api/v1/database", tags=["database"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "AskRAG API - Document Ingestion Ready",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "api_v1": "/api/v1"
    }

if __name__ == "__main__":
    print("🚀 Starting AskRAG Document Ingestion Server...")
    print(f"📡 Server will be available at: http://localhost:8000")
    print(f"📚 API documentation at: http://localhost:8000/docs")
    print(f"🔍 Health check at: http://localhost:8000/health")
    
    uvicorn.run(
        "document_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

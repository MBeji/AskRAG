#!/usr/bin/env python3
"""
Serveur AskRAG simplifié pour Étape 10 - Focus sur l'authentification
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn

# Import our auth components
from app.services.auth_service import AuthService, get_auth_service
from app.db.repositories.mock_repositories import get_mock_user_repository, MockUserRepository
from app.models.user_v1 import UserCreate, UserLogin, UserResponse
from app.core.config import get_settings

settings = get_settings()
security = HTTPBearer()

# Create FastAPI app
app = FastAPI(
    title="AskRAG API - Étape 10",
    description="Document ingestion and authentication API",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency overrides for mock repositories
def get_user_repository() -> MockUserRepository:
    """Get mock user repository"""
    return MockUserRepository()

# Authentication dependency
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
    user_repo = Depends(get_user_repository)
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
        
        user = user_repo.get_by_email(user_email)
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

# Root endpoints
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "AskRAG API - Document Ingestion Ready",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "askrag-api"}

# Authentication endpoints
@app.post("/api/v1/auth/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
    user_repo = Depends(get_user_repository)
):
    """Register a new user"""
    existing_user = user_repo.get_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user with hashed password
    hashed_password = auth_service.get_password_hash(user_data.password)
    user = user_repo.create({
        "email": user_data.email,
        "password": hashed_password,
        "full_name": user_data.full_name,
        "is_active": True
    })
    
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login=user.last_login
    )

@app.post("/api/v1/auth/login")
async def login(
    user_credentials: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
    user_repo = Depends(get_user_repository)
):
    """Login user and return access token"""
    user = user_repo.get_by_email(user_credentials.email)
    if not user or not auth_service.verify_password(user_credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth_service.create_access_token(data={"sub": user.email})
    user_repo.update_last_login(user.id)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login
        )
    }

@app.get("/api/v1/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )

# Document endpoints (basic)
@app.post("/api/v1/documents/upload")
async def upload_document(current_user = Depends(get_current_user)):
    """Upload document endpoint (placeholder)"""
    return {
        "message": "Document upload endpoint ready",
        "user": current_user.email,
        "status": "authenticated"
    }

@app.get("/api/v1/documents")
async def list_documents(current_user = Depends(get_current_user)):
    """List documents endpoint (placeholder)"""
    return {
        "message": "Document list endpoint ready",
        "user": current_user.email,
        "documents": []
    }

if __name__ == "__main__":
    print("🚀 Starting AskRAG Document Ingestion Server (Étape 10)...")
    print(f"📡 Server will be available at: http://localhost:8000")
    print(f"📚 API documentation at: http://localhost:8000/docs")
    print(f"🔍 Health check at: http://localhost:8000/health")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

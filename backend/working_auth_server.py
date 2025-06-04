#!/usr/bin/env python3
"""
Working FastAPI server for AskRAG Étape 10 - Fixed Authentication
"""
import sys
import os
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import jwt

# Import our components
from app.core.auth import AuthService  # Static methods
from app.core.config import settings
from app.db.repositories.mock_repositories import MockUserRepository
from app.models.user_v1 import UserCreate, UserLogin, UserResponse

# Response models
class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class StatusResponse(BaseModel):
    status: str
    message: str

# Create FastAPI app
app = FastAPI(
    title="AskRAG Document Ingestion API",
    description="Authentication and document upload API for Étape 10",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Dependencies
def get_user_repository() -> MockUserRepository:
    return MockUserRepository()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_repo: MockUserRepository = Depends(get_user_repository)
) -> UserResponse:
    """Get current authenticated user"""
    try:
        # Decode JWT token
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        # Get user from repository
        user = await user_repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

# Routes
@app.get("/", response_model=StatusResponse)
async def root():
    """Root endpoint"""
    return StatusResponse(status="success", message="AskRAG Document Ingestion API is running")

@app.get("/health", response_model=StatusResponse)
async def health_check():
    """Health check endpoint"""
    return StatusResponse(status="healthy", message="Server is operational")

@app.post("/api/v1/auth/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    user_repo: MockUserRepository = Depends(get_user_repository)
):
    """Register a new user"""
    # Check if user already exists
    existing_user = await user_repo.get_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    new_user = await user_repo.create(user_data)
    
    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        username=new_user.username,
        full_name=new_user.full_name,
        is_active=new_user.is_active,
        is_verified=new_user.is_verified,
        is_superuser=new_user.is_superuser,
        created_at=new_user.created_at,
        updated_at=new_user.updated_at,
        last_login=new_user.last_login
    )

@app.post("/api/v1/auth/login", response_model=LoginResponse)
async def login(
    user_credentials: UserLogin,
    user_repo: MockUserRepository = Depends(get_user_repository)
):
    """Login user and return access token"""
    # Get user by email
    user = await user_repo.get_by_email(user_credentials.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password using static method
    if not AuthService.verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create access token using static method
    access_token = AuthService.create_access_token(data={"sub": str(user.id)})
    
    # Update last login
    await user_repo.update_last_login(user.id)
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login
        )
    )

@app.get("/api/v1/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserResponse = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@app.post("/api/v1/documents/upload", response_model=StatusResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user)
):
    """Upload a document for processing"""
    # Create uploads directory if it doesn't exist
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(exist_ok=True)
    
    # Save uploaded file
    file_path = uploads_dir / f"{current_user.id}_{file.filename}"
    
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        return StatusResponse(
            status="success",
            message=f"Document '{file.filename}' uploaded successfully for user {current_user.email}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )

@app.get("/api/v1/documents", response_model=StatusResponse)
async def list_documents(current_user: UserResponse = Depends(get_current_user)):
    """List documents for current user"""
    uploads_dir = Path("uploads")
    if not uploads_dir.exists():
        user_files = []
    else:
        user_files = [f.name for f in uploads_dir.glob(f"{current_user.id}_*")]
    
    return StatusResponse(
        status="success",
        message=f"Found {len(user_files)} documents for user {current_user.email}: {', '.join(user_files)}"
    )

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting AskRAG Document Ingestion Server...")
    print("📡 Server: http://localhost:8003")
    print("📚 Docs: http://localhost:8003/docs")
    print("🔍 Health: http://localhost:8003/health")
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8003,
        log_level="info"
    )

"""
Authentication API endpoints for AskRAG
Handles user registration, login, logout, and token refresh
"""

from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, validator
import logging

from app.core.auth import AuthService, Token, TokenData
from app.core.security import (
    get_current_user, 
    get_current_active_user,
    security,
    validate_password_strength,
    sanitize_input
)
from app.models.user_v1 import User, UserCreate, UserResponse, UserLogin
from app.db.repositories.user_repository import UserRepository
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


class UserRegister(BaseModel):
    """User registration model"""
    username: str
    email: EmailStr
    password: str
    full_name: str = ""
    
    @validator('username')
    def validate_username(cls, v):
        v = sanitize_input(v, 50)
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, hyphens and underscores')
        return v.lower()
    
    @validator('password')
    def validate_password(cls, v):
        if not validate_password_strength(v):
            raise ValueError(
                'Password must be at least 8 characters and contain uppercase, '
                'lowercase, digit and special character'
            )
        return v
    
    @validator('full_name')
    def validate_full_name(cls, v):
        return sanitize_input(v, 100)


class PasswordChange(BaseModel):
    """Password change model"""
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if not validate_password_strength(v):
            raise ValueError(
                'Password must be at least 8 characters and contain uppercase, '
                'lowercase, digit and special character'
            )
        return v


class TokenRefresh(BaseModel):
    """Token refresh model"""
    refresh_token: str


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegister,
    user_repo: UserRepository = Depends()
) -> Any:
    """Register a new user"""
    try:
        # Check if feature is enabled
        if not getattr(settings, 'ENABLE_USER_REGISTRATION', True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User registration is currently disabled"
            )
        
        # Check if user already exists
        existing_user = await user_repo.get_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        existing_username = await user_repo.get_by_username(user_data.username)
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Create user
        user_create = UserCreate(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            is_active=True  # Auto-activate for now
        )
        
        user = await user_repo.create(user_create)
        logger.info(f"New user registered: {user.email}")
        
        return UserResponse.from_orm(user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=Token)
async def login_user(
    user_credentials: UserLogin,
    user_repo: UserRepository = Depends()
) -> Any:
    """Login user and return tokens"""
    try:
        # Get user by email or username
        user = None
        if "@" in user_credentials.username:
            user = await user_repo.get_by_email(user_credentials.username)
        else:
            user = await user_repo.get_by_username(user_credentials.username)
        
        # Verify user and password
        if not user or not AuthService.verify_password(
            user_credentials.password, user.hashed_password
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username/email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account is inactive"
            )
        
        # Create token pair
        user_data = {
            "sub": str(user.id),
            "email": user.email,
            "username": user.username
        }
        
        tokens = AuthService.create_token_pair(user_data)
        
        # Update last login
        await user_repo.update_last_login(user.id)
        
        logger.info(f"User logged in: {user.email}")
        return tokens
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: TokenRefresh
) -> Any:
    """Refresh access token using refresh token"""
    try:
        tokens = AuthService.refresh_access_token(refresh_data.refresh_token)
        return tokens
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get current user information"""
    return UserResponse.from_orm(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    full_name: str = Body(embed=True),
    current_user: User = Depends(get_current_active_user),
    user_repo: UserRepository = Depends()
) -> Any:
    """Update current user information"""
    try:
        full_name = sanitize_input(full_name, 100)
        updated_user = await user_repo.update_user_info(
            current_user.id, 
            {"full_name": full_name}
        )
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse.from_orm(updated_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Update failed"
        )


@router.put("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    user_repo: UserRepository = Depends()
) -> Any:
    """Change user password"""
    try:
        # Verify current password
        if not AuthService.verify_password(
            password_data.current_password, 
            current_user.hashed_password
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password"
            )
        
        # Update password
        await user_repo.update_password(
            current_user.id, 
            password_data.new_password
        )
        
        logger.info(f"Password changed for user: {current_user.email}")
        
        return {"message": "Password updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


@router.post("/logout")
async def logout_user(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Logout user (invalidate token - for now just a placeholder)"""
    # In a full implementation, you would:
    # 1. Add token to blacklist in Redis
    # 2. Or use shorter token expiry with refresh tokens
    
    logger.info(f"User logged out: {current_user.email}")
    
    return {"message": "Successfully logged out"}


@router.get("/validate-token")
async def validate_token(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Validate current token and return user info"""
    return {
        "valid": True,
        "user": UserResponse.from_orm(current_user)
    }

"""
Password reset functionality.
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, EmailStr
import secrets
import hashlib

from app.core.auth import verify_password, get_password_hash, create_access_token
from app.core.config import settings
from app.models.user_v1 import UserInDB, PasswordReset
from app.db.repositories.user_repository import UserRepository
from app.core.email import send_password_reset_email

router = APIRouter()

# Pydantic models for password reset
class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class PasswordResetResponse(BaseModel):
    message: str
    success: bool

# In-memory store for reset tokens (in production, use Redis or database)
reset_tokens: dict = {}

# Dependency injection
def get_user_repository() -> UserRepository:
    """Get user repository instance."""
    return UserRepository()


@router.post("/password-reset/request", response_model=PasswordResetResponse)
async def request_password_reset(
    request_data: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Request a password reset for a user.
    
    Args:
        request_data: Password reset request data
        background_tasks: Background tasks for sending email
        user_repo: User repository
        
    Returns:
        Password reset response
    """
    try:
        # Check if user exists
        user = await user_repo.get_by_email(request_data.email)
        if not user:
            # Don't reveal if email exists or not for security
            return PasswordResetResponse(
                message="If the email exists, a password reset link has been sent.",
                success=True
            )
        
        if not user.is_active:
            return PasswordResetResponse(
                message="Account is inactive. Please contact support.",
                success=False
            )
        
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=1)  # Token expires in 1 hour
        
        # Store reset token
        reset_tokens[reset_token] = {
            "user_id": user.id,
            "email": user.email,
            "expires_at": expires_at,
            "used": False
        }
        
        # Send password reset email in background
        if settings.SEND_EMAILS:
            background_tasks.add_task(
                send_password_reset_email,
                email=user.email,
                username=user.username,
                reset_token=reset_token
            )
        
        return PasswordResetResponse(
            message="If the email exists, a password reset link has been sent.",
            success=True
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process password reset request: {str(e)}"
        )


@router.post("/password-reset/verify", response_model=PasswordResetResponse)
async def verify_reset_token(
    token: str
):
    """
    Verify if a password reset token is valid.
    
    Args:
        token: Reset token to verify
        
    Returns:
        Verification response
    """
    try:
        # Check if token exists
        if token not in reset_tokens:
            return PasswordResetResponse(
                message="Invalid or expired reset token.",
                success=False
            )
        
        token_data = reset_tokens[token]
        
        # Check if token is expired
        if datetime.utcnow() > token_data["expires_at"]:
            # Clean up expired token
            del reset_tokens[token]
            return PasswordResetResponse(
                message="Reset token has expired.",
                success=False
            )
        
        # Check if token has been used
        if token_data["used"]:
            return PasswordResetResponse(
                message="Reset token has already been used.",
                success=False
            )
        
        return PasswordResetResponse(
            message="Reset token is valid.",
            success=True
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify reset token: {str(e)}"
        )


@router.post("/password-reset/confirm", response_model=PasswordResetResponse)
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Confirm password reset with new password.
    
    Args:
        reset_data: Password reset confirmation data
        user_repo: User repository
        
    Returns:
        Reset confirmation response
    """
    try:
        # Check if token exists
        if reset_data.token not in reset_tokens:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        token_data = reset_tokens[reset_data.token]
        
        # Check if token is expired
        if datetime.utcnow() > token_data["expires_at"]:
            # Clean up expired token
            del reset_tokens[reset_data.token]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token has expired"
            )
        
        # Check if token has been used
        if token_data["used"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token has already been used"
            )
        
        # Validate new password
        if len(reset_data.new_password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long"
            )
        
        # Get user
        user = await user_repo.get_by_id(token_data["user_id"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update password
        hashed_password = get_password_hash(reset_data.new_password)
        await user_repo.update_password(user.id, hashed_password)
        
        # Mark token as used
        reset_tokens[reset_data.token]["used"] = True
        
        # Clean up token after use
        del reset_tokens[reset_data.token]
        
        return PasswordResetResponse(
            message="Password has been successfully reset.",
            success=True
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset password: {str(e)}"
        )


@router.get("/password-reset/cleanup")
async def cleanup_expired_tokens():
    """
    Clean up expired password reset tokens.
    This endpoint can be called periodically or by admin users.
    
    Returns:
        Cleanup statistics
    """
    try:
        current_time = datetime.utcnow()
        expired_tokens = []
        
        for token, token_data in reset_tokens.items():
            if current_time > token_data["expires_at"]:
                expired_tokens.append(token)
        
        # Remove expired tokens
        for token in expired_tokens:
            del reset_tokens[token]
        
        return {
            "message": f"Cleaned up {len(expired_tokens)} expired tokens",
            "expired_tokens_removed": len(expired_tokens),
            "active_tokens_remaining": len(reset_tokens)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup expired tokens: {str(e)}"
        )

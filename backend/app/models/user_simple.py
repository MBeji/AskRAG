from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional, Dict, Any

class User(BaseModel):
    """User model"""
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., description="Unique username")
    full_name: str = Field(..., description="User's full name")
    hashed_password: str = Field(..., description="Hashed password")
    
    # User status
    is_active: bool = Field(default=True, description="User account status")
    is_verified: bool = Field(default=False, description="Email verification status")
    is_superuser: bool = Field(default=False, description="Admin privileges")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self.is_superuser


class UserLogin(BaseModel):
    """Schema for user login"""
    username: str = Field(..., description="Email or username")
    password: str


class UserResponse(BaseModel):
    """Schema for user API responses"""
    id: str
    email: str
    username: str
    full_name: str
    is_active: bool
    is_verified: bool
    is_admin: bool = False
    created_at: datetime

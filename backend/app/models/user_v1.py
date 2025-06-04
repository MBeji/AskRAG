"""
User model for authentication and user management (Pydantic v1)
"""
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId


class UserRole(str, Enum):
    """User roles enum"""
    USER = "user"
    ADMIN = "admin"
    SUPERUSER = "superuser"


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class User(BaseModel):
    """User model"""
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
    
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
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
    
    # Profile data
    profile_data: Optional[Dict[str, Any]] = Field(default=None, description="Additional profile data")
    
    # Security
    last_login: Optional[datetime] = Field(default=None, description="Last login timestamp")
    login_attempts: int = Field(default=0, description="Failed login attempts")
    locked_until: Optional[datetime] = Field(default=None, description="Account lock expiry")


class UserCreate(BaseModel):
    """Schema for creating a new user"""
    email: EmailStr
    username: str
    full_name: str
    password: str


class UserUpdate(BaseModel):
    """Schema for updating user data"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    profile_data: Optional[Dict[str, Any]] = None


class UserInDB(User):
    """User model as stored in database"""
    pass


class UserResponse(BaseModel):
    """Schema for user response (without sensitive data)"""
    id: Optional[str] = None
    email: EmailStr
    username: str
    full_name: str
    is_active: bool
    is_verified: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    profile_data: Optional[Dict[str, Any]] = None

    class Config:
        populate_by_name = True


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token payload data"""
    user_id: Optional[str] = None
    email: Optional[str] = None
    username: Optional[str] = None


class PasswordChange(BaseModel):
    """Schema for password change"""
    current_password: str
    new_password: str


class PasswordReset(BaseModel):
    """Schema for password reset"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation"""
    token: str
    new_password: str

"""
User model for authentication and user management (Pydantic v2)
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from bson import ObjectId


class User(BaseModel):
    """User model"""
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: Optional[str] = Field(alias="_id", default=None)
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
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    
    # Profile
    avatar_url: Optional[str] = Field(None, description="Profile picture URL")
    bio: Optional[str] = Field(None, description="User biography")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences")
    
    # Usage stats
    document_count: int = Field(default=0, description="Number of uploaded documents")
    chat_count: int = Field(default=0, description="Number of chat sessions")


class UserCreate(BaseModel):
    """Schema for creating a new user"""
    email: EmailStr
    username: str
    full_name: str
    password: str
    bio: Optional[str] = None


class UserUpdate(BaseModel):
    """Schema for updating user information"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


class UserLogin(BaseModel):
    """Schema for user login"""
    email_or_username: str = Field(..., description="Email or username")
    password: str


class UserResponse(BaseModel):
    """Schema for user API responses"""
    id: str
    email: str
    username: str
    full_name: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    avatar_url: Optional[str]
    bio: Optional[str]
    document_count: int
    chat_count: int


class UserProfile(BaseModel):
    """Schema for user profile"""
    id: str
    email: str
    username: str
    full_name: str
    avatar_url: Optional[str]
    bio: Optional[str]
    created_at: datetime
    preferences: Dict[str, Any]

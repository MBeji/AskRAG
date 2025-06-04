"""
Chat models for managing chat sessions and messages
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic v2"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError('Invalid ObjectId')
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type='string')
        return field_schema


class ChatMessage(BaseModel):
    """Individual chat message"""
    id: str = Field(..., description="Unique message ID")
    role: str = Field(..., description="user, assistant, or system")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # RAG context
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Source documents used")
    confidence_score: Optional[float] = Field(None, description="Response confidence score")
    
    # Metadata
    token_count: Optional[int] = Field(None, description="Token count for this message")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    model_used: Optional[str] = Field(None, description="AI model used for response")


class ChatSession(BaseModel):
    """Chat session model"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    title: str = Field(..., description="Session title")
    user_id: str = Field(..., description="User who owns the session")
    
    # Messages
    messages: List[ChatMessage] = Field(default_factory=list, description="Chat messages")
    message_count: int = Field(default=0, description="Total message count")
      # Session metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True, description="Session status")
    
    # RAG settings used in this session
    rag_settings: Dict[str, Any] = Field(default_factory=dict, description="RAG configuration")
    
    # Usage stats
    total_tokens: int = Field(default=0, description="Total tokens used")
    total_cost: float = Field(default=0.0, description="Total cost in USD")
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class ChatSessionCreate(BaseModel):
    """Schema for creating a new chat session"""
    title: str
    user_id: str
    rag_settings: Dict[str, Any] = Field(default_factory=dict)


class MessageCreate(BaseModel):
    """Schema for creating a new message"""
    content: str
    role: str = Field(default="user", description="user, assistant, or system")


class ChatSessionResponse(BaseModel):
    """Schema for chat session API responses"""
    id: str
    title: str
    user_id: str
    message_count: int
    created_at: datetime
    updated_at: datetime
    is_active: bool
    total_tokens: int
    total_cost: float


class ChatMessageResponse(BaseModel):
    """Schema for chat message API responses"""
    id: str
    role: str
    content: str
    timestamp: datetime
    sources: List[Dict[str, Any]]
    confidence_score: Optional[float]
    token_count: Optional[int]
    processing_time: Optional[float]
    model_used: Optional[str]


class ChatHistoryResponse(BaseModel):
    """Schema for chat history responses"""
    session: ChatSessionResponse
    messages: List[ChatMessageResponse]

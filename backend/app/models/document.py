"""
Document model for storing uploaded documents and their metadata
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


class Document(BaseModel):
    """Document model"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    filename: str = Field(..., description="Original filename")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Extracted text content")
    file_type: str = Field(..., description="File type (pdf, txt, docx, etc.)")
    file_size: int = Field(..., description="File size in bytes")
    file_path: str = Field(..., description="Storage path")
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[str] = Field(None, description="User who uploaded the document")
    
    # Vector storage
    vector_id: Optional[str] = Field(None, description="FAISS vector ID")
    chunk_count: int = Field(default=0, description="Number of text chunks")
    
    # Processing status
    processing_status: str = Field(default="pending", description="pending, processing, completed, failed")
    processing_error: Optional[str] = Field(None, description="Error message if processing failed")
      # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    tags: List[str] = Field(default_factory=list, description="Document tags")
      
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class DocumentCreate(BaseModel):
    """Schema for creating a new document"""
    filename: str
    title: str
    content: str
    file_type: str
    file_size: int
    file_path: str
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)


class DocumentUpdate(BaseModel):
    """Schema for updating a document"""
    title: Optional[str] = None
    content: Optional[str] = None
    vector_id: Optional[str] = None
    chunk_count: Optional[int] = None
    processing_status: Optional[str] = None
    processing_error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class DocumentResponse(BaseModel):
    """Schema for document API responses"""
    id: str
    filename: str
    title: str
    file_type: str
    file_size: int
    upload_date: datetime
    user_id: Optional[str]
    chunk_count: int
    processing_status: str
    tags: List[str]
    metadata: Dict[str, Any]

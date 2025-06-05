from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
# from beanie import PydanticObjectId # If using PydanticObjectId directly

from pydantic import conint, constr # For more specific types if needed

class DocumentBase(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255)
    content_type: str = Field(..., max_length=100)
    uploader_id: Optional[str] = None # Could be PydanticObjectId if linked to User
    status: Optional[str] = Field(default="pending", max_length=50)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    tags: Optional[List[str]] = Field(default_factory=list)
    title: Optional[str] = Field(default=None, max_length=255)
    file_size: Optional[conint(gt=0)] = None # Ensures file_size, if provided, is > 0
    file_path: Optional[str] = Field(default=None, max_length=1024) # Storage path

class DocumentCreate(DocumentBase):
    # Fields required on creation are inherited from DocumentBase
    # and should not be Optional there if truly required.
    # filename and content_type are already required in DocumentBase.
    pass

class DocumentUpdate(BaseModel): # Not inheriting from DocumentBase to define all as Optional
    filename: Optional[str] = Field(default=None, min_length=1, max_length=255)
    content_type: Optional[str] = Field(default=None, max_length=100)
    status: Optional[str] = Field(default=None, max_length=50)
    vector_ids: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    title: Optional[str] = Field(default=None, max_length=255)
    content: Optional[str] = None # Extracted text content, no specific validation here yet
    file_size: Optional[conint(gt=0)] = None
    file_path: Optional[str] = Field(default=None, max_length=1024)
    chunk_count: Optional[conint(ge=0)] = None # chunk_count can be 0
    processing_error: Optional[str] = None
    tags: Optional[List[str]] = None

class DocumentInDBBase(DocumentBase):
    id: str # In MongoDB, this is typically _id, Beanie handles mapping
    # If using Beanie's PydanticObjectId: id: PydanticObjectId
    upload_date: datetime
    vector_ids: List[str] = Field(default_factory=list)
    chunk_count: Optional[int] = 0
    processing_error: Optional[str] = None

    class Config:
        from_attributes = True # For Pydantic V2 (replaces orm_mode)
        # orm_mode = True # For Pydantic V1

class DocumentOut(DocumentInDBBase):
    # This will be the main schema for returning document info
    pass

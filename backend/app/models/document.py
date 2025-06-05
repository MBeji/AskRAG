from datetime import datetime
from typing import Optional, List, Dict, Any
from beanie import Document, Indexed
from pydantic import Field, EmailStr # EmailStr might not be needed here, but Field is useful.
from app.models.user import User # Assuming User model might be linked soon

# If we need to link to User using PydanticObjectId from Beanie
# from beanie import PydanticObjectId

class Document(Document):
    filename: Indexed(str)
    content_type: str # Was file_type in the old model
    # uploader_id: PydanticObjectId # Or Indexed(PydanticObjectId) if direct link to User._id
    uploader_id: str # Keeping as str for now, can be an ObjectId string.
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    # Status: pending_upload -> pending_extraction -> text_extracted -> pending_vectorization -> vectorized_pending_storage -> vectorized -> failed_extraction / failed_vectorization
    status: str = Field(default="pending_upload")
    vector_ids: List[str] = Field(default_factory=list) # Will store FAISS IDs in Step 13
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Fields from Step 11
    filename_on_disk: Optional[str] = None
    extracted_text: Optional[str] = None

    # New field for Step 12
    # Each dict: {"chunk_text": str, "embedding": List[float], "faiss_id": Optional[Any]}
    # faiss_id will be populated in Step 13.
    chunks: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

    # Optional fields from the old model that might be useful / can be retained
    title: Optional[str] = None # Can be derived from filename or user-provided
    # content: Optional[str] = None # Replaced by extracted_text for clarity of purpose
    file_size: Optional[int] = None # Size in bytes
    file_path: Optional[str] = None # Full absolute path to the stored file
    chunk_count: Optional[int] = Field(default=0) # For vectorization later
    processing_error: Optional[str] = None # To store any errors during processing
    tags: List[str] = Field(default_factory=list)

    class Settings:
        name = "documents" # MongoDB collection name
        # Example: indexes = [
        #     [("filename", pymongo.ASCENDING), ("upload_date", pymongo.DESCENDING)],
        # ]

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field # BaseModel for EmbeddedDocument if not using Beanie's specific
from beanie import Document, EmbeddedDocument, PydanticObjectId, Link # Link for potential User linking

from app.models.user import User as UserModel # For type hinting if using Link
from app.schemas.rag import SearchResultItem # For typing sources, if defined there

# If SearchResultItem is not yet in schemas.rag, define a placeholder or use Dict
# For now, assume SearchResultItem or a similar structure will be used for sources.
# Using Dict[str, Any] for sources for now to keep it simple if SearchResultItem is not ready.

class ChatMessage(EmbeddedDocument): # Use EmbeddedDocument for sub-documents in a list
    message_id: PydanticObjectId = Field(default_factory=PydanticObjectId)
    sender: str # e.g., "user", "bot"
    text: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    # sources: Optional[List[SearchResultItem]] = None # If using the Pydantic model from schemas.rag
    sources: Optional[List[Dict[str, Any]]] = None # Store relevant source chunks for bot messages

    class Settings:
        # Settings for embedded documents if needed, usually not required for basic embedding
        pass

class ChatSession(Document):
    # user_id: Link[UserModel] # Example if linking directly to User document (causes population)
    user_id: PydanticObjectId # Store as PydanticObjectId, assuming it's the User's _id
    title: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow) # Should be updated on new messages
    messages: List[ChatMessage] = Field(default_factory=list)

    class Settings:
        name = "chat_sessions" # MongoDB collection name
        # Example: indexes = [
        #     [("user_id", pymongo.ASCENDING), ("updated_at", pymongo.DESCENDING)],
        # ]
        # Keep_nulls = False # Beanie setting to not store fields with None value (if desired)

    # Method to update timestamp on modification
    async def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        await super().save(*args, **kwargs)

# Note: Pydantic schemas for API request/response (like ChatMessageResponse, ChatSessionResponse)
# should go into app/schemas/chat.py as per Step 21.3.

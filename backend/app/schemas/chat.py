from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from beanie import PydanticObjectId # For ID fields

# Assuming SearchResultItem is defined in schemas.rag and will be used for sources
# If not, define a similar structure here or use Dict[str, Any]
from app.schemas.rag import SearchResultItem # Or a more generic SourceItem if preferred

class ChatMessageBase(BaseModel):
    text: str = Field(..., min_length=1, description="Content of the chat message.")
    # sender is often determined by the endpoint (e.g., user message vs bot message)
    # If it can be part of request body for some reason:
    # sender: str = Field(..., description="Sender of the message, e.g., 'user' or 'bot'.")

class ChatMessageCreate(ChatMessageBase):
    # Used when client sends a new message. Sender is typically implicit (the user).
    # If creating bot messages internally, sender would be set.
    pass

class ChatMessageResponse(ChatMessageBase):
    message_id: str # PydanticObjectId will be serialized to str
    sender: str
    timestamp: datetime
    sources: Optional[List[SearchResultItem]] = None # Use the same SearchResultItem as RAG for consistency

    class Config:
        from_attributes = True

class ChatSessionBase(BaseModel):
    title: Optional[str] = Field(None, max_length=255, description="Title of the chat session.")

class ChatSessionCreate(ChatSessionBase):
    # Optional: include an initial message if sessions are always created with one
    # initial_message: Optional[ChatMessageCreate] = None
    # For now, service handles creating initial message if text is provided.
    pass

class ChatSessionResponse(ChatSessionBase):
    id: str # PydanticObjectId will be serialized to str
    user_id: str # PydanticObjectId of the user, serialized to str
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessageResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True

class ChatSessionListItem(ChatSessionBase):
    id: str # PydanticObjectId will be serialized to str
    user_id: str # PydanticObjectId of the user, serialized to str
    created_at: datetime
    updated_at: datetime
    last_message_snippet: Optional[str] = Field(None, description="A short snippet of the last message.")
    # message_count: Optional[int] = 0 # Could be added if useful

    class Config:
        from_attributes = True

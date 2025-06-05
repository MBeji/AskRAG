import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body

from beanie import PydanticObjectId
from app.models.user import User as UserModel
from app.services.auth_service import get_current_active_user
from app.services import chat_service
from app.schemas.chat import (
    ChatSessionCreate,
    ChatSessionResponse,
    ChatSessionListItem,
    ChatMessageCreate, # For adding a message to an existing session (user-initiated)
    ChatMessageResponse,
)
# Assuming SearchResultItem is used for sources, and it's in schemas.rag
# from app.schemas.rag import SearchResultItem

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_new_chat_session_endpoint(
    session_create: Optional[ChatSessionCreate] = None, # Can be empty to start a session, or with a title
    # initial_message: Optional[ChatMessageCreate] = Body(None, embed=True), # Alternative for initial message
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Create a new chat session for the authenticated user.
    Optionally, a title or an initial message can be provided.
    """
    initial_message_text: Optional[str] = None
    # if initial_message:
    #     initial_message_text = initial_message.text

    title = session_create.title if session_create else None

    session = await chat_service.create_chat_session(
        user=current_user,
        initial_message_text=initial_message_text, # Currently no direct way to pass initial message via this request
        title=title
    )
    if not session: # Should not happen if create_chat_session raises on error
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create chat session.")

    # Convert ChatMessage (Beanie model) to ChatMessageResponse (Pydantic schema)
    messages_response = [ChatMessageResponse.model_validate(msg) for msg in session.messages]

    return ChatSessionResponse(
        id=str(session.id),
        user_id=str(session.user_id),
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=messages_response
    )

@router.get("/sessions", response_model=List[ChatSessionListItem])
async def list_user_chat_sessions_endpoint(
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    List all chat sessions for the authenticated user.
    """
    sessions = await chat_service.list_chat_sessions_for_user(user=current_user, skip=skip, limit=limit)

    response_items = []
    for session in sessions:
        last_msg_snippet = None
        if session.messages:
            last_msg_snippet = session.messages[-1].text[:100] # Snippet of last message
            if len(session.messages[-1].text) > 100:
                last_msg_snippet += "..."

        response_items.append(ChatSessionListItem(
            id=str(session.id),
            user_id=str(session.user_id),
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            last_message_snippet=last_msg_snippet
        ))
    return response_items

@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session_endpoint(
    session_id: PydanticObjectId,
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Get a specific chat session, including all its messages.
    """
    session = await chat_service.get_chat_session(session_id=session_id, user=current_user)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found or access denied.")

    messages_response = [ChatMessageResponse.model_validate(msg) for msg in session.messages]

    return ChatSessionResponse(
        id=str(session.id),
        user_id=str(session.user_id),
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=messages_response
    )

@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse)
async def add_user_message_to_session_endpoint( # Renamed for clarity from generic "add_message"
    session_id: PydanticObjectId,
    message_data: ChatMessageCreate, # User sends a message with 'text'
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Add a new user message to an existing chat session.
    The RAG /ask endpoint will handle adding bot messages with sources.
    """
    # This endpoint is for when the user sends a message to an existing chat.
    # The RAG /ask endpoint should handle creating/adding user message AND bot response.
    # This specific endpoint might be useful if user can send messages without triggering RAG,
    # or if chat UI explicitly adds user message first, then calls /ask.
    # For now, assuming this is for user-initiated messages to an existing session.

    session = await chat_service.add_message_to_session(
        session_id=session_id,
        user=current_user,
        sender="user", # Message from user
        text=message_data.text,
        sources=None # User messages don't have sources
    )
    if not session or not session.messages:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found or message could not be added.")

    # Return the newly added message
    newly_added_message = session.messages[-1]
    return ChatMessageResponse.model_validate(newly_added_message)

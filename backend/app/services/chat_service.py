import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from beanie import PydanticObjectId
from app.models.user import User as UserModel # Beanie User model
from app.models.chat import ChatSession, ChatMessage # Beanie Chat models
# Schemas are not directly used here but define the data structures service interacts with
# from app.schemas.chat import ChatMessageCreate
# from app.schemas.rag import SearchResultItem # For typing sources

logger = logging.getLogger(__name__)

async def create_chat_session(
    user: UserModel,
    initial_message_text: Optional[str] = None,
    title: Optional[str] = None
) -> ChatSession:
    """
    Creates a new ChatSession for the user.
    If initial_message_text is provided, adds a user message.
    If title is not provided and initial_message_text is, use a snippet as title.
    """
    if not title and initial_message_text:
        title = initial_message_text[:50] + "..." if len(initial_message_text) > 50 else initial_message_text
    elif not title:
        title = f"Chat Session - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"

    chat_session = ChatSession(
        user_id=user.id, # type: ignore # Beanie expects PydanticObjectId here
        title=title,
        messages=[] # Start with an empty list of messages
    )

    # If there's an initial message, add it now before first save to ensure updated_at is correct.
    if initial_message_text:
        initial_msg_obj = ChatMessage(
            sender="user",
            text=initial_message_text,
            timestamp=datetime.utcnow()
            # sources would typically not be present for initial user message
        )
        chat_session.messages.append(initial_msg_obj)
        chat_session.updated_at = initial_msg_obj.timestamp # Set updated_at to the first message's time

    # The .save() method will set created_at and the initial updated_at if not already set by message logic
    await chat_session.save()
    logger.info(f"Chat session created: {chat_session.id} for user {user.id}")
    return chat_session

async def add_message_to_session(
    session_id: PydanticObjectId,
    user: UserModel, # To verify ownership
    sender: str,
    text: str,
    sources: Optional[List[Dict[str, Any]]] = None # Assumes sources are List of Dicts
) -> Optional[ChatSession]:
    """
    Adds a message to an existing ChatSession.
    Ensures the session belongs to the user.
    """
    chat_session = await ChatSession.find_one(
        ChatSession.id == session_id,
        ChatSession.user_id == user.id # type: ignore # Ownership check
    )

    if not chat_session:
        logger.warning(f"Chat session {session_id} not found for user {user.id}")
        return None

    new_message = ChatMessage(
        sender=sender,
        text=text,
        timestamp=datetime.utcnow(),
        sources=sources
    )
    chat_session.messages.append(new_message)
    # chat_session.updated_at will be set by the .save() hook in ChatSession model
    await chat_session.save()
    logger.info(f"Message added to session {session_id} by {sender}")
    return chat_session

async def get_chat_session(session_id: PydanticObjectId, user: UserModel) -> Optional[ChatSession]:
    """
    Retrieves a specific chat session by ID, ensuring it belongs to the user.
    """
    chat_session = await ChatSession.find_one(
        ChatSession.id == session_id,
        ChatSession.user_id == user.id # type: ignore
    )
    if not chat_session:
        logger.info(f"Chat session {session_id} not found or access denied for user {user.id}")
        return None
    logger.info(f"Chat session {session_id} retrieved for user {user.id}")
    return chat_session

async def list_chat_sessions_for_user(
    user: UserModel,
    skip: int = 0,
    limit: int = 100
) -> List[ChatSession]:
    """
    Lists chat sessions for a user, sorted by updated_at descending.
    """
    sessions = await ChatSession.find(
        ChatSession.user_id == user.id, # type: ignore
        skip=skip,
        limit=limit
    ).sort("-updated_at").to_list()

    logger.info(f"Retrieved {len(sessions)} chat sessions for user {user.id}")
    return sessions

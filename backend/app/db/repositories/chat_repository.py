"""
Chat repository for MongoDB operations
"""
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from ..connection import get_database
from ...models.chat import ChatSession, ChatSessionCreate, ChatMessage, MessageCreate


class ChatRepository:
    """Repository for chat CRUD operations"""
    
    def __init__(self):
        self.collection_name = "chat_sessions"
    
    @property
    def collection(self) -> AsyncIOMotorCollection:
        """Get chat sessions collection"""
        db = get_database()
        return db[self.collection_name]
    
    async def create_session(self, session_data: ChatSessionCreate) -> ChatSession:
        """Create a new chat session"""
        session_dict = session_data.dict()
        session_dict["created_at"] = datetime.utcnow()
        session_dict["updated_at"] = datetime.utcnow()
        session_dict["is_active"] = True
        session_dict["messages"] = []
        session_dict["message_count"] = 0
        session_dict["total_tokens"] = 0
        session_dict["total_cost"] = 0.0
        
        result = await self.collection.insert_one(session_dict)
        session_dict["_id"] = result.inserted_id
        
        return ChatSession(**session_dict)
    
    async def get_session_by_id(self, session_id: str) -> Optional[ChatSession]:
        """Get chat session by ID"""
        if not ObjectId.is_valid(session_id):
            return None
            
        session = await self.collection.find_one({"_id": ObjectId(session_id)})
        return ChatSession(**session) if session else None
    
    async def get_sessions_by_user(self, user_id: str, skip: int = 0, limit: int = 50) -> List[ChatSession]:
        """Get chat sessions by user ID"""
        cursor = self.collection.find(
            {"user_id": user_id, "is_active": True}
        ).skip(skip).limit(limit).sort("updated_at", -1)
        
        sessions = await cursor.to_list(length=limit)
        return [ChatSession(**session) for session in sessions]
    
    async def add_message(self, session_id: str, message: MessageCreate) -> Optional[ChatMessage]:
        """Add message to chat session"""
        if not ObjectId.is_valid(session_id):
            return None
        
        # Create message with ID and timestamp
        message_dict = message.dict()
        message_dict["id"] = str(ObjectId())
        message_dict["timestamp"] = datetime.utcnow()
        message_dict["sources"] = []
        
        chat_message = ChatMessage(**message_dict)
        
        # Update session with new message
        result = await self.collection.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$push": {"messages": message_dict},
                "$inc": {"message_count": 1},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        return chat_message if result.modified_count > 0 else None
    
    async def update_message(self, session_id: str, message_id: str, **kwargs) -> bool:
        """Update a specific message in a session"""
        if not ObjectId.is_valid(session_id):
            return False
        
        update_fields = {}
        for key, value in kwargs.items():
            update_fields[f"messages.$.{key}"] = value
        
        if not update_fields:
            return False
        
        result = await self.collection.update_one(
            {
                "_id": ObjectId(session_id),
                "messages.id": message_id
            },
            {
                "$set": {
                    **update_fields,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return result.modified_count > 0
    
    async def update_session_stats(self, session_id: str, tokens: int, cost: float) -> bool:
        """Update session usage statistics"""
        if not ObjectId.is_valid(session_id):
            return False
        
        result = await self.collection.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$inc": {
                    "total_tokens": tokens,
                    "total_cost": cost
                },
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        return result.modified_count > 0
    
    async def update_session_title(self, session_id: str, title: str) -> bool:
        """Update session title"""
        if not ObjectId.is_valid(session_id):
            return False
        
        result = await self.collection.update_one(
            {"_id": ObjectId(session_id)},
            {"$set": {"title": title, "updated_at": datetime.utcnow()}}
        )
        
        return result.modified_count > 0
    
    async def deactivate_session(self, session_id: str) -> bool:
        """Deactivate chat session"""
        if not ObjectId.is_valid(session_id):
            return False
        
        result = await self.collection.update_one(
            {"_id": ObjectId(session_id)},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )
        
        return result.modified_count > 0
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete chat session"""
        if not ObjectId.is_valid(session_id):
            return False
        
        result = await self.collection.delete_one({"_id": ObjectId(session_id)})
        return result.deleted_count > 0
    
    async def get_session_messages(self, session_id: str, skip: int = 0, limit: int = 100) -> List[ChatMessage]:
        """Get messages from a chat session"""
        if not ObjectId.is_valid(session_id):
            return []
        
        # Use aggregation to get paginated messages
        pipeline = [
            {"$match": {"_id": ObjectId(session_id)}},
            {"$project": {"messages": {"$slice": ["$messages", skip, limit]}}},
        ]
        
        result = await self.collection.aggregate(pipeline).to_list(1)
        if not result:
            return []
        
        messages = result[0].get("messages", [])
        return [ChatMessage(**msg) for msg in messages]
    
    async def count_user_sessions(self, user_id: str) -> int:
        """Count active sessions for a user"""
        return await self.collection.count_documents({
            "user_id": user_id,
            "is_active": True
        })
    
    async def create_indexes(self):
        """Create database indexes for better performance"""
        # User sessions index
        await self.collection.create_index("user_id")
        
        # Active sessions index
        await self.collection.create_index("is_active")
        
        # Updated date index
        await self.collection.create_index([("updated_at", -1)])
        
        # Message ID index for updates
        await self.collection.create_index("messages.id")

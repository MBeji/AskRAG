"""
User repository for MongoDB operations
"""
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from ..connection import get_database
from ...models.user import User, UserCreate, UserUpdate


class UserRepository:
    """Repository for user CRUD operations"""
    
    def __init__(self):
        self.collection_name = "users"
    
    @property
    def collection(self) -> AsyncIOMotorCollection:
        """Get users collection"""
        db = get_database()
        return db[self.collection_name]
    
    async def create(self, user_data: UserCreate, hashed_password: str) -> User:
        """Create a new user"""
        user_dict = user_data.dict(exclude={"password"})
        user_dict["hashed_password"] = hashed_password
        user_dict["created_at"] = datetime.utcnow()
        user_dict["updated_at"] = datetime.utcnow()
        user_dict["is_active"] = True
        user_dict["is_verified"] = False
        user_dict["is_superuser"] = False
        user_dict["document_count"] = 0
        user_dict["chat_count"] = 0
        user_dict["preferences"] = {}
        
        result = await self.collection.insert_one(user_dict)
        user_dict["_id"] = result.inserted_id
        
        return User(**user_dict)
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        if not ObjectId.is_valid(user_id):
            return None
            
        user = await self.collection.find_one({"_id": ObjectId(user_id)})
        return User(**user) if user else None
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        user = await self.collection.find_one({"email": email.lower()})
        return User(**user) if user else None
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        user = await self.collection.find_one({"username": username.lower()})
        return User(**user) if user else None
    
    async def get_by_email_or_username(self, email_or_username: str) -> Optional[User]:
        """Get user by email or username"""
        query = {
            "$or": [
                {"email": email_or_username.lower()},
                {"username": email_or_username.lower()}
            ]
        }
        user = await self.collection.find_one(query)
        return User(**user) if user else None
    
    async def get_all(self, skip: int = 0, limit: int = 50) -> List[User]:
        """Get all users"""
        cursor = self.collection.find().skip(skip).limit(limit).sort("created_at", -1)
        users = await cursor.to_list(length=limit)
        return [User(**user) for user in users]
    
    async def update(self, user_id: str, update_data: UserUpdate) -> Optional[User]:
        """Update user"""
        if not ObjectId.is_valid(user_id):
            return None
        
        update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
        if not update_dict:
            return await self.get_by_id(user_id)
        
        # Lowercase email and username
        if "email" in update_dict:
            update_dict["email"] = update_dict["email"].lower()
        if "username" in update_dict:
            update_dict["username"] = update_dict["username"].lower()
        
        update_dict["updated_at"] = datetime.utcnow()
        
        result = await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_dict}
        )
        
        if result.modified_count:
            return await self.get_by_id(user_id)
        return None
    
    async def delete(self, user_id: str) -> bool:
        """Delete user"""
        if not ObjectId.is_valid(user_id):
            return False
            
        result = await self.collection.delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count > 0
    
    async def update_last_login(self, user_id: str) -> bool:
        """Update user's last login timestamp"""
        if not ObjectId.is_valid(user_id):
            return False
        
        result = await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        return result.modified_count > 0
    
    async def increment_document_count(self, user_id: str) -> bool:
        """Increment user's document count"""
        if not ObjectId.is_valid(user_id):
            return False
        
        result = await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$inc": {"document_count": 1}}
        )
        return result.modified_count > 0
    
    async def increment_chat_count(self, user_id: str) -> bool:
        """Increment user's chat count"""
        if not ObjectId.is_valid(user_id):
            return False
        
        result = await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$inc": {"chat_count": 1}}
        )
        return result.modified_count > 0
    
    async def verify_user(self, user_id: str) -> bool:
        """Mark user as verified"""
        if not ObjectId.is_valid(user_id):
            return False
        
        result = await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"is_verified": True, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0
    
    async def deactivate_user(self, user_id: str) -> bool:
        """Deactivate user account"""
        if not ObjectId.is_valid(user_id):
            return False
        
        result = await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0
    
    async def email_exists(self, email: str) -> bool:
        """Check if email already exists"""
        count = await self.collection.count_documents({"email": email.lower()})
        return count > 0
    
    async def username_exists(self, username: str) -> bool:
        """Check if username already exists"""
        count = await self.collection.count_documents({"username": username.lower()})
        return count > 0
    
    async def create_indexes(self):
        """Create database indexes for better performance"""
        # Unique email index
        await self.collection.create_index("email", unique=True)
        
        # Unique username index
        await self.collection.create_index("username", unique=True)
        
        # Active users index
        await self.collection.create_index("is_active")
        
        # Created date index
        await self.collection.create_index([("created_at", -1)])

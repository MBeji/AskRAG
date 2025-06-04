"""
Document repository for MongoDB operations
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from ..connection import get_database
from ...models.document import Document, DocumentCreate, DocumentUpdate


class DocumentRepository:
    """Repository for document CRUD operations"""
    
    def __init__(self):
        self.collection_name = "documents"
    
    @property
    def collection(self) -> AsyncIOMotorCollection:
        """Get documents collection"""
        db = get_database()
        return db[self.collection_name]
    
    async def create(self, document_data: DocumentCreate) -> Document:
        """Create a new document"""
        doc_dict = document_data.dict()
        doc_dict["upload_date"] = datetime.utcnow()
        doc_dict["processing_status"] = "pending"
        
        result = await self.collection.insert_one(doc_dict)
        doc_dict["_id"] = result.inserted_id
        
        return Document(**doc_dict)
    
    async def get_by_id(self, document_id: str) -> Optional[Document]:
        """Get document by ID"""
        if not ObjectId.is_valid(document_id):
            return None
            
        doc = await self.collection.find_one({"_id": ObjectId(document_id)})
        return Document(**doc) if doc else None
    
    async def get_by_user_id(self, user_id: str, skip: int = 0, limit: int = 50) -> List[Document]:
        """Get documents by user ID"""
        cursor = self.collection.find({"user_id": user_id}).skip(skip).limit(limit).sort("upload_date", -1)
        docs = await cursor.to_list(length=limit)
        return [Document(**doc) for doc in docs]
    
    async def get_all(self, skip: int = 0, limit: int = 50) -> List[Document]:
        """Get all documents"""
        cursor = self.collection.find().skip(skip).limit(limit).sort("upload_date", -1)
        docs = await cursor.to_list(length=limit)
        return [Document(**doc) for doc in docs]
    
    async def update(self, document_id: str, update_data: DocumentUpdate) -> Optional[Document]:
        """Update document"""
        if not ObjectId.is_valid(document_id):
            return None
        
        update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
        if not update_dict:
            return await self.get_by_id(document_id)
        
        update_dict["updated_at"] = datetime.utcnow()
        
        result = await self.collection.update_one(
            {"_id": ObjectId(document_id)},
            {"$set": update_dict}
        )
        
        if result.modified_count:
            return await self.get_by_id(document_id)
        return None
    
    async def delete(self, document_id: str) -> bool:
        """Delete document"""
        if not ObjectId.is_valid(document_id):
            return False
            
        result = await self.collection.delete_one({"_id": ObjectId(document_id)})
        return result.deleted_count > 0
    
    async def update_processing_status(self, document_id: str, status: str, error: Optional[str] = None) -> bool:
        """Update document processing status"""
        if not ObjectId.is_valid(document_id):
            return False
        
        update_data = {"processing_status": status, "updated_at": datetime.utcnow()}
        if error:
            update_data["processing_error"] = error
        
        result = await self.collection.update_one(
            {"_id": ObjectId(document_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    async def search_by_text(self, query: str, user_id: Optional[str] = None) -> List[Document]:
        """Search documents by text content"""
        search_filter = {"$text": {"$search": query}}
        if user_id:
            search_filter["user_id"] = user_id
        
        cursor = self.collection.find(search_filter)
        docs = await cursor.to_list(length=100)
        return [Document(**doc) for doc in docs]
    
    async def get_by_status(self, status: str) -> List[Document]:
        """Get documents by processing status"""
        cursor = self.collection.find({"processing_status": status})
        docs = await cursor.to_list(length=100)
        return [Document(**doc) for doc in docs]
    
    async def count_by_user(self, user_id: str) -> int:
        """Count documents by user"""
        return await self.collection.count_documents({"user_id": user_id})
    
    async def create_indexes(self):
        """Create database indexes for better performance"""
        # Text search index
        await self.collection.create_index([("title", "text"), ("content", "text")])
        
        # User documents index
        await self.collection.create_index("user_id")
        
        # Processing status index
        await self.collection.create_index("processing_status")
        
        # Upload date index
        await self.collection.create_index([("upload_date", -1)])

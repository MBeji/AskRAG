"""
Repositories utilisant la base de données mock
"""
from typing import List, Optional
from datetime import datetime

from ..mock_database import get_mock_database
from ...models.user import User, UserCreate, UserUpdate
from ...models.document import Document, DocumentCreate, DocumentUpdate

class MockUserRepository:
    """Repository utilisateur pour base mock"""
    
    def __init__(self):
        self.db = get_mock_database()
        self.collection = self.db.get_collection("users")
    
    async def create(self, user_data: UserCreate) -> User:
        """Créer un utilisateur"""
        user_dict = user_data.dict()
        user_dict["created_at"] = datetime.utcnow()
        user_dict["is_active"] = True
        user_dict["is_admin"] = False
        
        # Hash password (simple mock)
        if "password" in user_dict:
            user_dict["hashed_password"] = f"hashed_{user_dict.pop('password')}"
        
        result = self.collection.insert_one(user_dict)
        user_dict["id"] = result.inserted_id
        user_dict["_id"] = result.inserted_id
        return User(**user_dict)
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Obtenir un utilisateur par ID"""
        user_data = self.collection.find_one({"_id": user_id})
        return User(**user_data) if user_data else None
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Obtenir un utilisateur par email"""
        user_data = self.collection.find_one({"email": email})
        return User(**user_data) if user_data else None
    
    async def list(self, skip: int = 0, limit: int = 50) -> List[User]:
        """Obtenir tous les utilisateurs"""
        users_data = self.collection.find()
        return [User(**user) for user in users_data[skip:skip+limit]]
    
    async def update(self, user_id: str, user_update: UserUpdate) -> Optional[User]:
        """Mettre à jour un utilisateur"""
        update_data = user_update.dict(exclude_unset=True)
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            # Mock update (simple replace for mock)
            user_data = self.collection.find_one({"_id": user_id})
            if user_data:
                user_data.update(update_data)
                return User(**user_data)
        return None
    
    async def delete(self, user_id: str) -> bool:
        """Supprimer un utilisateur"""
        result = self.collection.delete_one({"_id": user_id})
        return result.deleted_count > 0
    
    async def count(self) -> int:
        """Compter les utilisateurs"""
        return self.collection.count_documents()
    
    # Legacy methods for backward compatibility
    async def create_user(self, user_data: dict) -> dict:
        """Créer un utilisateur (legacy)"""
        user_data["created_at"] = datetime.now().isoformat()
        user_data["is_active"] = True
        result = self.collection.insert_one(user_data)
        user_data["_id"] = result.inserted_id
        return user_data
    
    async def get_user_by_id(self, user_id: str) -> Optional[dict]:
        """Obtenir un utilisateur par ID (legacy)"""
        return self.collection.find_one({"_id": user_id})
    
    async def get_user_by_email(self, email: str) -> Optional[dict]:
        """Obtenir un utilisateur par email (legacy)"""
        return self.collection.find_one({"email": email})
      async def get_all_users(self, skip: int = 0, limit: int = 50) -> List[dict]:
        """Obtenir tous les utilisateurs (legacy)"""
        all_users = self.collection.find()
        return all_users[skip:skip+limit]
    
    async def count_users(self) -> int:
        """Compter les utilisateurs (legacy)"""
        return self.collection.count_documents()

class MockDocumentRepository:
    """Repository document pour base mock"""
    
    def __init__(self):
        self.db = get_mock_database()
        self.collection = self.db.get_collection("documents")
    
    async def create(self, doc_data: DocumentCreate) -> Document:
        """Créer un document"""
        doc_dict = doc_data.dict()
        doc_dict["upload_date"] = datetime.utcnow()
        doc_dict["processing_status"] = "pending"
        doc_dict["chunk_count"] = 0
        
        result = self.collection.insert_one(doc_dict)
        doc_dict["id"] = result.inserted_id
        doc_dict["_id"] = result.inserted_id
        return Document(**doc_dict)
    
    async def get_by_id(self, doc_id: str) -> Optional[Document]:
        """Obtenir un document par ID"""
        doc_data = self.collection.find_one({"_id": doc_id})
        return Document(**doc_data) if doc_data else None
    
    async def list(self, skip: int = 0, limit: int = 50) -> List[Document]:
        """Obtenir tous les documents"""
        docs_data = self.collection.find()
        return [Document(**doc) for doc in docs_data[skip:skip+limit]]
    
    async def get_by_user(self, user_id: str, skip: int = 0, limit: int = 50) -> List[Document]:
        """Obtenir les documents d'un utilisateur"""
        docs_data = self.collection.find({"user_id": user_id})
        return [Document(**doc) for doc in docs_data[skip:skip+limit]]
    
    async def update(self, doc_id: str, doc_update: DocumentUpdate) -> Optional[Document]:
        """Mettre à jour un document"""
        update_data = doc_update.dict(exclude_unset=True)
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            # Mock update
            doc_data = self.collection.find_one({"_id": doc_id})
            if doc_data:
                doc_data.update(update_data)
                return Document(**doc_data)
        return None
    
    async def delete(self, doc_id: str) -> bool:
        """Supprimer un document"""
        result = self.collection.delete_one({"_id": doc_id})
        return result.deleted_count > 0
    
    async def count(self) -> int:
        """Compter les documents"""
        return self.collection.count_documents()
    
    # Legacy methods
    async def create_document(self, doc_data: dict) -> dict:
        """Créer un document (legacy)"""
        doc_data["upload_date"] = datetime.now().isoformat()
        doc_data["processing_status"] = "pending"
        result = self.collection.insert_one(doc_data)
        doc_data["_id"] = result.inserted_id
        return doc_data
    
    async def get_document_by_id(self, doc_id: str) -> Optional[dict]:
        """Obtenir un document par ID (legacy)"""
        return self.collection.find_one({"_id": doc_id})
      async def get_documents_by_user(self, user_id: str, skip: int = 0, limit: int = 50) -> List[dict]:
        """Obtenir les documents d'un utilisateur (legacy)"""
        all_docs = self.collection.find({"user_id": user_id})
        return all_docs[skip:skip+limit]
      async def get_all_documents(self, skip: int = 0, limit: int = 50) -> List[dict]:
        """Obtenir tous les documents (legacy)"""
        all_docs = self.collection.find()
        return all_docs[skip:skip+limit]
    
    async def count_documents(self) -> int:
        """Compter les documents (legacy)"""
        return self.collection.count_documents()

class MockChatRepository:
    """Repository chat pour base mock"""
    
    def __init__(self):
        self.db = get_mock_database()
        self.collection = self.db.get_collection("chat_sessions")
    
    async def create_session(self, session_data: dict) -> dict:
        """Créer une session de chat"""
        session_data["created_at"] = datetime.now().isoformat()
        session_data["is_active"] = True
        session_data["messages"] = []
        result = self.collection.insert_one(session_data)
        session_data["_id"] = result.inserted_id
        return session_data
    
    async def get_session_by_id(self, session_id: str) -> Optional[dict]:
        """Obtenir une session par ID"""
        return self.collection.find_one({"_id": session_id})
    
    async def get_sessions_by_user(self, user_id: str, skip: int = 0, limit: int = 50) -> List[dict]:
        """Obtenir les sessions d'un utilisateur"""
        cursor = self.collection.find({"user_id": user_id}).skip(skip).limit(limit)
        return await cursor.to_list(limit)
    
    async def count_sessions(self) -> int:
        """Compter les sessions"""
        return self.collection.count_documents()

# Fonctions de dépendance pour FastAPI
def get_mock_user_repository() -> MockUserRepository:
    """Obtenir une instance du repository utilisateur mock"""
    return MockUserRepository()

def get_mock_document_repository() -> MockDocumentRepository:
    """Obtenir une instance du repository document mock"""
    return MockDocumentRepository()

def get_mock_chat_repository() -> MockChatRepository:
    """Obtenir une instance du repository chat mock"""
    return MockChatRepository()

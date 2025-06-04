"""
Database management endpoints (using mock database)
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from ....db.repositories.mock_repositories import (
    MockUserRepository, 
    MockDocumentRepository, 
    MockChatRepository
)

router = APIRouter()


@router.get("/stats")
async def get_database_stats():
    """Get database statistics"""
    try:
        user_repo = MockUserRepository()
        document_repo = MockDocumentRepository()
        chat_repo = MockChatRepository()
        
        # Get collection stats
        user_count = await user_repo.count_users()
        document_count = await document_repo.count_documents()
        chat_count = await chat_repo.count_sessions()
        
        return {
            "total_users": user_count,
            "total_documents": document_count,
            "total_chat_sessions": chat_count,
            "database_type": "mock",
            "status": "healthy"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get database stats: {str(e)}")


@router.get("/users")
async def list_users(skip: int = 0, limit: int = 50):
    """List all users"""
    try:
        user_repo = MockUserRepository()
        users = await user_repo.get_all_users(skip=skip, limit=limit)
        
        return {
            "users": users,
            "count": len(users),
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list users: {str(e)}")


@router.get("/documents")
async def list_documents(skip: int = 0, limit: int = 50):
    """List all documents"""
    try:
        document_repo = MockDocumentRepository()
        documents = await document_repo.get_all_documents(skip=skip, limit=limit)
        
        return {
            "documents": documents,
            "count": len(documents),
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@router.post("/users")
async def create_user(user_data: Dict[str, Any]):
    """Create a new user"""
    try:
        user_repo = MockUserRepository()
        
        # Validation simple
        if not user_data.get("email") or not user_data.get("username"):
            raise HTTPException(status_code=400, detail="Email and username are required")
        
        # Vérifier si l'email existe
        existing_user = await user_repo.get_user_by_email(user_data["email"])
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already exists")
        
        user = await user_repo.create_user(user_data)
        return {"message": "User created successfully", "user": user}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")


@router.post("/documents")
async def create_document(doc_data: Dict[str, Any]):
    """Create a new document"""
    try:
        document_repo = MockDocumentRepository()
        
        # Validation simple
        if not doc_data.get("filename") or not doc_data.get("title"):
            raise HTTPException(status_code=400, detail="Filename and title are required")
        
        document = await document_repo.create_document(doc_data)
        return {"message": "Document created successfully", "document": document}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create document: {str(e)}")


@router.get("/test-connection")
async def test_database_connection():
    """Test database connection"""
    try:
        user_repo = MockUserRepository()
        
        # Test simple: créer et récupérer un utilisateur de test
        test_user = {
            "email": "test@test.com",
            "username": "test_user",
            "full_name": "Test User"
        }
        
        created_user = await user_repo.create_user(test_user)
        found_user = await user_repo.get_user_by_id(created_user["_id"])
        
        return {
            "status": "success",
            "message": "Mock database connection successful",
            "test_result": {
                "created_user_id": created_user["_id"],
                "found_user": found_user is not None
            },
            "database_type": "mock"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

"""
AskRAG FastAPI Application - Version complète avec Mock Database

Main entry point pour l'API AskRAG avec base de données mock complète.
"""

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.api import api_router
from app.db.mock_database import get_mock_database
from app.models.user import UserCreate
from app.models.document import DocumentCreate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app startup and shutdown"""
    # Startup
    logger.info("🚀 Starting AskRAG API with Mock Database...")
    
    try:
        # Initialize mock database
        mock_db = get_mock_database()
        
        # Create sample data if database is empty
        if mock_db.count_documents("users") == 0:
            logger.info("📊 Creating sample data...")
            
            # Create admin user
            admin_user_data = {
                "email": "admin@askrag.com",
                "username": "admin",
                "full_name": "Administrator",
                "is_active": True,
                "is_admin": True
            }
            admin_id = mock_db.insert_one("users", admin_user_data)
            logger.info(f"✅ Created admin user: {admin_id}")
            
            # Create demo user
            demo_user_data = {
                "email": "demo@askrag.com",
                "username": "demo",
                "full_name": "Demo User",
                "is_active": True,
                "is_admin": False
            }
            demo_id = mock_db.insert_one("users", demo_user_data)
            logger.info(f"✅ Created demo user: {demo_id}")
            
            # Create sample documents
            documents_data = [
                {
                    "filename": "guide-askrag.pdf",
                    "title": "Guide d'utilisation AskRAG",
                    "content": "AskRAG est un système de questions-réponses basé sur la récupération d'informations (RAG). Il permet de poser des questions sur vos documents et d'obtenir des réponses précises basées sur le contenu.",
                    "file_type": "pdf",
                    "file_size": 1024*50,
                    "file_path": "/uploads/guide-askrag.pdf",
                    "user_id": admin_id,
                    "processing_status": "completed",
                    "chunk_count": 5,
                    "tags": ["guide", "documentation"],
                    "metadata": {"language": "fr", "category": "documentation"}
                },
                {
                    "filename": "technical-specs.md",
                    "title": "Spécifications techniques",
                    "content": "Architecture: FastAPI + React + MongoDB + FAISS. Backend: Python 3.11+, FastAPI pour l'API REST, Motor pour MongoDB async. Frontend: React 18, TypeScript, Tailwind CSS. Base de données: MongoDB pour les métadonnées, FAISS pour les vecteurs.",
                    "file_type": "markdown",
                    "file_size": 1024*25,
                    "file_path": "/uploads/technical-specs.md",
                    "user_id": admin_id,
                    "processing_status": "completed",
                    "chunk_count": 3,
                    "tags": ["technical", "architecture"],
                    "metadata": {"language": "fr", "category": "technical"}
                },
                {
                    "filename": "user-manual.docx",
                    "title": "Manuel utilisateur",
                    "content": "Pour utiliser AskRAG: 1. Connectez-vous à votre compte. 2. Uploadez vos documents (PDF, Word, TXT). 3. Attendez le traitement automatique. 4. Posez vos questions dans le chat. 5. Obtenez des réponses basées sur vos documents.",
                    "file_type": "docx",
                    "file_size": 1024*75,
                    "file_path": "/uploads/user-manual.docx",
                    "user_id": demo_id,
                    "processing_status": "completed",
                    "chunk_count": 8,
                    "tags": ["manuel", "utilisateur"],
                    "metadata": {"language": "fr", "category": "user-guide"}
                }
            ]
            
            for doc_data in documents_data:
                doc_id = mock_db.insert_one("documents", doc_data)
                logger.info(f"✅ Created document: {doc_data['title']} ({doc_id})")
            
            # Save initial data
            mock_db.save_to_file()
            
        stats = {
            "users": mock_db.count_documents("users"),
            "documents": mock_db.count_documents("documents"),
            "chat_sessions": mock_db.count_documents("chat_sessions")
        }
        logger.info(f"📊 Database stats: {stats}")
        logger.info("✅ Mock database initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        raise
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("🛑 Shutting down AskRAG API...")
    try:
        mock_db = get_mock_database()
        mock_db.save_to_file()
        logger.info("💾 Mock database saved successfully")
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")

# Create FastAPI instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="RAG (Retrieval-Augmented Generation) API for document-based Q&A",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Root endpoint
@app.get("/")
async def root():
    """Welcome endpoint"""
    mock_db = get_mock_database()
    return {
        "message": "AskRAG API",
        "version": "1.0.0",
        "status": "running",
        "database": "mock",
        "docs": f"{settings.API_V1_STR}/docs",
        "stats": {
            "users": mock_db.count_documents("users"),
            "documents": mock_db.count_documents("documents"),
            "chat_sessions": mock_db.count_documents("chat_sessions")
        }
    }

# Health check endpoint
@app.get("/health")
async def health():
    """Health check endpoint"""
    try:
        mock_db = get_mock_database()
        return {
            "status": "healthy",
            "service": "askrag-api",
            "version": "1.0.0",
            "database": {
                "type": "mock",
                "status": "connected",
                "collections": {
                    "users": mock_db.count_documents("users"),
                    "documents": mock_db.count_documents("documents"),
                    "chat_sessions": mock_db.count_documents("chat_sessions")
                }
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "askrag-api",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app_complete:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )

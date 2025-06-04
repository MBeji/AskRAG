"""
Serveur de test RAG - Étape 15.1
Serveur FastAPI minimal pour tester les endpoints RAG
"""

import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Configuration d'environnement pour les tests
os.environ['OPENAI_API_KEY'] = 'sk-test-placeholder-key-for-development'
os.environ['ENVIRONMENT'] = 'development'
os.environ['SECRET_KEY'] = 'test-secret-key-for-development-only'

# Configuration des logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer l'application FastAPI
app = FastAPI(
    title="AskRAG Test Server",
    description="Serveur de test pour les endpoints RAG",
    version="1.0.0-test"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Pour les tests
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Endpoint racine"""
    return {
        "message": "AskRAG Test Server",
        "version": "1.0.0-test",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "rag": "/api/v1/rag/",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check"""
    try:
        # Test des imports
        from app.core.rag_pipeline import rag_pipeline
        from app.core.vector_store import vector_store
        
        return {
            "status": "healthy",
            "service": "askrag-test",
            "rag_pipeline": "ok",
            "vector_store": "ok",
            "test_mode": True
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "test_mode": True
        }

# Endpoint de test simple pour RAG
@app.post("/test/rag/simple")
async def test_rag_simple(question: str = "Qu'est-ce que AskRAG ?"):
    """Test simple du pipeline RAG"""
    try:
        from app.core.rag_pipeline import rag_pipeline
        
        # Ajouter un document de test
        test_doc = """
        AskRAG est une application de RAG (Retrieval-Augmented Generation).
        Elle permet d'analyser des documents et de répondre aux questions.
        L'authentification se fait via JWT.
        Le système utilise FAISS pour la vectorisation.
        """
        
        # Traitement du document
        result = rag_pipeline.process_document(
            file_content=test_doc.encode('utf-8'),
            filename="test.txt",
            document_metadata={'user_id': 'test_user'}
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=f"Erreur traitement: {result.get('error')}")
        
        # Recherche
        search_result = rag_pipeline.search(
            query=question,
            k=3,
            score_threshold=0.1
        )
        
        return {
            "question": question,
            "document_processed": result.get('success', False),
            "chunks_created": result.get('chunking', {}).get('total_chunks', 0),
            "search_results": len(search_result.get('results', [])),
            "results": search_result.get('results', [])[:2],  # Premiers résultats
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Erreur test RAG: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Inclure les endpoints RAG complets
try:
    from app.api.v1.api import api_router
    app.include_router(api_router, prefix="/api/v1")
    logger.info("✓ Endpoints RAG complets inclus")
except Exception as e:
    logger.warning(f"Impossible d'inclure les endpoints complets: {e}")

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Démarrage du serveur de test RAG...")
    print("📍 Endpoints disponibles:")
    print("   - GET  /              : Informations")
    print("   - GET  /health        : Health check")
    print("   - POST /test/rag/simple : Test RAG simple")
    print("   - GET  /docs          : Documentation API")
    print("   - *    /api/v1/rag/*  : Endpoints RAG complets")
    print()
    
    uvicorn.run(
        "test_rag_server:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )

"""
RAG (Retrieval-Augmented Generation) API endpoints - Updated with RAGService.

Endpoints pour le pipeline RAG complet incluant :
- Upload et vectorisation de documents
- Recherche sémantique 
- Génération de réponses avec citations
- Gestion de sessions de chat
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse

from app.models.user import User as UserModel # Use the Beanie User model
from app.services.auth_service import get_current_active_user # Use new auth dependency
from app.services.rag_service import semantic_search_in_documents # New service function
# Remove unused imports if they are specific to old logic
# from app.core.auth import get_current_user # Old
# from app.schemas.rag import SearchResult # Old SearchResult, will redefine or use new
# from app.core.rag_service import rag_service # Old RAGService class instance
# from app.core.rag_pipeline import rag_pipeline # Old pipeline
# from app.db.mock_database import get_mock_database # Not using mock DB for this

from app.schemas.rag import (
    DocumentSearchRequest, # Use this for /search endpoint
    SearchResultItem,      # Use this for search result items
    RAGQueryRequest,       # Use this for /ask endpoint
    QueryResponse,         # Use this for /ask endpoint response
    DocumentUploadResponse,# Keep for existing /upload endpoint
    ChatMessage,           # Keep for existing history endpoints
    ChatSession,           # Keep for existing session endpoints
    # RAGQueryResponse as OldRAGQueryResponse # If needed to distinguish from new QueryResponse
)
# Other Pydantic models if used by remaining old endpoints can be kept or managed separately.

logger = logging.getLogger(__name__)
router = APIRouter()

# NOTE: The "/upload" endpoint previously in this file has been removed.
# Document uploads should be handled by the dedicated /api/v1/documents/upload endpoint,
# which uses the new document processing pipeline (Steps 10-13).

@router.post("/search", response_model=List[SearchResultItem])
async def search_documents_new(
    search_request: DocumentSearchRequest,
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Recherche sémantique dans les documents de l'utilisateur.
    Utilise le nouveau `semantic_search_in_documents` service.
    """
    if not search_request.query.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query cannot be empty")

    try:
        # Note: semantic_search_in_documents currently only uses the query string and user.
        # It does not yet use limit or threshold from DocumentSearchRequest.
        # This could be an enhancement for semantic_search_in_documents.
        search_results = await semantic_search_in_documents(
            query=search_request.query,
            user=current_user
        )
        return search_results
    except RuntimeError as e:
        logger.error(f"Semantic search runtime error for query '{search_request.query}': {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        logger.error(f"Error during semantic search for query '{search_request.query}': {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error performing search")

@router.post("/ask", response_model=QueryResponse)
async def ask_question_with_llm(
    query_request: RAGQueryRequest, # Use RAGQueryRequest from schemas/rag.py
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Receives a query, performs semantic search, and generates an answer using LLM.
    """
    if not query_request.query.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query cannot be empty")

    try:
        from app.services.rag_service import get_answer_from_llm # Import new service function
        
        result = await get_answer_from_llm(query=query_request.query, user=current_user)
        
        # Ensure the result from get_answer_from_llm matches QueryResponse structure.
        # get_answer_from_llm returns {"answer": str, "sources": List[Dict_matching_SearchResultItem]}
        # This should be directly compatible if SearchResultItem is correctly defined and used by get_answer_from_llm.
        return result
        
    except RuntimeError as e: # Catch specific error from service if a sub-service (LLM, vector store) is down
        logger.error(f"RAG query runtime error for query '{query_request.query}': {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        logger.error(f"Error during RAG query for '{query_request.query}': {e}")
        # Consider logging the full stack trace for e in development/debug mode
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error processing your query.")

# Keep the rest of the file (chat history, sessions, etc.) as is for now.
# These will need refactoring to use the new services and models if they are to be kept.

# ===== ÉTAPE 15.5 : Gestion de l'historique des conversations ===== (Still uses mock_db)

@router.get("/history/{session_id}", response_model=List[ChatMessage])
async def get_conversation_history(
    session_id: str,
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """
    Récupère l'historique d'une conversation.
    """
    try:
        mock_db = get_mock_database()
        
        # Vérifier que la session appartient à l'utilisateur
        session = mock_db.find_one("chat_sessions", {
            "session_id": session_id,
            "user_id": str(current_user.id)
        })
        
        if not session:
            raise HTTPException(status_code=404, detail="Session non trouvée")
        
        # Récupérer les messages
        messages_cursor = mock_db.get_collection("chat_messages").find({
            "session_id": session_id,
            "user_id": str(current_user.id)
        }).limit(limit)
        messages = await messages_cursor.to_list(limit)
        
        logger.info(f"Historique récupéré pour session {session_id}, {len(messages)} messages")
        
        return [
            ChatMessage(
                message_id=str(msg.get("_id", "")),
                session_id=session_id,
                content=msg["content"],
                role=msg["role"],
                timestamp=msg["timestamp"],
                sources=msg.get("sources", [])
            )
            for msg in reversed(messages)  # Ordre chronologique
        ]
        
    except Exception as e:
        logger.error(f"Erreur récupération historique session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur d'historique: {str(e)}")


@router.delete("/history/{session_id}")
async def clear_conversation_history(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Efface l'historique d'une conversation.
    """
    try:
        mock_db = get_mock_database()
        
        # Vérifier que la session appartient à l'utilisateur
        session = mock_db.find_one("chat_sessions", {
            "session_id": session_id,
            "user_id": str(current_user.id)
        })
        
        if not session:
            raise HTTPException(status_code=404, detail="Session non trouvée")
        
        # Supprimer les messages
        deleted_count = mock_db.delete_many("chat_messages", {
            "session_id": session_id,
            "user_id": str(current_user.id)
        })
        
        # Mettre à jour le compteur de messages
        mock_db.update_one("chat_sessions", 
            {"session_id": session_id}, 
            {"message_count": 0}
        )
        
        logger.info(f"Historique effacé pour session {session_id}, {deleted_count} messages supprimés")
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Historique effacé avec succès",
                "deleted_messages": deleted_count
            }
        )
        
    except Exception as e:
        logger.error(f"Erreur effacement historique session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur d'effacement: {str(e)}")


# ===== ÉTAPE 16.1 : Gestion des sessions de chat =====

@router.post("/sessions", response_model=ChatSession)
async def create_chat_session(
    title: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Créer une nouvelle session de chat."""
    try:
        import uuid
        from datetime import datetime
        
        session_id = str(uuid.uuid4())
        session_data = {
            "session_id": session_id,
            "user_id": str(current_user.id),
            "title": title or f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "created_at": datetime.now().isoformat(),
            "message_count": 0,
            "status": "active"
        }
        
        mock_db = get_mock_database()
        mock_db.insert_one("chat_sessions", session_data)
        
        logger.info(f"Session de chat créée {session_id} pour user {current_user.email}")
        
        return ChatSession(**session_data)
        
    except Exception as e:
        logger.error(f"Erreur lors de la création de session: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur de création: {str(e)}")


@router.get("/sessions", response_model=List[ChatSession])
async def get_chat_sessions(
    current_user: User = Depends(get_current_user)
):
    """Récupérer les sessions de chat de l'utilisateur."""
    try:
        mock_db = get_mock_database()
        sessions_cursor = mock_db.get_collection("chat_sessions").find({"user_id": str(current_user.id)})
        sessions = await sessions_cursor.to_list(100)
        
        logger.info(f"Sessions récupérées pour user {current_user.email}: {len(sessions)}")
        
        return [ChatSession(**session) for session in sessions]
        
    except Exception as e:
        logger.error(f"Erreur récupération sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur de récupération: {str(e)}")


@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Supprimer une session de chat."""
    try:
        mock_db = get_mock_database()
        
        # Vérifier que la session appartient à l'utilisateur
        session = mock_db.find_one("chat_sessions", {
            "session_id": session_id,
            "user_id": str(current_user.id)
        })
        
        if not session:
            raise HTTPException(status_code=404, detail="Session non trouvée")
        
        # Supprimer les messages associés
        mock_db.delete_many("chat_messages", {"session_id": session_id})
        
        # Supprimer la session
        mock_db.delete_one("chat_sessions", {"session_id": session_id})
        
        logger.info(f"Session {session_id} supprimée pour user {current_user.email}")
        
        return JSONResponse(
            status_code=200,
            content={"message": "Session supprimée avec succès"}
        )
        
    except Exception as e:
        logger.error(f"Erreur suppression session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur de suppression: {str(e)}")


# ===== ÉTAPE 16.2 : Health check et statistiques =====

@router.get("/health")
async def rag_health_check():
    """Health check du système RAG."""
    try:
        health_status = await rag_service.health_check()
        
        return JSONResponse(
            status_code=200 if health_status.get('service') == 'healthy' else 503,
            content=health_status
        )
        
    except Exception as e:
        logger.error(f"Erreur health check RAG: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "service": "unhealthy",
                "error": str(e)
            }
        )


@router.get("/stats")
async def get_rag_statistics(
    current_user: User = Depends(get_current_user)
):
    """Récupère les statistiques du système RAG."""
    try:
        stats = rag_service.get_statistics()
        
        return JSONResponse(
            status_code=200,
            content=stats
        )
        
    except Exception as e:
        logger.error(f"Erreur récupération statistiques RAG: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur statistiques: {str(e)}")

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

from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.rag import (
    RAGQueryRequest, RAGQueryResponse, 
    DocumentUploadResponse, SearchResult,
    ChatSession, ChatMessage
)
from app.core.rag_service import rag_service
from app.core.rag_pipeline import rag_pipeline
from app.core.vector_store import vector_store
from app.db.mock_database import get_mock_database

logger = logging.getLogger(__name__)
router = APIRouter()

# ===== ÉTAPE 15.4 : Pipeline RAG complet avec RAGService =====

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user)
):
    """
    Upload et vectorise un document.
    
    Étapes :
    1. Validation du fichier
    2. Extraction du contenu
    3. Chunking intelligent
    4. Génération d'embeddings
    5. Sauvegarde dans le vector store
    """
    try:
        # Validation du fichier
        if not file.filename:
            raise HTTPException(status_code=400, detail="Nom de fichier requis")
        
        # Vérifier le type de fichier supporté
        supported_types = ['.pdf', '.docx', '.txt', '.md', '.html']
        file_ext = file.filename.lower().split('.')[-1]
        if f'.{file_ext}' not in supported_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Type de fichier non supporté. Types acceptés: {supported_types}"
            )

        # Lire le contenu du fichier
        content = await file.read()
        
        # Traitement avec le RAGService
        result = rag_service.process_document(
            file_content=content,
            filename=file.filename,
            user_id=str(current_user.id),
            document_metadata={
                'file_type': file_ext,
                'title': title or file.filename,
                'user_id': str(current_user.id)
            }
        )
        
        if not result.get('success'):
            raise HTTPException(
                status_code=500,
                detail=f"Erreur de traitement: {result.get('error')}"
            )
        
        # Sauvegarder les métadonnées en base
        mock_db = get_mock_database()
        doc_metadata = {
            "filename": file.filename,
            "title": title or file.filename,
            "file_type": file_ext,
            "user_id": str(current_user.id),
            "chunks_count": result.get("chunking", {}).get("total_chunks", 0),
            "document_id": result.get("document_id"),
            "processing_time": result.get("processing_time", 0),
            "status": "processed"
        }
        doc_id = mock_db.insert_one("documents", doc_metadata)
        
        logger.info(f"Document {file.filename} traité avec succès pour user {current_user.email}")
        
        return DocumentUploadResponse(
            document_id=str(doc_id),
            filename=file.filename,
            title=title or file.filename,
            chunks_count=result.get("chunking", {}).get("total_chunks", 0),
            processing_time=result.get("processing_time", 0),
            status="success",
            message="Document vectorisé avec succès"
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de l'upload du document {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur de traitement: {str(e)}")


@router.post("/search", response_model=List[SearchResult])
async def search_documents(
    query: str,
    limit: int = 5,
    threshold: float = 0.7,
    current_user: User = Depends(get_current_user)
):
    """
    Recherche sémantique dans les documents de l'utilisateur.
    """
    try:
        if not query.strip():
            raise HTTPException(status_code=400, detail="Requête vide")
        
        # Recherche sémantique
        search_response = rag_pipeline.search(
            query=query,
            k=limit,
            score_threshold=threshold,
            filters={'user_id': str(current_user.id)}
        )
        
        if not search_response.get('success'):
            raise HTTPException(
                status_code=500,
                detail=f"Erreur de recherche: {search_response.get('error')}"
            )
        
        results = search_response.get('results', [])
        
        logger.info(f"Recherche '{query}' - {len(results)} résultats pour user {current_user.email}")
        
        return [
            SearchResult(
                chunk_id=result['metadata'].get('chunk_id', f'chunk_{i}'),
                content=result['content'],
                score=result['score'],
                metadata=result.get('metadata', {}),
                document_title=result['metadata'].get('filename', 'Document'),
                page_number=result['metadata'].get('page_number')
            )
            for i, result in enumerate(results)
        ]
        
    except Exception as e:
        logger.error(f"Erreur lors de la recherche '{query}': {e}")
        raise HTTPException(status_code=500, detail=f"Erreur de recherche: {str(e)}")


@router.post("/ask", response_model=RAGQueryResponse)
async def ask_question(
    request: RAGQueryRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Pose une question et obtient une réponse générée par RAG.
    
    Pipeline complet avec RAGService :
    1. Recherche sémantique des chunks pertinents
    2. Génération de réponse avec LLM
    3. Extraction des citations
    4. Formatage de la réponse finale
    """
    try:
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question vide")
        
        # Récupération du contexte de conversation si session fournie
        conversation_history = []
        if request.session_id:
            conversation_history = rag_service.get_conversation_context(
                session_id=request.session_id,
                max_messages=10
            )
        
        # Génération de réponse avec RAGService
        response = await rag_service.ask(
            query=request.question,
            user_id=str(current_user.id),
            session_id=request.session_id,
            conversation_history=conversation_history,
            filters={'user_id': str(current_user.id)},
            include_citations=True,
            max_results=request.max_chunks or 5,
            score_threshold=0.6
        )
        
        if not response.get('success'):
            raise HTTPException(
                status_code=500,
                detail=f"Erreur de génération: {response.get('error')}"
            )
        
        # Sauvegarder l'historique si session fournie
        if request.session_id:
            rag_service.save_conversation(
                query=request.question,
                answer=response["answer"],
                sources=response.get("sources", []),
                user_id=str(current_user.id),
                session_id=request.session_id,
                metadata=response.get("metadata", {})
            )
        
        logger.info(f"Question RAG traitée pour user {current_user.email}, session {request.session_id}")
        
        return RAGQueryResponse(
            answer=response["answer"],
            sources=response.get("sources", []),
            citations=response.get("citations", []),
            confidence=0.8,  # À calculer dynamiquement
            processing_time=response.get("metadata", {}).get("response_time", 0),
            session_id=request.session_id,
            chunk_count=response.get("metadata", {}).get("sources_count", 0)
        )
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement de la question RAG: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur de génération: {str(e)}")


# ===== ÉTAPE 15.5 : Gestion de l'historique des conversations =====

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

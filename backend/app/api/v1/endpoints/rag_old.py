"""
RAG (Retrieval-Augmented Generation) API endpoints.

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
from app.core.rag_pipeline import rag_pipeline
from app.core.rag_service import rag_service
from app.core.vector_store import vector_store
from app.db.mock_database import get_mock_database

logger = logging.getLogger(__name__)
router = APIRouter()

# ===== ÉTAPE 14.8.1 : Endpoints RAG de base =====

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
        
        # Traitement avec le pipeline RAG
        result = rag_pipeline.process_document(
            file_content=content,
            filename=file.filename,
            document_metadata={
                'file_type': file_ext,
                'title': title or file.filename,
                'user_id': str(current_user.id)
            }
        )
        
        # Sauvegarder les métadonnées en base
        mock_db = get_mock_database()
        doc_metadata = {
            "filename": file.filename,
            "title": title or file.filename,
            "file_type": file_ext,
            "user_id": str(current_user.id),
            "chunks_count": result["chunking"]["total_chunks"],
            "vector_ids": result["vectorization"]["chunk_ids"],
            "processing_time": result["processing_time_seconds"],
            "status": "processed"
        }
        doc_id = mock_db.insert_one("documents", doc_metadata)
        
        logger.info(f"Document {file.filename} traité avec succès pour user {current_user.email}")
        
        return DocumentUploadResponse(
            document_id=str(doc_id),
            filename=file.filename,
            title=title or file.filename,
            chunks_count=result["chunking"]["total_chunks"],
            processing_time=result["processing_time_seconds"],
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
    try:        if not query.strip():
            raise HTTPException(status_code=400, detail="Requête vide")
        
        # Recherche sémantique
        search_response = rag_pipeline.search(
            query=query,
            k=limit,
            score_threshold=threshold,
            filter_metadata={'user_id': str(current_user.id)}
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
    
    Pipeline complet :
    1. Recherche sémantique des chunks pertinents
    2. Génération de réponse avec LLM
    3. Extraction des citations
    4. Formatage de la réponse finale
    """
    try:
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question vide")
          # Génération de réponse avec RAG
        response = await rag_pipeline.generate_answer_with_llm(
            question=request.question,
            user_id=str(current_user.id),
            session_id=request.session_id,
            max_chunks=request.max_chunks or 5,
            temperature=request.temperature or 0.7
        )
        
        # Sauvegarder l'historique si session fournie
        if request.session_id:
            mock_db = get_mock_database()
            
            # Message utilisateur
            mock_db.insert_one("chat_messages", {
                "session_id": request.session_id,
                "user_id": str(current_user.id),
                "content": request.question,
                "role": "user",
                "timestamp": response["timestamp"]
            })
            
            # Message assistant
            mock_db.insert_one("chat_messages", {
                "session_id": request.session_id,
                "user_id": str(current_user.id),
                "content": response["answer"],
                "role": "assistant",
                "sources": response.get("sources", []),
                "timestamp": response["timestamp"]
            })
        
        logger.info(f"Question RAG traitée pour user {current_user.email}, session {request.session_id}")
        
        return RAGQueryResponse(
            answer=response["answer"],
            sources=response.get("sources", []),
            confidence=response.get("confidence", 0.8),
            processing_time=response.get("processing_time", 0),
            session_id=request.session_id,
            chunk_count=response.get("chunk_count", 0)
        )
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement de la question RAG: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur de génération: {str(e)}")


# ===== ÉTAPE 14.8.2 : Gestion des sessions de chat =====

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
        sessions = mock_db.find_many("chat_sessions", {"user_id": str(current_user.id)})
        
        return [ChatSession(**session) for session in sessions]
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur de récupération: {str(e)}")


@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessage])
async def get_session_messages(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Récupérer les messages d'une session."""
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
        messages = mock_db.find_many("chat_messages", {
            "session_id": session_id,
            "user_id": str(current_user.id)
        })
        
        return [ChatMessage(**message) for message in messages]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des messages: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur de récupération: {str(e)}")


# ===== ÉTAPE 14.8.3 : Endpoints de gestion =====

@router.get("/status")
async def get_rag_status():
    """Status du système RAG."""
    try:
        # Vérifier les services
        vector_status = vector_store.get_status()
        
        return {
            "status": "healthy",
            "vector_store": vector_status,
            "pipeline": "ready",
            "services": {
                "embeddings": "online",
                "chunker": "online",
                "extractor": "online",
                "llm": "online"
            }
        }
        
    except Exception as e:
        logger.error(f"Erreur lors du check de statut RAG: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Supprimer un document et ses vecteurs."""
    try:
        mock_db = get_mock_database()
        
        # Vérifier que le document appartient à l'utilisateur
        document = mock_db.find_one("documents", {
            "_id": document_id,
            "user_id": str(current_user.id)
        })
        
        if not document:
            raise HTTPException(status_code=404, detail="Document non trouvé")
        
        # Supprimer les vecteurs
        if "vector_ids" in document:
            await vector_store.delete_vectors(document["vector_ids"])
        
        # Supprimer le document de la base
        mock_db.delete_one("documents", {"_id": document_id})
        
        logger.info(f"Document {document_id} supprimé pour user {current_user.email}")
        
        return {"message": "Document supprimé avec succès"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la suppression du document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur de suppression: {str(e)}")

"""
Schémas Pydantic pour les endpoints RAG.

Définit les modèles de données pour les requêtes et réponses
du système RAG (Retrieval-Augmented Generation).
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# ===== SCHÉMAS POUR LES REQUÊTES RAG =====

class RAGQueryRequest(BaseModel):
    """Requête pour poser une question avec RAG."""
    question: str = Field(..., min_length=1, max_length=1000, description="Question à poser")
    session_id: Optional[str] = Field(None, description="ID de session pour l'historique")
    max_chunks: Optional[int] = Field(5, ge=1, le=20, description="Nombre max de chunks à utiliser")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="Température pour la génération")
    include_sources: bool = Field(True, description="Inclure les sources dans la réponse")

    class Config:
        schema_extra = {
            "example": {
                "question": "Comment fonctionne l'authentification dans cette application ?",
                "session_id": "uuid-session-123",
                "max_chunks": 5,
                "temperature": 0.7,
                "include_sources": True
            }
        }

# Added/updated for Step 14/15 RAG flow
class SearchResultItem(BaseModel):
    """Schema for an item in search results list."""
    document_id: str = Field(..., description="MongoDB ID of the source document.")
    chunk_index: int = Field(..., ge=0, description="Index of the chunk within the document.")
    chunk_text: str = Field(..., description="Text content of the chunk.")
    source_filename: str = Field(..., description="Original filename of the source document.")
    score: Optional[float] = Field(None, description="Relevance score from FAISS (lower is better for L2, higher for IP/cosine).")
    upload_date: Optional[datetime] = Field(None, description="Upload date of the source document.")

    class Config:
        from_attributes = True


# Extend RAGQueryRequest from Step 15 to include session_id for Step 21
class RAGQueryRequest(BaseModel): # Was defined in endpoints/rag.py, standardizing here
    query: str = Field(..., min_length=1, description="User query for RAG system.")
    session_id: Optional[PydanticObjectId] = Field(None, description="Optional ID of an existing chat session.")
    # max_chunks, temperature etc. from old RAGQueryRequest can be added back if needed for per-query override

class QueryResponse(BaseModel): # Renamed from OldRAGQueryResponse for clarity
    """Schema for the response from the /ask endpoint."""
    answer: str = Field(..., description="LLM-generated answer.")
    sources: List[SearchResultItem] = Field(..., description="List of source chunks used for the answer.")
    session_id: PydanticObjectId = Field(..., description="ID of the chat session this interaction belongs to.")


    class Config:
        # PydanticObjectId needs arbitrary_types_allowed for direct use if not stringified first
        arbitrary_types_allowed = True
        json_encoders = {
            PydanticObjectId: str # Ensure PydanticObjectId is serialized to string
        }
        schema_extra = {
            "example": {
                "answer": "The capital of France is Paris, based on the provided documents.",
                "sources": [
                    {
                        "document_id": "doc_123",
                        "chunk_index": 0,
                        "chunk_text": "Paris is the capital of France...",
                        "source_filename": "france_guide.pdf",
                        "score": 0.95,
                        "upload_date": "2023-01-01T10:00:00Z"
                    }
                ]
            }
        }


class DocumentSearchRequest(BaseModel):
    """Requête pour la recherche sémantique."""
    query: str = Field(..., min_length=1, max_length=500, description="Requête de recherche")
    limit: int = Field(5, ge=1, le=50, description="Nombre de résultats à retourner")
    threshold: float = Field(0.7, ge=0.0, le=1.0, description="Seuil de similarité minimum")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "authentification JWT",
                "limit": 5,
                "threshold": 0.7
            }
        }


# ===== SCHÉMAS POUR LES RÉPONSES RAG =====

class DocumentChunk(BaseModel):
    """Chunk de document avec métadonnées."""
    chunk_id: str = Field(..., description="ID unique du chunk")
    content: str = Field(..., description="Contenu textuel du chunk")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Métadonnées du chunk")
    document_id: Optional[str] = Field(None, description="ID du document source")
    document_title: Optional[str] = Field(None, description="Titre du document source")
    page_number: Optional[int] = Field(None, description="Numéro de page si applicable")
    chunk_index: Optional[int] = Field(None, description="Index du chunk dans le document")


class SearchResult(BaseModel):
    """Résultat de recherche sémantique."""
    chunk_id: str = Field(..., description="ID du chunk trouvé")
    content: str = Field(..., description="Contenu du chunk")
    score: float = Field(..., ge=0.0, le=1.0, description="Score de similarité")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Métadonnées")
    document_title: Optional[str] = Field(None, description="Titre du document")
    page_number: Optional[int] = Field(None, description="Numéro de page")
    
    class Config:
        schema_extra = {
            "example": {
                "chunk_id": "doc123_chunk_5",
                "content": "L'authentification JWT permet de sécuriser les API...",
                "score": 0.85,
                "metadata": {"chunk_type": "paragraph", "tokens": 150},
                "document_title": "Guide d'authentification",
                "page_number": 12
            }
        }


class SourceCitation(BaseModel):
    """Citation d'une source dans une réponse RAG."""
    chunk_id: str = Field(..., description="ID du chunk source")
    document_title: str = Field(..., description="Titre du document")
    page_number: Optional[int] = Field(None, description="Numéro de page")
    excerpt: str = Field(..., max_length=200, description="Extrait pertinent")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Score de pertinence")


class Citation(BaseModel):
    """Citation avec position dans le texte - Étape 15.3."""
    citation_id: str = Field(..., description="ID unique de la citation")
    source_chunk_id: str = Field(..., description="ID du chunk source")
    document_title: str = Field(..., description="Titre du document source")
    page_number: Optional[int] = Field(None, description="Numéro de page")
    position_start: int = Field(..., ge=0, description="Position de début dans le texte")
    position_end: int = Field(..., ge=0, description="Position de fin dans le texte")
    cited_text: str = Field(..., description="Texte cité")
    context: str = Field(..., max_length=300, description="Contexte de la citation")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confiance de la citation")
    citation_type: str = Field(default="direct", description="Type: 'direct', 'paraphrase', 'reference'")


class RAGQueryResponse(BaseModel):
    """Réponse complète à une question RAG."""
    answer: str = Field(..., description="Réponse générée")
    sources: List[SourceCitation] = Field(default_factory=list, description="Sources utilisées")
    citations: List[Citation] = Field(default_factory=list, description="Citations extraites")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confiance dans la réponse")
    processing_time: float = Field(..., ge=0.0, description="Temps de traitement en secondes")
    session_id: Optional[str] = Field(None, description="ID de session")
    chunk_count: int = Field(..., ge=0, description="Nombre de chunks utilisés")
    
    class Config:
        schema_extra = {
            "example": {
                "answer": "L'authentification JWT dans cette application utilise...",
                "sources": [
                    {
                        "chunk_id": "doc123_chunk_5",
                        "document_title": "Guide d'authentification",
                        "page_number": 12,
                        "excerpt": "JWT permet de sécuriser les API...",
                        "relevance_score": 0.85
                    }
                ],
                "confidence": 0.9,
                "processing_time": 1.5,
                "session_id": "uuid-session-123",
                "chunk_count": 3
            }
        }


class DocumentUploadResponse(BaseModel):
    """Réponse après upload d'un document."""
    document_id: str = Field(..., description="ID du document créé")
    filename: str = Field(..., description="Nom du fichier")
    title: str = Field(..., description="Titre du document")
    chunks_count: int = Field(..., ge=0, description="Nombre de chunks créés")
    processing_time: float = Field(..., ge=0.0, description="Temps de traitement")
    status: str = Field(..., description="Statut du traitement")
    message: str = Field(..., description="Message de confirmation")
    
    class Config:
        schema_extra = {
            "example": {
                "document_id": "doc_12345",
                "filename": "guide.pdf",
                "title": "Guide d'utilisation",
                "chunks_count": 45,
                "processing_time": 12.3,
                "status": "success",
                "message": "Document vectorisé avec succès"
            }
        }


# ===== SCHÉMAS POUR LES SESSIONS DE CHAT =====

class ChatMessage(BaseModel):
    """Message dans une session de chat."""
    message_id: Optional[str] = Field(None, description="ID du message")
    session_id: str = Field(..., description="ID de la session")
    user_id: str = Field(..., description="ID de l'utilisateur")
    content: str = Field(..., description="Contenu du message")
    role: str = Field(..., description="Rôle: 'user' ou 'assistant'")
    sources: Optional[List[SourceCitation]] = Field(None, description="Sources si rôle assistant")
    timestamp: str = Field(..., description="Timestamp ISO du message")
    
    class Config:
        schema_extra = {
            "example": {
                "message_id": "msg_123",
                "session_id": "session_456",
                "user_id": "user_789",
                "content": "Comment fonctionne l'authentification ?",
                "role": "user",
                "timestamp": "2025-05-30T10:30:00"
            }
        }


class ChatSession(BaseModel):
    """Session de chat RAG."""
    session_id: str = Field(..., description="ID unique de la session")
    user_id: str = Field(..., description="ID de l'utilisateur")
    title: str = Field(..., description="Titre de la session")
    created_at: str = Field(..., description="Date de création ISO")
    updated_at: Optional[str] = Field(None, description="Date de dernière mise à jour")
    message_count: int = Field(0, ge=0, description="Nombre de messages")
    status: str = Field("active", description="Statut: 'active', 'archived', 'deleted'")
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "session_456",
                "user_id": "user_789",
                "title": "Questions sur l'authentification",
                "created_at": "2025-05-30T10:00:00",
                "message_count": 6,
                "status": "active"
            }
        }


class CreateSessionRequest(BaseModel):
    """Requête pour créer une session."""
    title: Optional[str] = Field(None, max_length=100, description="Titre de la session")
    
    class Config:
        schema_extra = {
            "example": {
                "title": "Nouvelle discussion"
            }
        }


# ===== SCHÉMAS POUR LA GESTION DES DOCUMENTS =====

class DocumentMetadata(BaseModel):
    """Métadonnées d'un document."""
    document_id: str = Field(..., description="ID du document")
    filename: str = Field(..., description="Nom du fichier")
    title: str = Field(..., description="Titre du document")
    file_type: str = Field(..., description="Type de fichier")
    file_size: Optional[int] = Field(None, description="Taille en octets")
    upload_date: str = Field(..., description="Date d'upload ISO")
    chunks_count: int = Field(..., ge=0, description="Nombre de chunks")
    status: str = Field(..., description="Statut: 'processing', 'processed', 'error'")
    user_id: str = Field(..., description="ID du propriétaire")
    
    class Config:
        schema_extra = {
            "example": {
                "document_id": "doc_123",
                "filename": "guide.pdf",
                "title": "Guide d'utilisation",
                "file_type": "pdf",
                "file_size": 2048576,
                "upload_date": "2025-05-30T09:00:00",
                "chunks_count": 45,
                "status": "processed",
                "user_id": "user_789"
            }
        }


class RAGStatus(BaseModel):
    """Status du système RAG."""
    status: str = Field(..., description="Statut global")
    vector_store: Dict[str, Any] = Field(..., description="Statut du vector store")
    pipeline: str = Field(..., description="Statut du pipeline")
    services: Dict[str, str] = Field(..., description="Statut des services")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "vector_store": {
                    "collection": "askrag_documents",
                    "total_vectors": 1250,
                    "dimension": 1536
                },
                "pipeline": "ready",
                "services": {
                    "embeddings": "online",
                    "chunker": "online",
                    "extractor": "online",
                    "llm": "online"
                }
            }
        }

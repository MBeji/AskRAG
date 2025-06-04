"""
ChromaDB Vector Store Service for AskRAG
Handles document embeddings storage and retrieval with ChromaDB
"""
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import chromadb
from chromadb.config import Settings
from chromadb.api.models.Collection import Collection
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class VectorStore:
    """ChromaDB Vector Store for document embeddings"""
    
    def __init__(self):
        self.client = None
        self.collections = {}
        self.persist_directory = Path(settings.CHROMA_PERSIST_DIR if hasattr(settings, 'CHROMA_PERSIST_DIR') else "data/chroma_db")
        self.collection_prefix = "askrag_user_"
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize ChromaDB client with proper configuration"""
        try:
            # Ensure persist directory exists
            self.persist_directory.mkdir(parents=True, exist_ok=True)
            
            # Initialize ChromaDB client
            self.client = chromadb.Client(Settings(
                persist_directory=str(self.persist_directory),
                anonymized_telemetry=False
            ))
            
            logger.info(f"ChromaDB initialized successfully at {self.persist_directory}")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            self.client = None
    
    def _get_collection_name(self, user_id: str) -> str:
        """Get collection name for a user"""
        return f"{self.collection_prefix}{user_id}"
    
    def get_or_create_collection(self, user_id: str) -> Optional[Collection]:
        """Get or create a collection for a user"""
        if not self.client:
            logger.error("ChromaDB client not initialized")
            return None
        
        collection_name = self._get_collection_name(user_id)
        
        try:
            # Check if collection exists in cache
            if collection_name in self.collections:
                return self.collections[collection_name]
            
            # Get or create collection
            collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"user_id": user_id}
            )
            
            # Cache collection
            self.collections[collection_name] = collection
            logger.info(f"Collection {collection_name} ready")
            
            return collection
            
        except Exception as e:
            logger.error(f"Failed to get/create collection {collection_name}: {e}")
            return None
    
    def add_document_embeddings(
        self, 
        user_id: str, 
        document_id: str, 
        chunks: List[str], 
        embeddings: List[List[float]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add document embeddings to vector store"""
        if not chunks or not embeddings or len(chunks) != len(embeddings):
            logger.error("Invalid chunks or embeddings data")
            return False
        
        collection = self.get_or_create_collection(user_id)
        if not collection:
            return False
        
        try:
            # Prepare IDs and metadata
            ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]
            metadatas = []
            
            for i in range(len(chunks)):
                chunk_metadata = {
                    "document_id": document_id,
                    "chunk_id": i,
                    "chunk_size": len(chunks[i]),
                    "user_id": user_id
                }
                if metadata:
                    chunk_metadata.update(metadata)
                metadatas.append(chunk_metadata)
            
            # Add to collection
            collection.add(
                embeddings=embeddings,
                documents=chunks,
                ids=ids,
                metadatas=metadatas
            )
            
            # Persist changes
            self.client.persist()
            
            logger.info(f"Added {len(chunks)} chunks for document {document_id} to vector store")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add embeddings for document {document_id}: {e}")
            return False
    
    def search_similar_chunks(
        self, 
        user_id: str, 
        query_embedding: List[float],
        n_results: int = 5,
        document_filter: Optional[str] = None,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search for similar chunks in vector store"""
        collection = self.get_or_create_collection(user_id)
        if not collection:
            return []
        
        try:
            # Prepare query filters
            where_clause = {}
            if document_filter:
                where_clause["document_id"] = document_filter
            
            # Perform similarity search
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_clause if where_clause else None,
                include=["documents", "metadatas", "distances"]
            )
            
            # Process results
            similar_chunks = []
            if results and results.get("documents"):
                documents = results["documents"][0]
                metadatas = results.get("metadatas", [[]])[0]
                distances = results.get("distances", [[]])[0]
                
                for i, (doc, metadata, distance) in enumerate(zip(documents, metadatas, distances)):
                    # Calculate similarity score (ChromaDB uses distance)
                    similarity_score = 1 - distance  # Convert distance to similarity
                    
                    if similarity_score >= similarity_threshold:
                        similar_chunks.append({
                            "chunk_text": doc,
                            "metadata": metadata,
                            "similarity_score": similarity_score,
                            "distance": distance
                        })
            
            logger.info(f"Found {len(similar_chunks)} similar chunks for user {user_id}")
            return similar_chunks
            
        except Exception as e:
            logger.error(f"Failed to search similar chunks: {e}")
            return []
    
    def delete_document(self, user_id: str, document_id: str) -> bool:
        """Delete all chunks of a document from vector store"""
        collection = self.get_or_create_collection(user_id)
        if not collection:
            return False
        
        try:
            # Get all IDs for this document
            results = collection.get(
                where={"document_id": document_id},
                include=["metadatas"]
            )
            
            if results and results.get("ids"):
                ids_to_delete = results["ids"]
                collection.delete(ids=ids_to_delete)
                self.client.persist()
                
                logger.info(f"Deleted {len(ids_to_delete)} chunks for document {document_id}")
                return True
            
            return True  # Document not found, consider as success
            
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            return False
    
    def get_collection_stats(self, user_id: str) -> Dict[str, Any]:
        """Get statistics for user's collection"""
        collection = self.get_or_create_collection(user_id)
        if not collection:
            return {}
        
        try:
            # Get collection count
            count = collection.count()
            
            # Get unique documents
            results = collection.get(include=["metadatas"])
            unique_docs = set()
            if results and results.get("metadatas"):
                for metadata in results["metadatas"]:
                    if "document_id" in metadata:
                        unique_docs.add(metadata["document_id"])
            
            return {
                "total_chunks": count,
                "unique_documents": len(unique_docs),
                "collection_name": self._get_collection_name(user_id)
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {}
    
    def health_check(self) -> Dict[str, Any]:
        """Check vector store health"""
        try:
            if not self.client:
                return {"status": "error", "message": "ChromaDB client not initialized"}
            
            # Try to list collections
            collections = self.client.list_collections()
            
            return {
                "status": "healthy",
                "collections_count": len(collections),
                "persist_directory": str(self.persist_directory),
                "client_initialized": True
            }
            
        except Exception as e:
            return {
                "status": "error", 
                "message": str(e),
                "client_initialized": self.client is not None
            }

# Global instance
_vector_store = None

def get_vector_store() -> VectorStore:
    """Get global vector store instance"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store

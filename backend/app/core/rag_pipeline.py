"""
Pipeline RAG Principal
Étape 14.7: Service RAG complet avec extraction, chunking, vectorisation et recherche
Étape 15.2: Intégration LLM service
"""

import os
import logging
import asyncio
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime
from pathlib import Path
import json

from .document_extractor import DocumentExtractor, document_extractor
from .text_chunker import TextChunker, ChunkStrategy, text_chunker
from .vector_store import VectorStore, vector_store
from .embeddings import EmbeddingService, embedding_service
from .llm_service import LLMService, llm_service


class RAGPipeline:
    """
    Pipeline RAG complet pour traitement de documents et recherche sémantique
    Intègre extraction, chunking, vectorisation et recherche
    """
    
    def __init__(self,
                 vector_store: VectorStore = None,
                 document_extractor: DocumentExtractor = None,
                 text_chunker: TextChunker = None,
                 embedding_service: EmbeddingService = None,
                 llm_service: LLMService = None):
        """
        Initialise le pipeline RAG
        
        Args:
            vector_store: Service de vectorisation
            document_extractor: Service d'extraction de documents
            text_chunker: Service de découpage de texte
            embedding_service: Service d'embeddings
            llm_service: Service LLM pour génération de réponses
        """
        # Utiliser les instances globales par défaut si non spécifiées
        self.vector_store = vector_store if vector_store is not None else globals().get('vector_store')
        self.document_extractor = document_extractor if document_extractor is not None else globals().get('document_extractor')
        self.text_chunker = text_chunker if text_chunker is not None else globals().get('text_chunker')
        self.embedding_service = embedding_service if embedding_service is not None else globals().get('embedding_service')
        self.llm_service = llm_service if llm_service is not None else globals().get('llm_service')
        
        self.logger = logging.getLogger(__name__)
        
        # Statistiques
        self.stats = {
            'documents_processed': 0,
            'chunks_created': 0,
            'embeddings_generated': 0,
            'searches_performed': 0,
            'last_operation': None
        }
    
    def process_document(self, 
                        file_content: bytes, 
                        filename: str, 
                        document_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Traite un document complet : extraction, chunking, vectorisation et stockage
        
        Args:
            file_content: Contenu du fichier en bytes
            filename: Nom du fichier
            document_metadata: Métadonnées du document
            
        Returns:
            Résultat du traitement avec statistiques
        """
        try:
            self.logger.info(f"Début traitement document: {filename}")
            start_time = datetime.now()
            
            # 1. Extraction du texte
            extraction_result = self.document_extractor.extract_text(
                file_content=file_content,
                filename=filename
            )
            
            if not extraction_result.get('success'):
                return {
                    'success': False,
                    'error': f"Erreur extraction: {extraction_result.get('error')}",
                    'stage': 'extraction'
                }
            
            extracted_text = extraction_result.get('text', '')
            if not extracted_text.strip():
                return {
                    'success': False,
                    'error': "Aucun texte extrait du document",
                    'stage': 'extraction'
                }
            
            # 2. Chunking du texte
            chunks_result = self.text_chunker.chunk_text(
                text=extracted_text,
                strategy=ChunkStrategy.SEMANTIC,
                metadata=document_metadata or {}
            )
            
            if not chunks_result.get('success'):
                return {
                    'success': False,
                    'error': f"Erreur chunking: {chunks_result.get('error')}",
                    'stage': 'chunking'
                }
            
            chunks = chunks_result.get('chunks', [])
            if not chunks:
                return {
                    'success': False,
                    'error': "Aucun chunk créé",
                    'stage': 'chunking'
                }
            
            # 3. Génération des embeddings
            embeddings_result = self.embedding_service.generate_embeddings(
                texts=[chunk['content'] for chunk in chunks]
            )
            
            if not embeddings_result.get('success'):
                return {
                    'success': False,
                    'error': f"Erreur embeddings: {embeddings_result.get('error')}",
                    'stage': 'embeddings'
                }
            
            embeddings = embeddings_result.get('embeddings', [])
            if len(embeddings) != len(chunks):
                return {
                    'success': False,
                    'error': f"Nombre d'embeddings ({len(embeddings)}) != nombre de chunks ({len(chunks)})",
                    'stage': 'embeddings'
                }
            
            # 4. Stockage dans le vector store
            storage_result = self.vector_store.add_documents(
                chunks=chunks,
                embeddings=embeddings,
                document_metadata=document_metadata or {}
            )
            
            if not storage_result.get('success'):
                return {
                    'success': False,
                    'error': f"Erreur stockage: {storage_result.get('error')}",
                    'stage': 'storage'
                }
            
            # Mise à jour des statistiques
            processing_time = (datetime.now() - start_time).total_seconds()
            self.stats['documents_processed'] += 1
            self.stats['chunks_created'] += len(chunks)
            self.stats['embeddings_generated'] += len(embeddings)
            self.stats['last_operation'] = datetime.now().isoformat()
            
            self.logger.info(f"Document traité avec succès: {filename} ({len(chunks)} chunks en {processing_time:.2f}s)")
            
            return {
                'success': True,
                'document_id': storage_result.get('document_id'),
                'processing_time': processing_time,
                'extraction': extraction_result,
                'chunking': chunks_result,
                'embeddings': {'count': len(embeddings)},
                'storage': storage_result,
                'stats': self.stats.copy()
            }
            
        except Exception as e:
            self.logger.error(f"Erreur traitement document {filename}: {e}")
            return {
                'success': False,
                'error': str(e),
                'stage': 'pipeline'
            }
    
    def search(self, 
               query: str, 
               k: int = 5, 
               score_threshold: float = 0.7,
               filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Recherche sémantique dans les documents vectorisés
        
        Args:
            query: Requête de recherche
            k: Nombre de résultats à retourner
            score_threshold: Seuil de pertinence
            filters: Filtres sur les métadonnées
            
        Returns:
            Résultats de recherche avec scores
        """
        try:
            self.logger.info(f"Recherche: '{query}' (k={k}, threshold={score_threshold})")
            start_time = datetime.now()
            
            # 1. Génération de l'embedding de la requête
            query_embedding_result = self.embedding_service.generate_embeddings([query])
            
            if not query_embedding_result.get('success'):
                return {
                    'success': False,
                    'error': f"Erreur embedding requête: {query_embedding_result.get('error')}"
                }
            
            query_embedding = query_embedding_result.get('embeddings', [])[0]
            
            # 2. Recherche dans le vector store
            search_result = self.vector_store.search(
                query_embedding=query_embedding,
                k=k,
                score_threshold=score_threshold,
                filters=filters
            )
            
            if not search_result.get('success'):
                return {
                    'success': False,
                    'error': f"Erreur recherche: {search_result.get('error')}"
                }
            
            # Mise à jour des statistiques
            search_time = (datetime.now() - start_time).total_seconds()
            self.stats['searches_performed'] += 1
            self.stats['last_operation'] = datetime.now().isoformat()
            
            results = search_result.get('results', [])
            self.logger.info(f"Recherche terminée: {len(results)} résultats en {search_time:.3f}s")
            
            return {
                'success': True,
                'query': query,
                'results': results,
                'search_time': search_time,
                'total_results': len(results),
                'stats': self.stats.copy()
            }
            
        except Exception as e:
            self.logger.error(f"Erreur recherche '{query}': {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_answer_with_llm(self, 
                                query: str, 
                                search_results: List[Dict[str, Any]] = None,
                                conversation_history: List[Dict[str, str]] = None,
                                max_context_length: int = 4000) -> Dict[str, Any]:
        """
        Génère une réponse RAG en utilisant le service LLM
        
        Args:
            query: Question de l'utilisateur
            search_results: Résultats de recherche (si None, recherche automatique)
            conversation_history: Historique de conversation
            max_context_length: Longueur maximale du contexte
            
        Returns:
            Réponse générée avec sources et métadonnées
        """
        try:
            self.logger.info(f"Génération réponse RAG pour: '{query}'")
            start_time = datetime.now()
            
            # 1. Recherche si pas de résultats fournis
            if search_results is None:
                search_result = self.search(query, k=5, score_threshold=0.5)
                if not search_result.get('success'):
                    return {
                        'success': False,
                        'error': f"Erreur recherche pour génération: {search_result.get('error')}"
                    }
                search_results = search_result.get('results', [])
            
            # 2. Préparation du contexte
            context_chunks = []
            sources = []
            
            for result in search_results[:10]:  # Limite à 10 résultats max
                chunk_text = result.get('content', '')
                if len(chunk_text.strip()) > 0:
                    context_chunks.append(chunk_text)
                    sources.append({
                        'content': chunk_text[:200] + "..." if len(chunk_text) > 200 else chunk_text,
                        'score': result.get('score', 0.0),
                        'metadata': result.get('metadata', {})
                    })
            
            if not context_chunks:
                return {
                    'success': False,
                    'error': "Aucun contexte pertinent trouvé pour la question"
                }
            
            # 3. Génération de la réponse avec le LLM
            llm_result = self.llm_service.generate_rag_response(
                query=query,
                context_chunks=context_chunks,
                conversation_history=conversation_history,
                max_context_length=max_context_length
            )
            
            if not llm_result.get('success'):
                return {
                    'success': False,
                    'error': f"Erreur génération LLM: {llm_result.get('error')}"
                }
            
            # Temps de traitement
            generation_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(f"Réponse RAG générée en {generation_time:.2f}s")
            
            return {
                'success': True,
                'query': query,
                'answer': llm_result.get('response', ''),
                'sources': sources,
                'generation_time': generation_time,
                'context_used': len(context_chunks),
                'llm_metadata': llm_result.get('metadata', {}),
                'stats': self.stats.copy()
            }
            
        except Exception as e:
            self.logger.error(f"Erreur génération réponse RAG pour '{query}': {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques du pipeline"""
        return {
            'pipeline_stats': self.stats.copy(),
            'vector_store_stats': self.vector_store.get_statistics() if self.vector_store else {},
            'service_status': {
                'vector_store': self.vector_store is not None,
                'document_extractor': self.document_extractor is not None,
                'text_chunker': self.text_chunker is not None,
                'embedding_service': self.embedding_service is not None,
                'llm_service': self.llm_service is not None
            }
        }


# Instance globale du pipeline RAG
rag_pipeline = RAGPipeline()
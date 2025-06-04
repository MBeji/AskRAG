"""
Pipeline RAG Principal
Étape 14.7: Service RAG complet avec extraction, chunking, vectorisation et recherche
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
        """        # Utiliser les instances globales par défaut
        from . import vector_store as default_vector_store
        from . import document_extractor as default_document_extractor  
        from . import text_chunker as default_text_chunker
        from . import embedding_service as default_embedding_service
        from . import llm_service as default_llm_service
        
        self.vector_store = vector_store or default_vector_store
        self.document_extractor = document_extractor or default_document_extractor
        self.text_chunker = text_chunker or default_text_chunker
        self.embedding_service = embedding_service or default_embedding_service
        self.llm_service = llm_service or default_llm_service
        
        self.logger = logging.getLogger(__name__)
        
        # Statistiques
        self.stats = {
            'documents_processed': 0,
            'chunks_created': 0,
            'vectors_stored': 0,
            'searches_performed': 0,
            'last_activity': None
        }
        
        self.logger.info("RAGPipeline initialisé")
    
    def process_document(self,
                        file_path: Union[str, Path] = None,
                        file_content: bytes = None,
                        filename: str = None,
                        document_metadata: Dict[str, Any] = None,
                        chunk_strategy: ChunkStrategy = ChunkStrategy.HYBRID,
                        chunk_size: int = 1000) -> Dict[str, Any]:
        """
        Traite un document complet: extraction -> chunking -> vectorisation
        
        Args:
            file_path: Chemin du fichier
            file_content: Contenu binaire du fichier
            filename: Nom du fichier
            document_metadata: Métadonnées du document
            chunk_strategy: Stratégie de découpage
            chunk_size: Taille des chunks
            
        Returns:
            Dict: Résultat du traitement avec statistiques
        """
        try:
            start_time = datetime.now()
            self.logger.info(f"Début traitement document: {filename or file_path}")
            
            # 1. Extraction du contenu
            extraction_result = self.document_extractor.extract_content(
                file_path=file_path,
                file_content=file_content,
                filename=filename
            )
            
            if not extraction_result['metadata']['extraction_success']:
                return {
                    'success': False,
                    'error': extraction_result['metadata'].get('error', 'Extraction échouée'),
                    'stage': 'extraction'
                }
            
            content = extraction_result['content']
            file_metadata = extraction_result['metadata']
            
            # 2. Découpage en chunks
            document_id = file_metadata['filename']
            
            # Configurer le chunker si nécessaire
            if chunk_strategy != self.text_chunker.strategy or chunk_size != self.text_chunker.chunk_size:
                chunker = TextChunker(
                    chunk_size=chunk_size,
                    strategy=chunk_strategy
                )
            else:
                chunker = self.text_chunker
            
            chunks = chunker.chunk_text(
                text=content,
                document_id=document_id,
                metadata={
                    **file_metadata,
                    **(document_metadata or {})
                }
            )
            
            if not chunks:
                return {
                    'success': False,
                    'error': 'Aucun chunk généré',
                    'stage': 'chunking'
                }
            
            # 3. Vectorisation et stockage
            stored_chunks = []
            failed_chunks = []
            
            for chunk in chunks:
                try:
                    chunk_id = self.vector_store.add_document(
                        content=chunk['content'],
                        metadata={
                            **chunk['metadata'],
                            'processed_at': datetime.now().isoformat()
                        },
                        document_id=chunk['metadata']['chunk_id']
                    )
                    stored_chunks.append(chunk_id)
                    
                except Exception as e:
                    self.logger.error(f"Erreur stockage chunk: {e}")
                    failed_chunks.append(str(e))
            
            # 4. Statistiques et résultat
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # Mettre à jour les stats
            self.stats['documents_processed'] += 1
            self.stats['chunks_created'] += len(chunks)
            self.stats['vectors_stored'] += len(stored_chunks)
            self.stats['last_activity'] = end_time.isoformat()
            
            result = {
                'success': True,
                'document_id': document_id,
                'processing_time_seconds': processing_time,
                'extraction': {
                    'format': file_metadata['format'],
                    'content_length': file_metadata['content_length'],
                    'size_bytes': file_metadata['size_bytes']
                },
                'chunking': {
                    'strategy': chunk_strategy.value,
                    'total_chunks': len(chunks),
                    'chunk_size': chunk_size,
                    'stats': chunker.get_chunk_stats(chunks)
                },
                'vectorization': {
                    'stored_chunks': len(stored_chunks),
                    'failed_chunks': len(failed_chunks),
                    'chunk_ids': stored_chunks
                }
            }
            
            if failed_chunks:
                result['warnings'] = failed_chunks
            
            self.logger.info(f"Document traité avec succès: {len(stored_chunks)} chunks stockés")
            return result
            
        except Exception as e:
            self.logger.error(f"Erreur traitement document: {e}")
            return {
                'success': False,
                'error': str(e),
                'stage': 'pipeline'
            }
    
    def search(self,
              query: str,
              k: int = 5,
              score_threshold: float = 0.7,
              filter_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Recherche sémantique dans les documents
        
        Args:
            query: Requête de recherche
            k: Nombre de résultats maximum
            score_threshold: Seuil de similarité minimum
            filter_metadata: Filtres sur les métadonnées
            
        Returns:
            Dict: Résultats de recherche avec contexte
        """
        try:
            start_time = datetime.now()
            self.logger.info(f"Recherche: '{query[:50]}...'")
            
            # Recherche dans le vector store
            results = self.vector_store.search(
                query=query,
                k=k,
                score_threshold=score_threshold
            )
            
            # Filtrer par métadonnées si spécifié
            if filter_metadata and results:
                filtered_results = []
                for result in results:
                    metadata = result.get('metadata', {})
                    match = True
                    
                    for key, value in filter_metadata.items():
                        if key not in metadata or metadata[key] != value:
                            match = False
                            break
                    
                    if match:
                        filtered_results.append(result)
                
                results = filtered_results
            
            # Organiser les résultats par document
            document_groups = {}
            for result in results:
                doc_name = result['metadata'].get('filename', 'unknown')
                if doc_name not in document_groups:
                    document_groups[doc_name] = []
                document_groups[doc_name].append(result)
            
            # Statistiques
            end_time = datetime.now()
            search_time = (end_time - start_time).total_seconds()
            
            self.stats['searches_performed'] += 1
            self.stats['last_activity'] = end_time.isoformat()
            
            return {
                'query': query,
                'total_results': len(results),
                'search_time_seconds': search_time,
                'results': results,
                'documents_found': len(document_groups),
                'document_groups': document_groups,
                'parameters': {
                    'k': k,
                    'score_threshold': score_threshold,
                    'filter_metadata': filter_metadata
                }
            }
            
        except Exception as e:
            self.logger.error(f"Erreur recherche: {e}")
            return {
                'query': query,
                'error': str(e),
                'total_results': 0,
                'results': []
            }
    
    def generate_answer(self,
                       query: str,
                       search_results: List[Dict[str, Any]] = None,
                       context_limit: int = 3000,
                       include_sources: bool = True) -> Dict[str, Any]:
        """
        Génère une réponse basée sur les résultats de recherche
        (Prépare le contexte pour un LLM)
        
        Args:
            query: Question de l'utilisateur
            search_results: Résultats de recherche (si None, effectue la recherche)
            context_limit: Limite de caractères pour le contexte
            include_sources: Inclure les sources dans la réponse
            
        Returns:
            Dict: Contexte préparé pour génération de réponse
        """
        try:
            # Effectuer la recherche si pas de résultats fournis
            if search_results is None:
                search_response = self.search(query)
                search_results = search_response.get('results', [])
            
            if not search_results:
                return {
                    'query': query,
                    'context': '',
                    'sources': [],
                    'answer': 'Aucun document pertinent trouvé pour répondre à cette question.',
                    'confidence': 0.0
                }
            
            # Construire le contexte
            context_parts = []
            sources = []
            current_length = 0
            
            for i, result in enumerate(search_results):
                content = result.get('content', '')
                metadata = result.get('metadata', {})
                score = result.get('score', 0.0)
                
                # Vérifier la limite de contexte
                if current_length + len(content) > context_limit:
                    # Tronquer le contenu si nécessaire
                    remaining_space = context_limit - current_length
                    if remaining_space > 100:  # Minimum viable
                        content = content[:remaining_space - 3] + "..."
                    else:
                        break
                
                # Ajouter au contexte
                source_info = f"[Source {i+1}]"
                context_parts.append(f"{source_info}\n{content}\n")
                current_length += len(content) + len(source_info) + 2
                
                # Ajouter aux sources
                if include_sources:
                    sources.append({
                        'index': i + 1,
                        'filename': metadata.get('filename', 'unknown'),
                        'chunk_id': metadata.get('chunk_id', ''),
                        'score': score,
                        'word_count': metadata.get('word_count', 0)
                    })
            
            context = '\n'.join(context_parts)
            
            # Calculer la confiance moyenne
            confidence = sum(r.get('score', 0) for r in search_results[:len(sources)]) / len(sources) if sources else 0.0
            
            return {
                'query': query,
                'context': context,
                'context_length': len(context),
                'sources': sources,
                'confidence': confidence,
                'total_sources': len(search_results),
                'used_sources': len(sources),
                'ready_for_llm': True
            }
            
        except Exception as e:
            self.logger.error(f"Erreur génération réponse: {e}")
            return {
                'query': query,
                'context': '',
                'sources': [],
                'error': str(e),
                'ready_for_llm': False
            }
      async def generate_answer_with_llm(self,
                                     question: str,
                                     user_id: str = None,
                                     session_id: str = None,
                                     max_chunks: int = 5,
                                     temperature: float = 0.7,
                                     conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Génère une réponse complète avec RAG (Retrieval-Augmented Generation).
        
        Args:
            question: Question de l'utilisateur
            user_id: ID de l'utilisateur (pour filtrage)
            session_id: ID de session pour l'historique
            max_chunks: Nombre maximum de chunks à utiliser
            temperature: Température pour la génération LLM
            conversation_history: Historique de conversation
            
        Returns:
            Dict: Réponse générée avec sources et métadonnées
        """
        try:
            start_time = datetime.now()
            self.logger.info(f"Génération de réponse pour: {question[:50]}...")
            
            # 1. Recherche sémantique des chunks pertinents
            search_response = self.search(
                query=question,
                k=max_chunks,
                score_threshold=0.6,
                filter_metadata={'user_id': user_id} if user_id else None
            )
            
            search_results = search_response.get('results', [])
            
            if not search_results:
                return {
                    'answer': "Je n'ai pas trouvé d'informations pertinentes dans vos documents pour répondre à cette question.",
                    'sources': [],
                    'confidence': 0.0,
                    'processing_time': (datetime.now() - start_time).total_seconds(),
                    'timestamp': datetime.now().isoformat(),
                    'chunk_count': 0,
                    'model_used': self.llm_service.model_name,
                    'test_mode': self.llm_service.test_mode
                }
            
            # 2. Préparer le contexte pour le LLM
            context_chunks = []
            sources = []
            
            for i, result in enumerate(search_results):
                context_chunks.append(f"[Source {i+1}] {result['content']}")
                sources.append({
                    'index': i + 1,
                    'chunk_id': result['metadata'].get('chunk_id', f'chunk_{i}'),
                    'document_title': result['metadata'].get('filename', 'Document'),
                    'page_number': result['metadata'].get('page_number'),
                    'excerpt': result['content'][:200] + '...' if len(result['content']) > 200 else result['content'],
                    'relevance_score': result['score']
                })
            
            context = "\n\n".join(context_chunks)
            
            # 3. Génération avec le service LLM
            llm_response = self.llm_service.generate_rag_response(
                question=question,
                context=context,
                conversation_history=conversation_history
            )
            
            # 4. Calculer la confiance basée sur les scores de similarité
            avg_score = sum(r['score'] for r in search_results) / len(search_results)
            confidence = min(avg_score * 1.2, 1.0)  # Boost légèrement la confiance
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                'answer': llm_response.get('answer', 'Erreur lors de la génération'),
                'sources': sources,
                'confidence': confidence,
                'processing_time': processing_time,
                'timestamp': datetime.now().isoformat(),
                'chunk_count': len(search_results),
                'model_used': llm_response.get('model', self.llm_service.model_name),
                'tokens_used': llm_response.get('tokens_used', 0),
                'test_mode': llm_response.get('test_mode', False),
                'search_time': search_response.get('search_time_seconds', 0)
            }
            
            # Ajouter l'erreur si elle existe
            if 'error' in llm_response:
                result['llm_error'] = llm_response['error']
            
            self.logger.info(f"Réponse générée en {processing_time:.2f}s avec {len(sources)} sources")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erreur génération réponse: {e}")
            return {
                'answer': f"Erreur lors de la génération de la réponse: {str(e)}",
                'sources': [],
                'confidence': 0.0,
                'processing_time': (datetime.now() - start_time).total_seconds(),
                'timestamp': datetime.now().isoformat(),
                'chunk_count': 0,
                'error': str(e)
            }

    def delete_document(self, document_id: str) -> Dict[str, Any]:
        """
        Supprime un document et tous ses chunks
        
        Args:
            document_id: ID du document à supprimer
            
        Returns:
            Dict: Résultat de la suppression
        """
        try:
            # Pour l'instant, FAISS ne permet pas de supprimer facilement
            # On pourrait marquer comme supprimé dans les métadonnées
            self.logger.warning(f"Suppression document non implémentée: {document_id}")
            
            return {
                'success': False,
                'error': 'Suppression non implémentée avec FAISS',
                'document_id': document_id
            }
            
        except Exception as e:
            self.logger.error(f"Erreur suppression document: {e}")
            return {
                'success': False,
                'error': str(e),
                'document_id': document_id
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du pipeline"""
        vector_info = self.vector_store.get_collection_info()
        
        return {
            'pipeline_stats': self.stats,
            'vector_store': vector_info,
            'chunker_config': {
                'strategy': self.text_chunker.strategy.value,
                'chunk_size': self.text_chunker.chunk_size,
                'overlap': self.text_chunker.chunk_overlap
            },
            'embedding_stats': self.embedding_service.get_cache_stats(),
            'supported_formats': self.document_extractor.get_supported_formats()
        }
    
    def reset(self) -> Dict[str, Any]:
        """Remet à zéro le pipeline"""
        try:
            # Reset vector store
            self.vector_store.reset_collection()
            
            # Reset stats
            self.stats = {
                'documents_processed': 0,
                'chunks_created': 0,
                'vectors_stored': 0,
                'searches_performed': 0,
                'last_activity': None
            }
            
            # Clear embedding cache
            self.embedding_service.clear_cache()
            
            self.logger.info("Pipeline RAG remis à zéro")
            
            return {
                'success': True,
                'message': 'Pipeline RAG remis à zéro'
            }
            
        except Exception as e:
            self.logger.error(f"Erreur reset pipeline: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Instance globale
rag_pipeline = RAGPipeline()

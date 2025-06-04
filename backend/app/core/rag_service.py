"""
Service RAG Complet - Étape 15.4
Intègre retrieval, LLM et système de citations pour un pipeline RAG complet
"""

import os
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import asyncio

from .rag_pipeline import rag_pipeline
from .citation_system import citation_extractor
from .llm_service import llm_service


class RAGService:
    """
    Service RAG complet qui orchestrate retrieval, LLM et citations
    """
    
    def __init__(self,
                 rag_pipeline=None,
                 citation_extractor=None,
                 llm_service=None):
        """
        Initialise le service RAG complet
        
        Args:
            rag_pipeline: Pipeline RAG pour recherche et vectorisation
            citation_extractor: Extracteur de citations
            llm_service: Service LLM pour génération de réponses
        """
        self.rag_pipeline = rag_pipeline or globals().get('rag_pipeline')
        self.citation_extractor = citation_extractor or globals().get('citation_extractor')
        self.llm_service = llm_service or globals().get('llm_service')
        
        self.logger = logging.getLogger(__name__)
        
        # Statistiques du service
        self.stats = {
            'total_queries': 0,
            'successful_responses': 0,
            'failed_responses': 0,
            'average_response_time': 0.0,
            'total_citations_extracted': 0,
            'last_query_time': None
        }
    
    async def ask(self, 
                  query: str,
                  user_id: str = None,
                  session_id: str = None,
                  conversation_history: List[Dict[str, str]] = None,
                  filters: Dict[str, Any] = None,
                  include_citations: bool = True,
                  max_results: int = 5,
                  score_threshold: float = 0.6) -> Dict[str, Any]:
        """
        Fonction principale pour poser une question au système RAG
        
        Args:
            query: Question de l'utilisateur
            user_id: ID de l'utilisateur
            session_id: ID de session
            conversation_history: Historique de conversation
            filters: Filtres pour la recherche
            include_citations: Inclure les citations dans la réponse
            max_results: Nombre maximum de résultats de recherche
            score_threshold: Seuil de pertinence pour la recherche
            
        Returns:
            Réponse complète avec answer, sources, citations et métadonnées
        """
        try:
            self.logger.info(f"Nouvelle requête RAG: '{query}' (user: {user_id}, session: {session_id})")
            start_time = datetime.now()
            
            # Mise à jour des statistiques
            self.stats['total_queries'] += 1
            self.stats['last_query_time'] = start_time.isoformat()
            
            # 1. Recherche sémantique
            search_result = self.rag_pipeline.search(
                query=query,
                k=max_results,
                score_threshold=score_threshold,
                filters=filters
            )
            
            if not search_result.get('success'):
                self.stats['failed_responses'] += 1
                return {
                    'success': False,
                    'error': f"Erreur recherche: {search_result.get('error')}",
                    'stage': 'search'
                }
            
            search_results = search_result.get('results', [])
            
            if not search_results:
                self.stats['failed_responses'] += 1
                return {
                    'success': False,
                    'error': "Aucun document pertinent trouvé pour cette question",
                    'stage': 'search',
                    'query': query
                }
            
            # 2. Génération de la réponse avec LLM
            llm_result = self.rag_pipeline.generate_answer_with_llm(
                query=query,
                search_results=search_results,
                conversation_history=conversation_history,
                max_context_length=4000
            )
            
            if not llm_result.get('success'):
                self.stats['failed_responses'] += 1
                return {
                    'success': False,
                    'error': f"Erreur génération LLM: {llm_result.get('error')}",
                    'stage': 'llm_generation'
                }
            
            answer = llm_result.get('answer', '')
            sources = llm_result.get('sources', [])
            
            # 3. Extraction des citations (si demandée)
            citations = []
            if include_citations and answer:
                try:
                    citation_result = self.citation_extractor.extract_citations(
                        text=answer,
                        sources=sources
                    )
                    
                    if citation_result.get('success'):
                        citations = citation_result.get('citations', [])
                        self.stats['total_citations_extracted'] += len(citations)
                        self.logger.info(f"Extraites {len(citations)} citations")
                    else:
                        self.logger.warning(f"Erreur extraction citations: {citation_result.get('error')}")
                        
                except Exception as e:
                    self.logger.warning(f"Erreur lors de l'extraction des citations: {e}")
            
            # 4. Préparation de la réponse finale
            response_time = (datetime.now() - start_time).total_seconds()
            
            # Mise à jour des statistiques
            self.stats['successful_responses'] += 1
            if self.stats['successful_responses'] > 0:
                self.stats['average_response_time'] = (
                    (self.stats['average_response_time'] * (self.stats['successful_responses'] - 1) + response_time) /
                    self.stats['successful_responses']
                )
            
            self.logger.info(f"Requête RAG traitée avec succès en {response_time:.2f}s")
            
            return {
                'success': True,
                'query': query,
                'answer': answer,
                'sources': sources,
                'citations': citations,
                'metadata': {
                    'user_id': user_id,
                    'session_id': session_id,
                    'response_time': response_time,
                    'search_results_count': len(search_results),
                    'sources_count': len(sources),
                    'citations_count': len(citations),
                    'timestamp': start_time.isoformat(),
                    'search_metadata': search_result.get('search_time', 0),
                    'llm_metadata': llm_result.get('llm_metadata', {})
                },
                'stats': self.stats.copy()
            }
            
        except Exception as e:
            self.stats['failed_responses'] += 1
            self.logger.error(f"Erreur service RAG pour '{query}': {e}")
            return {
                'success': False,
                'error': str(e),
                'stage': 'service',
                'query': query
            }
    
    def process_document(self,
                        file_content: bytes,
                        filename: str,
                        user_id: str = None,
                        document_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Traite un document pour l'intégrer dans la base de connaissances
        
        Args:
            file_content: Contenu du fichier
            filename: Nom du fichier
            user_id: ID de l'utilisateur
            document_metadata: Métadonnées du document
            
        Returns:
            Résultat du traitement
        """
        try:
            self.logger.info(f"Traitement document: {filename} (user: {user_id})")
            
            # Enrichir les métadonnées
            metadata = document_metadata or {}
            metadata.update({
                'user_id': user_id,
                'uploaded_at': datetime.now().isoformat(),
                'processed_by': 'rag_service'
            })
            
            # Traitement par le pipeline RAG
            result = self.rag_pipeline.process_document(
                file_content=file_content,
                filename=filename,
                document_metadata=metadata
            )
            
            if result.get('success'):
                self.logger.info(f"Document {filename} traité avec succès")
            else:
                self.logger.error(f"Erreur traitement document {filename}: {result.get('error')}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erreur service traitement document {filename}: {e}")
            return {
                'success': False,
                'error': str(e),
                'filename': filename
            }
    
    def get_conversation_context(self, 
                               session_id: str,
                               max_messages: int = 10) -> List[Dict[str, str]]:
        """
        Récupère le contexte de conversation pour une session
        
        Args:
            session_id: ID de session
            max_messages: Nombre maximum de messages à récupérer
            
        Returns:
            Liste des messages de conversation
        """
        try:
            # À implémenter avec la base de données de conversations
            # Pour l'instant, retourne une liste vide
            self.logger.info(f"Récupération contexte conversation session: {session_id}")
            return []
            
        except Exception as e:
            self.logger.error(f"Erreur récupération contexte session {session_id}: {e}")
            return []
    
    def save_conversation(self,
                         query: str,
                         answer: str,
                         sources: List[Dict[str, Any]],
                         user_id: str = None,
                         session_id: str = None,
                         metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Sauvegarde une conversation dans l'historique
        
        Args:
            query: Question posée
            answer: Réponse générée
            sources: Sources utilisées
            user_id: ID utilisateur
            session_id: ID session
            metadata: Métadonnées additionnelles
            
        Returns:
            Résultat de la sauvegarde
        """
        try:
            self.logger.info(f"Sauvegarde conversation (user: {user_id}, session: {session_id})")
            
            # À implémenter avec la base de données
            # Pour l'instant, log seulement
            conversation_data = {
                'query': query,
                'answer': answer,
                'sources_count': len(sources),
                'user_id': user_id,
                'session_id': session_id,
                'timestamp': datetime.now().isoformat(),
                'metadata': metadata or {}
            }
            
            self.logger.info(f"Conversation sauvegardée: {conversation_data}")
            
            return {
                'success': True,
                'conversation_id': f"conv_{datetime.now().timestamp()}",
                'saved_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Erreur sauvegarde conversation: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques du service RAG"""
        return {
            'service_stats': self.stats.copy(),
            'pipeline_stats': self.rag_pipeline.get_statistics() if self.rag_pipeline else {},
            'components_status': {
                'rag_pipeline': self.rag_pipeline is not None,
                'citation_extractor': self.citation_extractor is not None,
                'llm_service': self.llm_service is not None
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé du service RAG"""
        try:
            health_status = {
                'service': 'healthy',
                'components': {},
                'timestamp': datetime.now().isoformat()
            }
            
            # Vérifier les composants
            if self.rag_pipeline:
                health_status['components']['rag_pipeline'] = 'healthy'
            else:
                health_status['components']['rag_pipeline'] = 'missing'
                health_status['service'] = 'degraded'
            
            if self.citation_extractor:
                health_status['components']['citation_extractor'] = 'healthy'
            else:
                health_status['components']['citation_extractor'] = 'missing'
            
            if self.llm_service:
                health_status['components']['llm_service'] = 'healthy'
            else:
                health_status['components']['llm_service'] = 'missing'
                health_status['service'] = 'degraded'
            
            return health_status
            
        except Exception as e:
            return {
                'service': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


# Instance globale du service RAG
rag_service = RAGService()

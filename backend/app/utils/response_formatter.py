"""
Module de formatage des réponses - Étape 16.3.2
Formatage et structuration des réponses des endpoints RAG
"""

import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from fastapi import status
from fastapi.responses import JSONResponse


class ResponseFormatter:
    """
    Formateur principal pour les réponses des endpoints RAG
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def success_response(self, 
                        data: Any, 
                        message: str = "Opération réussie",
                        metadata: Dict[str, Any] = None,
                        status_code: int = status.HTTP_200_OK) -> JSONResponse:
        """
        Crée une réponse de succès standardisée
        
        Args:
            data: Données à retourner
            message: Message de succès
            metadata: Métadonnées additionnelles
            status_code: Code de statut HTTP
            
        Returns:
            JSONResponse formatée
        """
        response_data = {
            "success": True,
            "message": message,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        if metadata:
            response_data["metadata"] = metadata
        
        return JSONResponse(
            status_code=status_code,
            content=response_data
        )
    
    def error_response(self, 
                      error: str, 
                      error_code: str = None,
                      details: Dict[str, Any] = None,
                      status_code: int = status.HTTP_400_BAD_REQUEST) -> JSONResponse:
        """
        Crée une réponse d'erreur standardisée
        
        Args:
            error: Message d'erreur
            error_code: Code d'erreur interne
            details: Détails additionnels sur l'erreur
            status_code: Code de statut HTTP
            
        Returns:
            JSONResponse formatée
        """
        response_data = {
            "success": False,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        
        if error_code:
            response_data["error_code"] = error_code
            
        if details:
            response_data["details"] = details
        
        return JSONResponse(
            status_code=status_code,
            content=response_data
        )
    
    def paginated_response(self, 
                          items: List[Any],
                          page: int,
                          page_size: int,
                          total_items: int,
                          message: str = "Données récupérées avec succès") -> JSONResponse:
        """
        Crée une réponse paginée standardisée
        
        Args:
            items: Liste des éléments de la page actuelle
            page: Numéro de page actuelle (base 1)
            page_size: Taille de page
            total_items: Nombre total d'éléments
            message: Message de succès
            
        Returns:
            JSONResponse formatée avec pagination
        """
        total_pages = (total_items + page_size - 1) // page_size
        
        pagination_metadata = {
            "pagination": {
                "current_page": page,
                "page_size": page_size,
                "total_items": total_items,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1,
                "next_page": page + 1 if page < total_pages else None,
                "previous_page": page - 1 if page > 1 else None
            }
        }
        
        return self.success_response(
            data=items,
            message=message,
            metadata=pagination_metadata
        )
    
    def rag_query_response(self, 
                          answer: str,
                          sources: List[Dict[str, Any]],
                          citations: List[Dict[str, Any]] = None,
                          processing_time: float = 0.0,
                          confidence: float = 0.0,
                          session_id: str = None,
                          query: str = None) -> JSONResponse:
        """
        Formate une réponse de requête RAG
        
        Args:
            answer: Réponse générée
            sources: Sources utilisées
            citations: Citations extraites
            processing_time: Temps de traitement
            confidence: Score de confiance
            session_id: ID de session
            query: Requête originale
            
        Returns:
            JSONResponse formatée pour RAG
        """
        data = {
            "answer": answer,
            "sources": sources,
            "citations": citations or [],
            "confidence": confidence,
            "chunk_count": len(sources)
        }
        
        metadata = {
            "processing_time": processing_time,
            "session_id": session_id,
            "query": query,
            "timestamp": datetime.now().isoformat()
        }
        
        return self.success_response(
            data=data,
            message="Réponse générée avec succès",
            metadata=metadata
        )
    
    def document_upload_response(self, 
                               document_id: str,
                               filename: str,
                               chunks_count: int,
                               processing_time: float) -> JSONResponse:
        """
        Formate une réponse d'upload de document
        
        Args:
            document_id: ID du document créé
            filename: Nom du fichier
            chunks_count: Nombre de chunks créés
            processing_time: Temps de traitement
            
        Returns:
            JSONResponse formatée pour upload
        """
        data = {
            "document_id": document_id,
            "filename": filename,
            "chunks_count": chunks_count,
            "status": "processed"
        }
        
        metadata = {
            "processing_time": processing_time,
            "upload_timestamp": datetime.now().isoformat()
        }
        
        return self.success_response(
            data=data,
            message="Document traité et vectorisé avec succès",
            metadata=metadata,
            status_code=status.HTTP_201_CREATED
        )
    
    def search_results_response(self, 
                              results: List[Dict[str, Any]],
                              query: str,
                              search_time: float) -> JSONResponse:
        """
        Formate une réponse de recherche sémantique
        
        Args:
            results: Résultats de recherche
            query: Requête de recherche
            search_time: Temps de recherche
            
        Returns:
            JSONResponse formatée pour recherche
        """
        metadata = {
            "query": query,
            "results_count": len(results),
            "search_time": search_time,
            "timestamp": datetime.now().isoformat()
        }
        
        return self.success_response(
            data=results,
            message=f"Recherche terminée - {len(results)} résultats trouvés",
            metadata=metadata
        )
    
    def health_check_response(self, 
                            service_status: str,
                            components: Dict[str, str],
                            details: Dict[str, Any] = None) -> JSONResponse:
        """
        Formate une réponse de health check
        
        Args:
            service_status: Statut global ('healthy', 'degraded', 'unhealthy')
            components: Statut des composants
            details: Détails additionnels
            
        Returns:
            JSONResponse formatée pour health check
        """
        data = {
            "status": service_status,
            "components": components
        }
        
        if details:
            data["details"] = details
        
        # Déterminer le code de statut HTTP
        if service_status == "healthy":
            status_code = status.HTTP_200_OK
        elif service_status == "degraded":
            status_code = status.HTTP_200_OK  # Service disponible mais dégradé
        else:
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        
        return JSONResponse(
            status_code=status_code,
            content={
                "success": service_status in ["healthy", "degraded"],
                "message": f"Service {service_status}",
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def statistics_response(self, 
                          stats: Dict[str, Any],
                          component: str = "rag_system") -> JSONResponse:
        """
        Formate une réponse de statistiques
        
        Args:
            stats: Statistiques à retourner
            component: Nom du composant
            
        Returns:
            JSONResponse formatée pour statistiques
        """
        metadata = {
            "component": component,
            "generated_at": datetime.now().isoformat()
        }
        
        return self.success_response(
            data=stats,
            message=f"Statistiques {component} récupérées",
            metadata=metadata
        )
    
    def chat_session_response(self, 
                            session_data: Dict[str, Any],
                            action: str = "created") -> JSONResponse:
        """
        Formate une réponse de session de chat
        
        Args:
            session_data: Données de session
            action: Action effectuée ('created', 'updated', 'deleted')
            
        Returns:
            JSONResponse formatée pour session
        """
        messages = {
            "created": "Session de chat créée avec succès",
            "updated": "Session de chat mise à jour",
            "deleted": "Session de chat supprimée"
        }
        
        status_codes = {
            "created": status.HTTP_201_CREATED,
            "updated": status.HTTP_200_OK,
            "deleted": status.HTTP_200_OK
        }
        
        return self.success_response(
            data=session_data,
            message=messages.get(action, "Opération session effectuée"),
            status_code=status_codes.get(action, status.HTTP_200_OK)
        )
    
    def validation_error_response(self, 
                                field: str, 
                                error: str) -> JSONResponse:
        """
        Formate une réponse d'erreur de validation
        
        Args:
            field: Champ en erreur
            error: Message d'erreur
            
        Returns:
            JSONResponse formatée pour erreur de validation
        """
        return self.error_response(
            error="Erreur de validation",
            error_code="VALIDATION_ERROR",
            details={"field": field, "message": error},
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    def not_found_response(self, 
                          resource: str, 
                          identifier: str = None) -> JSONResponse:
        """
        Formate une réponse de ressource non trouvée
        
        Args:
            resource: Type de ressource
            identifier: Identifiant de la ressource
            
        Returns:
            JSONResponse formatée pour 404
        """
        message = f"{resource} non trouvé"
        if identifier:
            message += f" (ID: {identifier})"
        
        return self.error_response(
            error=message,
            error_code="RESOURCE_NOT_FOUND",
            details={"resource": resource, "identifier": identifier},
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    def rate_limit_response(self, 
                           retry_after: int = 60) -> JSONResponse:
        """
        Formate une réponse de limite de taux dépassée
        
        Args:
            retry_after: Secondes à attendre avant retry
            
        Returns:
            JSONResponse formatée pour 429
        """
        response = self.error_response(
            error="Limite de taux dépassée",
            error_code="RATE_LIMIT_EXCEEDED",
            details={"retry_after": retry_after},
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )
        
        response.headers["Retry-After"] = str(retry_after)
        return response


# Instance globale du formateur
response_formatter = ResponseFormatter()

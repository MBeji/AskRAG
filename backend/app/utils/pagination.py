"""
Système de pagination efficace pour AskRAG
Étape 16.4.3 - Implémenter la pagination efficace
"""

import logging
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic
from datetime import datetime
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
import math

logger = logging.getLogger(__name__)

T = TypeVar('T')

@dataclass
class PaginationInfo:
    """Informations de pagination"""
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool
    next_page: Optional[int]
    previous_page: Optional[int]
    
    @classmethod
    def create(cls, page: int, page_size: int, total_items: int) -> 'PaginationInfo':
        """Crée les informations de pagination"""
        total_pages = math.ceil(total_items / page_size) if page_size > 0 else 0
        
        return cls(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
            next_page=page + 1 if page < total_pages else None,
            previous_page=page - 1 if page > 1 else None
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return asdict(self)

@dataclass
class PaginatedResponse(Generic[T]):
    """Réponse paginée générique"""
    items: List[T]
    pagination: PaginationInfo
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire pour l'API"""
        return {
            "items": self.items,
            "pagination": self.pagination.to_dict(),
            "metadata": self.metadata or {}
        }

class PaginationParams:
    """Paramètres de pagination avec validation"""
    
    def __init__(self, 
                 page: int = 1, 
                 page_size: int = 20,
                 max_page_size: int = 100,
                 default_page_size: int = 20):
        self.page = max(1, page)
        self.page_size = min(max(1, page_size), max_page_size)
        self.max_page_size = max_page_size
        self.default_page_size = default_page_size
    
    @property
    def offset(self) -> int:
        """Décalage pour la requête (page - 1) * page_size"""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Limite pour la requête"""
        return self.page_size
    
    @classmethod
    def from_request(cls, page: Any = None, page_size: Any = None, **kwargs) -> 'PaginationParams':
        """Crée depuis les paramètres de requête HTTP"""
        try:
            page = int(page) if page else 1
        except (TypeError, ValueError):
            page = 1
        
        try:
            page_size = int(page_size) if page_size else kwargs.get('default_page_size', 20)
        except (TypeError, ValueError):
            page_size = kwargs.get('default_page_size', 20)
        
        return cls(page=page, page_size=page_size, **kwargs)

class CursorPagination:
    """Pagination par curseur pour de meilleures performances sur de gros datasets"""
    
    def __init__(self, cursor_field: str = "created_at", page_size: int = 20):
        self.cursor_field = cursor_field
        self.page_size = page_size
    
    def encode_cursor(self, item: Dict[str, Any]) -> str:
        """Encode un curseur depuis un élément"""
        import base64
        import json
        
        cursor_value = item.get(self.cursor_field)
        if isinstance(cursor_value, datetime):
            cursor_value = cursor_value.isoformat()
        
        cursor_data = {
            "field": self.cursor_field,
            "value": cursor_value,
            "id": str(item.get("_id", ""))
        }
        
        cursor_json = json.dumps(cursor_data, sort_keys=True)
        return base64.urlsafe_b64encode(cursor_json.encode()).decode()
    
    def decode_cursor(self, cursor: str) -> Dict[str, Any]:
        """Décode un curseur"""
        import base64
        import json
        
        try:
            cursor_json = base64.urlsafe_b64decode(cursor.encode()).decode()
            cursor_data = json.loads(cursor_json)
            
            # Convertir la date si nécessaire
            if cursor_data.get("field") == "created_at":
                cursor_data["value"] = datetime.fromisoformat(cursor_data["value"])
            
            return cursor_data
        except Exception as e:
            logger.error(f"Erreur décodage curseur: {e}")
            return {}
    
    def build_query(self, cursor: Optional[str] = None, direction: str = "next") -> Dict[str, Any]:
        """Construit la requête MongoDB avec curseur"""
        query = {}
        
        if cursor:
            cursor_data = self.decode_cursor(cursor)
            if cursor_data:
                field = cursor_data.get("field", self.cursor_field)
                value = cursor_data.get("value")
                
                if direction == "next":
                    query[field] = {"$lt": value}  # Pour tri DESC
                else:  # direction == "prev"
                    query[field] = {"$gt": value}  # Pour tri DESC
        
        return query

class RAGPaginator:
    """Paginateur spécialisé pour les opérations RAG"""
    
    def __init__(self):
        self.default_page_size = 20
        self.max_page_size = 100
        self.search_results_page_size = 10  # Plus petit pour les résultats de recherche
    
    async def paginate_documents(self, 
                                user_id: str,
                                pagination: PaginationParams,
                                filters: Dict[str, Any] = None) -> PaginatedResponse[Dict]:
        """Pagine les documents d'un utilisateur"""
        from ..db.repositories.document_repository import DocumentRepository
        from ..utils.database_optimizer import OptimizedQueryBuilder, SortParams, SortDirection
        
        try:
            # Récupérer le repository
            doc_repo = DocumentRepository()
            
            # Construire la requête optimisée
            query_builder = OptimizedQueryBuilder(doc_repo.collection)
            query_builder.add_user_filter(user_id)
            
            # Ajouter les filtres
            if filters:
                for field, value in filters.items():
                    if field == "search":
                        query_builder.add_text_search(value, ["filename", "content"])
                    elif field == "date_from":
                        query_builder.add_date_range("created_at", start_date=value)
                    elif field == "date_to":
                        query_builder.add_date_range("created_at", end_date=value)
                    else:
                        query_builder.add_filter(field, value)
            
            # Ajouter tri et pagination
            sort_params = SortParams("created_at", SortDirection.DESC)
            query_builder.add_sort(sort_params)
            query_builder.add_pagination(pagination)
            
            # Projection pour optimiser les performances
            query_builder.add_projection([
                "_id", "filename", "file_size", "content_type", 
                "created_at", "updated_at", "status", "chunk_count"
            ])
            
            # Exécuter la requête
            result = await query_builder.execute()
            
            # Créer la réponse paginée
            pagination_info = PaginationInfo.create(
                pagination.page, 
                pagination.page_size, 
                result.total_count
            )
            
            return PaginatedResponse(
                items=result.items,
                pagination=pagination_info,
                metadata={
                    "filters_applied": filters or {},
                    "query_time": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Erreur pagination documents: {e}")
            raise
    
    async def paginate_chat_sessions(self,
                                   user_id: str,
                                   pagination: PaginationParams,
                                   filters: Dict[str, Any] = None) -> PaginatedResponse[Dict]:
        """Pagine les sessions de chat d'un utilisateur"""
        from ..db.repositories.chat_repository import ChatRepository
        from ..utils.database_optimizer import OptimizedQueryBuilder, SortParams, SortDirection
        
        try:
            # Récupérer le repository
            chat_repo = ChatRepository()
            
            # Construire la requête optimisée
            query_builder = OptimizedQueryBuilder(chat_repo.sessions_collection)
            query_builder.add_user_filter(user_id)
            
            # Ajouter les filtres
            if filters:
                for field, value in filters.items():
                    if field == "search":
                        query_builder.add_text_search(value, ["title"])
                    elif field == "active_only":
                        query_builder.add_filter("is_active", True)
                    else:
                        query_builder.add_filter(field, value)
            
            # Ajouter tri et pagination
            sort_params = SortParams("updated_at", SortDirection.DESC)
            query_builder.add_sort(sort_params)
            query_builder.add_pagination(pagination)
            
            # Projection optimisée
            query_builder.add_projection([
                "_id", "title", "created_at", "updated_at", 
                "is_active", "message_count", "last_message_preview"
            ])
            
            # Exécuter la requête
            result = await query_builder.execute()
            
            # Créer la réponse paginée
            pagination_info = PaginationInfo.create(
                pagination.page, 
                pagination.page_size, 
                result.total_count
            )
            
            return PaginatedResponse(
                items=result.items,
                pagination=pagination_info,
                metadata={
                    "filters_applied": filters or {},
                    "active_sessions": len([s for s in result.items if s.get("is_active")])
                }
            )
            
        except Exception as e:
            logger.error(f"Erreur pagination sessions: {e}")
            raise
    
    async def paginate_search_results(self,
                                    search_results: List[Dict],
                                    pagination: PaginationParams,
                                    metadata: Dict[str, Any] = None) -> PaginatedResponse[Dict]:
        """Pagine les résultats de recherche sémantique"""
        try:
            total_items = len(search_results)
            start_idx = pagination.offset
            end_idx = start_idx + pagination.limit
            
            # Extraire la page courante
            page_items = search_results[start_idx:end_idx]
            
            # Créer les informations de pagination
            pagination_info = PaginationInfo.create(
                pagination.page,
                pagination.page_size,
                total_items
            )
            
            return PaginatedResponse(
                items=page_items,
                pagination=pagination_info,
                metadata={
                    **(metadata or {}),
                    "search_performance": {
                        "total_results": total_items,
                        "page_results": len(page_items),
                        "relevance_scores": [r.get("similarity_score", 0) for r in page_items]
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"Erreur pagination résultats recherche: {e}")
            raise

# Utilitaires pour FastAPI
def create_pagination_params(page: int = 1, page_size: int = 20) -> PaginationParams:
    """Crée des paramètres de pagination pour FastAPI"""
    return PaginationParams.from_request(page=page, page_size=page_size)

def pagination_response_model(item_model: Type) -> Type:
    """Crée un modèle de réponse paginée pour FastAPI"""
    from pydantic import BaseModel
    from typing import List
    
    class PaginationInfoModel(BaseModel):
        page: int
        page_size: int
        total_items: int
        total_pages: int
        has_next: bool
        has_previous: bool
        next_page: Optional[int]
        previous_page: Optional[int]
    
    class PaginatedResponseModel(BaseModel):
        items: List[item_model]
        pagination: PaginationInfoModel
        metadata: Dict[str, Any] = {}
    
    return PaginatedResponseModel

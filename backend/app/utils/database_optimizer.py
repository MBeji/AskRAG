"""
Utilitaires d'optimisation des requêtes de base de données
Étape 16.4.2 - Optimiser les requêtes à la base
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import pymongo
from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId

logger = logging.getLogger(__name__)

class SortDirection(Enum):
    """Directions de tri"""
    ASC = 1
    DESC = -1

@dataclass
class PaginationParams:
    """Paramètres de pagination optimisée"""
    page: int = 1
    page_size: int = 20
    max_page_size: int = 100
    
    def __post_init__(self):
        # Validation des paramètres
        if self.page < 1:
            self.page = 1
        if self.page_size < 1:
            self.page_size = 20
        if self.page_size > self.max_page_size:
            self.page_size = self.max_page_size
    
    @property
    def skip(self) -> int:
        """Nombre d'éléments à ignorer"""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Limite d'éléments à retourner"""
        return self.page_size

@dataclass
class SortParams:
    """Paramètres de tri optimisé"""
    field: str
    direction: SortDirection = SortDirection.DESC
    secondary_field: Optional[str] = None
    secondary_direction: SortDirection = SortDirection.ASC
    
    def to_mongo_sort(self) -> List[Tuple[str, int]]:
        """Convertit en format de tri MongoDB"""
        sort_spec = [(self.field, self.direction.value)]
        if self.secondary_field:
            sort_spec.append((self.secondary_field, self.secondary_direction.value))
        return sort_spec

@dataclass
class QueryResult:
    """Résultat d'une requête paginée"""
    items: List[Dict[str, Any]]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
    
    @classmethod
    def create(cls, items: List[Dict], total_count: int, pagination: PaginationParams) -> 'QueryResult':
        """Crée un résultat de requête"""
        total_pages = (total_count + pagination.page_size - 1) // pagination.page_size
        
        return cls(
            items=items,
            total_count=total_count,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages,
            has_next=pagination.page < total_pages,
            has_prev=pagination.page > 1
        )

class OptimizedQueryBuilder:
    """Constructeur de requêtes optimisées MongoDB"""
    
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection
        self._pipeline = []
        self._filters = {}
        self._projection = {}
        self._sort = []
        self._pagination = None
    
    def add_filter(self, field: str, value: Any, operator: str = "$eq") -> 'OptimizedQueryBuilder':
        """Ajoute un filtre à la requête"""
        if operator == "$eq":
            self._filters[field] = value
        else:
            self._filters[field] = {operator: value}
        return self
    
    def add_text_search(self, text: str, fields: List[str] = None) -> 'OptimizedQueryBuilder':
        """Ajoute une recherche textuelle optimisée"""
        if not text.strip():
            return self
        
        if fields:
            # Recherche dans des champs spécifiques
            text_conditions = []
            for field in fields:
                text_conditions.append({
                    field: {"$regex": text, "$options": "i"}
                })
            self._filters["$or"] = text_conditions
        else:
            # Recherche full-text si index disponible
            self._filters["$text"] = {"$search": text}
        
        return self
    
    def add_date_range(self, field: str, start_date: datetime = None, 
                      end_date: datetime = None) -> 'OptimizedQueryBuilder':
        """Ajoute un filtre de plage de dates"""
        date_filter = {}
        
        if start_date:
            date_filter["$gte"] = start_date
        if end_date:
            date_filter["$lte"] = end_date
        
        if date_filter:
            self._filters[field] = date_filter
        
        return self
    
    def add_user_filter(self, user_id: str) -> 'OptimizedQueryBuilder':
        """Ajoute un filtre utilisateur (sécurité)"""
        if user_id:
            self._filters["user_id"] = user_id
        return self
    
    def add_projection(self, fields: List[str], exclude: bool = False) -> 'OptimizedQueryBuilder':
        """Ajoute une projection pour limiter les champs retournés"""
        for field in fields:
            self._projection[field] = 0 if exclude else 1
        return self
    
    def add_sort(self, sort_params: SortParams) -> 'OptimizedQueryBuilder':
        """Ajoute un tri optimisé"""
        self._sort = sort_params.to_mongo_sort()
        return self
    
    def add_pagination(self, pagination: PaginationParams) -> 'OptimizedQueryBuilder':
        """Ajoute la pagination"""
        self._pagination = pagination
        return self
    
    async def execute(self) -> QueryResult:
        """Exécute la requête optimisée"""
        try:
            # Compter le total d'abord (avec cache potentiel)
            total_count = await self._count_total()
            
            # Si pas de résultats, retourner vide
            if total_count == 0:
                return QueryResult.create([], 0, self._pagination or PaginationParams())
            
            # Construire la requête principale
            cursor = self.collection.find(self._filters)
            
            # Appliquer la projection
            if self._projection:
                cursor = cursor.project(self._projection)
            
            # Appliquer le tri
            if self._sort:
                cursor = cursor.sort(self._sort)
            
            # Appliquer la pagination
            if self._pagination:
                cursor = cursor.skip(self._pagination.skip).limit(self._pagination.limit)
            
            # Exécuter et convertir les résultats
            items = []
            async for doc in cursor:
                # Convertir ObjectId en string pour JSON
                if "_id" in doc and isinstance(doc["_id"], ObjectId):
                    doc["_id"] = str(doc["_id"])
                items.append(doc)
            
            return QueryResult.create(
                items, 
                total_count, 
                self._pagination or PaginationParams()
            )
            
        except Exception as e:
            logger.error(f"Erreur exécution requête optimisée: {e}")
            raise
    
    async def _count_total(self) -> int:
        """Compte le total avec optimisations"""
        try:
            # Utiliser countDocuments pour les petites collections
            # ou estimatedDocumentCount pour les grandes
            if len(self._filters) == 0:
                # Pas de filtres, utiliser l'estimation rapide
                return await self.collection.estimated_document_count()
            else:
                # Avec filtres, compter précisément
                return await self.collection.count_documents(self._filters)
                
        except Exception as e:
            logger.error(f"Erreur comptage documents: {e}")
            return 0

class DatabaseOptimizer:
    """Optimiseur de performances base de données"""
    
    @staticmethod
    async def ensure_indexes(collection: AsyncIOMotorCollection, 
                           indexes: List[Dict[str, Any]]) -> bool:
        """S'assure que les index nécessaires existent"""
        try:
            existing_indexes = await collection.list_indexes().to_list(length=None)
            existing_names = {idx.get("name") for idx in existing_indexes}
            
            for index_spec in indexes:
                index_name = index_spec.get("name")
                if index_name not in existing_names:
                    keys = index_spec["keys"]
                    options = index_spec.get("options", {})
                    
                    await collection.create_index(keys, name=index_name, **options)
                    logger.info(f"Index créé: {index_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur création indexes: {e}")
            return False
    
    @staticmethod
    async def analyze_query_performance(collection: AsyncIOMotorCollection,
                                      query: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse les performances d'une requête"""
        try:
            # Utiliser explain() pour analyser
            cursor = collection.find(query)
            explain_result = await cursor.explain()
            
            execution_stats = explain_result.get("executionStats", {})
            
            return {
                "total_docs_examined": execution_stats.get("totalDocsExamined", 0),
                "total_keys_examined": execution_stats.get("totalKeysExamined", 0),
                "execution_time_ms": execution_stats.get("executionTimeMillis", 0),
                "docs_returned": execution_stats.get("nReturned", 0),
                "index_used": execution_stats.get("indexUsed", False),
                "winning_plan": explain_result.get("queryPlanner", {}).get("winningPlan", {})
            }
            
        except Exception as e:
            logger.error(f"Erreur analyse performance: {e}")
            return {}
    
    @staticmethod
    def get_optimal_indexes() -> Dict[str, List[Dict]]:
        """Retourne les index optimaux pour chaque collection"""
        return {
            "documents": [
                {
                    "name": "user_id_1_created_at_-1",
                    "keys": [("user_id", 1), ("created_at", -1)],
                    "options": {"background": True}
                },
                {
                    "name": "user_id_1_filename_1",
                    "keys": [("user_id", 1), ("filename", 1)],
                    "options": {"background": True, "unique": True}
                },
                {
                    "name": "filename_text_content_text",
                    "keys": [("filename", "text"), ("content", "text")],
                    "options": {"background": True}
                }
            ],
            "chat_sessions": [
                {
                    "name": "user_id_1_created_at_-1",
                    "keys": [("user_id", 1), ("created_at", -1)],
                    "options": {"background": True}
                },
                {
                    "name": "user_id_1_updated_at_-1",
                    "keys": [("user_id", 1), ("updated_at", -1)],
                    "options": {"background": True}
                }
            ],
            "chat_messages": [
                {
                    "name": "session_id_1_created_at_1",
                    "keys": [("session_id", 1), ("created_at", 1)],
                    "options": {"background": True}
                },
                {
                    "name": "user_id_1_created_at_-1",
                    "keys": [("user_id", 1), ("created_at", -1)],
                    "options": {"background": True}
                }
            ],
            "users": [
                {
                    "name": "email_1",
                    "keys": [("email", 1)],
                    "options": {"background": True, "unique": True}
                },
                {
                    "name": "username_1",
                    "keys": [("username", 1)],
                    "options": {"background": True, "unique": True}
                }
            ]
        }

# Décorateur pour monitoring des requêtes
def monitor_query_performance(operation_name: str):
    """Décorateur pour monitorer les performances des requêtes"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = datetime.now()
            
            try:
                result = await func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                
                logger.info(f"Requête '{operation_name}' exécutée en {duration:.3f}s")
                
                # Optionnel: envoyer les métriques au système de monitoring
                from ..utils.metrics import RAGMetrics
                metrics = RAGMetrics()
                await metrics.record_database_query(operation_name, duration)
                
                return result
                
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                logger.error(f"Erreur requête '{operation_name}' après {duration:.3f}s: {e}")
                raise
        
        return wrapper
    return decorator

"""
Module de cache pour les requêtes RAG
Étape 16.3.3 - Implémentation du cache des requêtes
"""

import hashlib
import json
import pickle
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class CacheKey:
    """Génération de clés de cache standardisées"""
    
    @staticmethod
    def for_query(query: str, filters: Optional[Dict] = None) -> str:
        """Génère une clé pour une requête de recherche"""
        data = {
            "type": "query",
            "query": query.lower().strip(),
            "filters": filters or {}
        }
        return CacheKey._hash_data(data)
    
    @staticmethod
    def for_document_chunks(document_id: str) -> str:
        """Génère une clé pour les chunks d'un document"""
        return f"doc_chunks:{document_id}"
    
    @staticmethod
    def for_embeddings(content_hash: str) -> str:
        """Génère une clé pour les embeddings d'un contenu"""
        return f"embeddings:{content_hash}"
    
    @staticmethod
    def for_rag_response(query: str, context_hash: str) -> str:
        """Génère une clé pour une réponse RAG complète"""
        data = {
            "type": "rag_response",
            "query": query.lower().strip(),
            "context": context_hash
        }
        return CacheKey._hash_data(data)
    
    @staticmethod
    def for_session_history(session_id: str) -> str:
        """Génère une clé pour l'historique d'une session"""
        return f"session_history:{session_id}"
    
    @staticmethod
    def _hash_data(data: Dict) -> str:
        """Hash sécurisé des données"""
        json_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(json_str.encode()).hexdigest()[:16]


class CacheBackend(ABC):
    """Interface abstraite pour les backends de cache"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Récupère une valeur du cache"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Stocke une valeur dans le cache"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Supprime une valeur du cache"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Vérifie l'existence d'une clé"""
        pass
    
    @abstractmethod
    async def clear(self, pattern: Optional[str] = None) -> int:
        """Vide le cache ou les clés matchant un pattern"""
        pass


class MemoryCache(CacheBackend):
    """Cache en mémoire pour le développement"""
    
    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, Dict] = {}
        self.max_size = max_size
    
    async def get(self, key: str) -> Optional[Any]:
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        
        # Vérifier l'expiration
        if entry.get("expires_at") and datetime.now() > entry["expires_at"]:
            del self.cache[key]
            return None
        
        return entry["value"]
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        try:
            # Gérer la taille max du cache
            if len(self.cache) >= self.max_size and key not in self.cache:
                # Supprimer la plus ancienne entrée
                oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]["created_at"])
                del self.cache[oldest_key]
            
            expires_at = None
            if ttl:
                expires_at = datetime.now() + timedelta(seconds=ttl)
            
            self.cache[key] = {
                "value": value,
                "created_at": datetime.now(),
                "expires_at": expires_at
            }
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la mise en cache: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    async def exists(self, key: str) -> bool:
        return await self.get(key) is not None
    
    async def clear(self, pattern: Optional[str] = None) -> int:
        if pattern is None:
            count = len(self.cache)
            self.cache.clear()
            return count
        
        # Pattern matching simple
        keys_to_delete = [k for k in self.cache.keys() if pattern in k]
        for key in keys_to_delete:
            del self.cache[key]
        return len(keys_to_delete)


class RedisCache(CacheBackend):
    """Cache Redis pour la production avec gestion avancée"""
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self._connection_verified = False
    
    async def _ensure_connection(self):
        """S'assure que la connexion Redis est disponible"""
        if not self.redis:
            from ..core.redis_config import get_redis_client
            self.redis = await get_redis_client()
        
        # Vérifier la connexion si pas encore fait
        if not self._connection_verified and self.redis:
            try:
                await self.redis.ping()
                self._connection_verified = True
            except Exception as e:
                logger.error(f"Connexion Redis échouée: {e}")
                self.redis = None
    
    async def get(self, key: str) -> Optional[Any]:
        try:
            await self._ensure_connection()
            if not self.redis:
                return None
            
            data = await self.redis.get(key)
            if data is None:
                return None
            
            # Support JSON et pickle pour flexibilité
            try:
                return json.loads(data.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return pickle.loads(data)
                
        except Exception as e:
            logger.error(f"Erreur Redis get {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        try:
            await self._ensure_connection()
            if not self.redis:
                return False
            
            # Tenter JSON d'abord, puis pickle
            try:
                data = json.dumps(value, ensure_ascii=False).encode('utf-8')
            except (TypeError, ValueError):
                data = pickle.dumps(value)
            
            if ttl:
                await self.redis.setex(key, ttl, data)
            else:
                await self.redis.set(key, data)
            return True
            
        except Exception as e:
            logger.error(f"Erreur Redis set {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        try:
            await self._ensure_connection()
            if not self.redis:
                return False
                
            result = await self.redis.delete(key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Erreur Redis delete {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        try:
            await self._ensure_connection()
            if not self.redis:
                return False
                
            return await self.redis.exists(key) > 0
            
        except Exception as e:
            logger.error(f"Erreur Redis exists {key}: {e}")
            return False
    
    async def clear(self, pattern: Optional[str] = None) -> int:
        try:
            await self._ensure_connection()
            if not self.redis:
                return 0
            
            if pattern is None:
                return await self.redis.flushdb()
            
            # Utiliser SCAN pour les gros datasets
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                return await self.redis.delete(*keys)
            return 0
            
        except Exception as e:
            logger.error(f"Erreur Redis clear {pattern}: {e}")
            return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """Récupère les statistiques du cache Redis"""
        try:
            await self._ensure_connection()
            if not self.redis:
                return {"status": "disconnected"}
            
            info = await self.redis.info()
            return {
                "backend_type": "RedisCache",
                "status": "connected",
                "used_memory": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_ratio": self._calculate_hit_ratio(info),
                "redis_version": info.get("redis_version", "N/A")
            }
            
        except Exception as e:
            logger.error(f"Erreur stats Redis: {e}")
            return {"status": "error", "error": str(e)}
    
    def _calculate_hit_ratio(self, info: dict) -> str:
        """Calcule le ratio de hit du cache"""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        
        if total == 0:
            return "0.0%"
        
        ratio = (hits / total) * 100
        return f"{ratio:.1f}%"


class QueryCache:
    """Cache spécialisé pour les requêtes RAG"""
    
    def __init__(self, backend: CacheBackend):
        self.backend = backend
        self.default_ttl = 3600  # 1 heure par défaut
        self.ttl_config = {
            "search_results": 1800,      # 30 minutes
            "rag_responses": 3600,       # 1 heure
            "embeddings": 86400,         # 24 heures
            "document_chunks": 86400,    # 24 heures
            "session_history": 3600      # 1 heure
        }
    
    async def get_search_results(self, query: str, filters: Optional[Dict] = None) -> Optional[List[Dict]]:
        """Récupère les résultats de recherche en cache"""
        key = CacheKey.for_query(query, filters)
        return await self.backend.get(key)
    
    async def cache_search_results(self, query: str, results: List[Dict], filters: Optional[Dict] = None) -> bool:
        """Met en cache les résultats de recherche"""
        key = CacheKey.for_query(query, filters)
        ttl = self.ttl_config["search_results"]
        return await self.backend.set(key, results, ttl)
    
    async def get_rag_response(self, query: str, context_hash: str) -> Optional[Dict]:
        """Récupère une réponse RAG en cache"""
        key = CacheKey.for_rag_response(query, context_hash)
        return await self.backend.get(key)
    
    async def cache_rag_response(self, query: str, context_hash: str, response: Dict) -> bool:
        """Met en cache une réponse RAG"""
        key = CacheKey.for_rag_response(query, context_hash)
        ttl = self.ttl_config["rag_responses"]
        
        # Ajouter des métadonnées de cache
        cached_response = {
            **response,
            "cached_at": datetime.now().isoformat(),
            "cache_key": key
        }
        
        return await self.backend.set(key, cached_response, ttl)
    
    async def get_embeddings(self, content_hash: str) -> Optional[List[float]]:
        """Récupère des embeddings en cache"""
        key = CacheKey.for_embeddings(content_hash)
        return await self.backend.get(key)
    
    async def cache_embeddings(self, content_hash: str, embeddings: List[float]) -> bool:
        """Met en cache des embeddings"""
        key = CacheKey.for_embeddings(content_hash)
        ttl = self.ttl_config["embeddings"]
        return await self.backend.set(key, embeddings, ttl)
    
    async def get_document_chunks(self, document_id: str) -> Optional[List[Dict]]:
        """Récupère les chunks d'un document en cache"""
        key = CacheKey.for_document_chunks(document_id)
        return await self.backend.get(key)
    
    async def cache_document_chunks(self, document_id: str, chunks: List[Dict]) -> bool:
        """Met en cache les chunks d'un document"""
        key = CacheKey.for_document_chunks(document_id)
        ttl = self.ttl_config["document_chunks"]
        return await self.backend.set(key, chunks, ttl)
    
    async def get_session_history(self, session_id: str) -> Optional[List[Dict]]:
        """Récupère l'historique d'une session en cache"""
        key = CacheKey.for_session_history(session_id)
        return await self.backend.get(key)
    
    async def cache_session_history(self, session_id: str, history: List[Dict]) -> bool:
        """Met en cache l'historique d'une session"""
        key = CacheKey.for_session_history(session_id)
        ttl = self.ttl_config["session_history"]
        return await self.backend.set(key, history, ttl)
    
    async def invalidate_session_cache(self, session_id: str) -> bool:
        """Invalide le cache d'une session"""
        key = CacheKey.for_session_history(session_id)
        return await self.backend.delete(key)
    
    async def invalidate_document_cache(self, document_id: str) -> bool:
        """Invalide le cache d'un document"""
        chunks_key = CacheKey.for_document_chunks(document_id)
        return await self.backend.delete(chunks_key)
    
    async def clear_all_cache(self) -> int:
        """Vide tout le cache"""
        return await self.backend.clear()
    
    async def clear_expired_cache(self) -> int:
        """Nettoie le cache expiré (pour MemoryCache)"""
        if isinstance(self.backend, MemoryCache):
            expired_keys = []
            for key, entry in self.backend.cache.items():
                if entry.get("expires_at") and datetime.now() > entry["expires_at"]:
                    expired_keys.append(key)
            
            for key in expired_keys:
                await self.backend.delete(key)
            
            return len(expired_keys)
        return 0
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Récupère les statistiques du cache"""
        stats = {
            "backend_type": type(self.backend).__name__,
            "default_ttl": self.default_ttl,
            "ttl_config": self.ttl_config
        }
        
        if isinstance(self.backend, MemoryCache):
            stats.update({
                "total_keys": len(self.backend.cache),
                "max_size": self.backend.max_size
            })
        
        return stats


class CacheManager:
    """Gestionnaire principal du cache avec auto-détection Redis"""
    
    def __init__(self, backend: Optional[CacheBackend] = None):
        self.backend = backend or MemoryCache()
        self.query_cache = QueryCache(self.backend)
        self._fallback_backend = MemoryCache()
    
    @classmethod
    def create_memory_cache(cls, max_size: int = 1000) -> 'CacheManager':
        """Crée un cache en mémoire"""
        return cls(MemoryCache(max_size))
    
    @classmethod
    def create_redis_cache(cls, redis_client=None) -> 'CacheManager':
        """Crée un cache Redis avec fallback automatique"""
        return cls(RedisCache(redis_client))
    
    @classmethod
    async def create_optimal_cache(cls) -> 'CacheManager':
        """Crée le cache optimal disponible (Redis si possible, sinon Memory)"""
        try:
            # Tenter Redis d'abord
            from ..core.redis_config import get_redis_client
            redis_client = await get_redis_client()
            
            if redis_client:
                redis_cache = RedisCache(redis_client)
                # Test rapide de connexion
                test_result = await redis_cache.set("test_connection", "ok", 5)
                if test_result:
                    await redis_cache.delete("test_connection")
                    logger.info("Cache Redis sélectionné automatiquement")
                    return cls(redis_cache)
            
            # Fallback vers Memory cache
            logger.info("Cache mémoire sélectionné (Redis non disponible)")
            return cls(MemoryCache())
            
        except Exception as e:
            logger.warning(f"Erreur auto-détection cache, utilisation Memory: {e}")
            return cls(MemoryCache())
    
    def get_query_cache(self) -> QueryCache:
        """Récupère l'interface de cache pour les requêtes"""
        return self.query_cache
    
    async def switch_to_fallback(self):
        """Bascule vers le cache de secours en cas d'erreur"""
        if not isinstance(self.backend, MemoryCache):
            logger.warning("Basculement vers cache mémoire de secours")
            self.backend = self._fallback_backend
            self.query_cache = QueryCache(self.backend)
    
    async def get_backend_stats(self) -> Dict[str, Any]:
        """Récupère les statistiques détaillées du backend"""
        if hasattr(self.backend, 'get_stats'):
            return await self.backend.get_stats()
        else:
            return await self.query_cache.get_cache_stats()
    
    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé du cache avec diagnostics avancés"""
        try:
            start_time = datetime.now()
            test_key = "health_check_test"
            test_value = {"timestamp": start_time.isoformat(), "test": "cache_health"}
            
            # Test écriture
            write_start = datetime.now()
            write_success = await self.backend.set(test_key, test_value, 60)
            write_time = (datetime.now() - write_start).total_seconds()
            
            if not write_success:
                await self.switch_to_fallback()
                return {
                    "status": "fallback", 
                    "error": "Échec écriture cache principal",
                    "backend": type(self.backend).__name__,
                    "fallback_active": True
                }
            
            # Test lecture
            read_start = datetime.now()
            read_value = await self.backend.get(test_key)
            read_time = (datetime.now() - read_start).total_seconds()
            
            if read_value != test_value:
                await self.switch_to_fallback()
                return {
                    "status": "fallback", 
                    "error": "Échec lecture cache principal",
                    "backend": type(self.backend).__name__,
                    "fallback_active": True
                }
            
            # Test suppression
            delete_start = datetime.now()
            delete_success = await self.backend.delete(test_key)
            delete_time = (datetime.now() - delete_start).total_seconds()
            
            total_time = (datetime.now() - start_time).total_seconds()
            
            # Récupérer les stats du backend
            backend_stats = await self.get_backend_stats()
            
            return {
                "status": "healthy",
                "backend": type(self.backend).__name__,
                "performance": {
                    "write_time_ms": round(write_time * 1000, 2),
                    "read_time_ms": round(read_time * 1000, 2),
                    "delete_time_ms": round(delete_time * 1000, 2),
                    "total_time_ms": round(total_time * 1000, 2)
                },
                "operations": {
                    "write_success": write_success,
                    "read_success": read_value == test_value,
                    "delete_success": delete_success
                },
                "backend_stats": backend_stats,
                "fallback_available": True
            }
            
        except Exception as e:
            logger.error(f"Erreur health check cache: {e}")
            await self.switch_to_fallback()
            return {
                "status": "error", 
                "error": str(e),
                "backend": type(self.backend).__name__,
                "fallback_active": True
            }
    
    async def initialize(self):
        """Initialise le gestionnaire de cache"""
        # Pour les tests de performance, effectuer un health check
        try:
            health = await self.health_check()
            if health["status"] == "healthy":
                logger.info(f"CacheManager initialisé avec backend {health['backend']}")
            else:
                logger.warning(f"CacheManager initialisé avec problèmes: {health}")
        except Exception as e:
            logger.warning(f"Erreur lors de l'initialisation du cache: {e}")
            await self.switch_to_fallback()
    
    async def cleanup(self):
        """Nettoie les ressources du gestionnaire de cache"""
        try:
            # Nettoyer le cache expiré si c'est un MemoryCache
            if isinstance(self.backend, MemoryCache):
                expired_count = await self.query_cache.clear_expired_cache()
                logger.info(f"Nettoyage cache: {expired_count} entrées expirées supprimées")
            
            # Pour Redis, on ne fait pas de cleanup automatique
            logger.info(f"Cleanup CacheManager terminé (backend: {type(self.backend).__name__})")
            
        except Exception as e:
            logger.warning(f"Erreur lors du cleanup du cache: {e}")

# Instance globale du gestionnaire de cache
_global_cache_manager: Optional[CacheManager] = None

async def get_cache_manager() -> CacheManager:
    """Récupère l'instance globale du gestionnaire de cache"""
    global _global_cache_manager
    
    if _global_cache_manager is None:
        _global_cache_manager = await CacheManager.create_optimal_cache()
    
    return _global_cache_manager

async def get_query_cache() -> QueryCache:
    """Récupère l'interface de cache pour les requêtes"""
    manager = await get_cache_manager()
    return manager.get_query_cache()

async def reset_cache_manager():
    """Réinitialise le gestionnaire de cache global"""
    global _global_cache_manager
    _global_cache_manager = None

# Context manager pour les opérations de cache
class CacheOperation:
    """Context manager pour les opérations de cache avec gestion d'erreurs"""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.cache_manager = None
    
    async def __aenter__(self):
        try:
            self.cache_manager = await get_cache_manager()
            return self.cache_manager.get_query_cache()
        except Exception as e:
            logger.error(f"Erreur démarrage opération cache '{self.operation_name}': {e}")
            # Retourner un cache minimal en cas d'erreur
            return QueryCache(MemoryCache(max_size=100))
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logger.error(f"Erreur pendant opération cache '{self.operation_name}': {exc_val}")
        return False

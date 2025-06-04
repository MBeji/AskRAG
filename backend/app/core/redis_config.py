"""
Configuration et connexion Redis pour le cache
Étape 16.4.1 - Implémentation du cache Redis
"""

import asyncio
import logging
from typing import Optional
import aioredis
from functools import lru_cache
import os

logger = logging.getLogger(__name__)

class RedisConfig:
    """Configuration Redis"""
    
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_db = int(os.getenv("REDIS_DB", "0"))
        self.redis_password = os.getenv("REDIS_PASSWORD", None)
        self.redis_ttl = int(os.getenv("REDIS_TTL", "3600"))
        self.redis_max_connections = int(os.getenv("REDIS_MAX_CONNECTIONS", "10"))
        self.redis_retry_on_timeout = os.getenv("REDIS_RETRY_ON_TIMEOUT", "true").lower() == "true"
        self.redis_health_check_interval = int(os.getenv("REDIS_HEALTH_CHECK_INTERVAL", "30"))

class RedisConnectionManager:
    """Gestionnaire de connexions Redis avec pool et santé"""
    
    def __init__(self, config: Optional[RedisConfig] = None):
        self.config = config or RedisConfig()
        self._pool: Optional[aioredis.ConnectionPool] = None
        self._redis: Optional[aioredis.Redis] = None
        self._is_connected = False
        self._is_healthy = False
    
    async def connect(self) -> bool:
        """Établit la connexion Redis"""
        try:
            # Configuration du pool de connexions
            self._pool = aioredis.ConnectionPool.from_url(
                self.config.redis_url,
                max_connections=self.config.redis_max_connections,
                retry_on_timeout=self.config.redis_retry_on_timeout,
                health_check_interval=self.config.redis_health_check_interval,
                password=self.config.redis_password,
                db=self.config.redis_db
            )
            
            # Créer l'instance Redis
            self._redis = aioredis.Redis(connection_pool=self._pool)
            
            # Test de connexion
            await self._redis.ping()
            
            self._is_connected = True
            self._is_healthy = True
            
            logger.info(f"Connexion Redis établie: {self.config.redis_url}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur connexion Redis: {e}")
            self._is_connected = False
            self._is_healthy = False
            return False
    
    async def disconnect(self):
        """Ferme la connexion Redis"""
        try:
            if self._redis:
                await self._redis.close()
            if self._pool:
                await self._pool.disconnect()
            
            self._is_connected = False
            self._is_healthy = False
            
            logger.info("Connexion Redis fermée")
            
        except Exception as e:
            logger.error(f"Erreur fermeture Redis: {e}")
    
    async def health_check(self) -> bool:
        """Vérifie la santé de la connexion Redis"""
        try:
            if not self._redis:
                return False
            
            # Test ping
            await self._redis.ping()
            
            # Test écriture/lecture
            test_key = "health_check_test"
            await self._redis.set(test_key, "ok", ex=5)
            result = await self._redis.get(test_key)
            await self._redis.delete(test_key)
            
            self._is_healthy = (result == b"ok")
            return self._is_healthy
            
        except Exception as e:
            logger.error(f"Health check Redis failed: {e}")
            self._is_healthy = False
            return False
    
    async def get_stats(self) -> dict:
        """Récupère les statistiques Redis"""
        try:
            if not self._redis:
                return {"status": "disconnected"}
            
            info = await self._redis.info()
            
            return {
                "status": "connected" if self._is_healthy else "unhealthy",
                "used_memory": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "redis_version": info.get("redis_version", "N/A"),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0)
            }
            
        except Exception as e:
            logger.error(f"Erreur stats Redis: {e}")
            return {"status": "error", "error": str(e)}
    
    @property
    def redis(self) -> Optional[aioredis.Redis]:
        """Retourne l'instance Redis"""
        return self._redis if self._is_connected else None
    
    @property
    def is_connected(self) -> bool:
        """Indique si Redis est connecté"""
        return self._is_connected
    
    @property
    def is_healthy(self) -> bool:
        """Indique si Redis est en bonne santé"""
        return self._is_healthy

# Instance globale du gestionnaire Redis
_redis_manager: Optional[RedisConnectionManager] = None

@lru_cache()
def get_redis_config() -> RedisConfig:
    """Retourne la configuration Redis (cached)"""
    return RedisConfig()

async def get_redis_manager() -> RedisConnectionManager:
    """Retourne le gestionnaire Redis global"""
    global _redis_manager
    
    if _redis_manager is None:
        _redis_manager = RedisConnectionManager(get_redis_config())
        await _redis_manager.connect()
    
    return _redis_manager

async def get_redis_client() -> Optional[aioredis.Redis]:
    """Retourne le client Redis connecté"""
    manager = await get_redis_manager()
    return manager.redis

async def close_redis_connection():
    """Ferme la connexion Redis globale"""
    global _redis_manager
    
    if _redis_manager:
        await _redis_manager.disconnect()
        _redis_manager = None

# Context manager pour les opérations Redis
class RedisOperation:
    """Context manager pour les opérations Redis avec gestion d'erreurs"""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.redis_client = None
    
    async def __aenter__(self):
        try:
            self.redis_client = await get_redis_client()
            if not self.redis_client:
                raise ConnectionError("Redis client not available")
            return self.redis_client
        except Exception as e:
            logger.error(f"Erreur démarrage opération Redis '{self.operation_name}': {e}")
            raise
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logger.error(f"Erreur pendant opération Redis '{self.operation_name}': {exc_val}")
        return False

# Décorateur pour les opérations Redis avec retry
def redis_operation(retries: int = 3, delay: float = 1.0):
    """Décorateur pour retry automatique des opérations Redis"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < retries - 1:
                        logger.warning(f"Retry {attempt + 1}/{retries} pour {func.__name__}: {e}")
                        await asyncio.sleep(delay * (attempt + 1))
                    else:
                        logger.error(f"Échec définitif {func.__name__} après {retries} tentatives: {e}")
            
            raise last_exception
        
        return wrapper
    return decorator

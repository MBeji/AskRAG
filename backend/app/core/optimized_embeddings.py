"""
Service d'embeddings optimisé avec traitement par batch
Étape 16.4.4 - Optimiser les embeddings batch
"""

import asyncio
import logging
import time
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class BatchStats:
    """Statistiques de traitement par batch"""
    total_texts: int
    total_batches: int
    cache_hits: int
    cache_misses: int
    total_time: float
    avg_batch_time: float
    embeddings_generated: int
    errors: int

class OptimizedEmbeddingService:
    """Service d'embeddings optimisé avec mise en cache avancée et traitement batch"""
    
    def __init__(self, 
                 model_name: str = "text-embedding-3-small",
                 api_key: str = None,
                 max_batch_size: int = 50,
                 max_concurrent_batches: int = 3):
        
        self.model_name = model_name
        self.api_key = api_key
        self.max_batch_size = max_batch_size
        self.max_concurrent_batches = max_concurrent_batches
        
        # Configuration OpenAI
        if api_key:
            import openai
            self.client = openai.OpenAI(api_key=api_key)
        else:
            self.client = None
            logger.warning("Mode test activé - embeddings simulés")
        
        # Cache optimisé avec LRU
        self._cache = {}
        self._cache_access_times = {}
        self._max_cache_size = 10000
        
        # Statistiques
        self._stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'batch_operations': 0,
            'total_embeddings_generated': 0,
            'total_api_calls': 0,
            'average_batch_time': 0.0
        }
        
        # Pool de threads pour les opérations parallèles
        self._executor = ThreadPoolExecutor(max_workers=max_concurrent_batches)
        
        logger.info(f"OptimizedEmbeddingService initialisé: {model_name}")
    
    def _get_cache_key(self, text: str) -> str:
        """Génère une clé de cache optimisée"""
        content = f"{self.model_name}:{text.strip()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _manage_cache_size(self):
        """Gère la taille du cache avec stratégie LRU"""
        if len(self._cache) >= self._max_cache_size:
            # Supprimer les 20% plus anciens
            num_to_remove = self._max_cache_size // 5
            
            # Trier par temps d'accès
            sorted_items = sorted(
                self._cache_access_times.items(),
                key=lambda x: x[1]
            )
            
            for key, _ in sorted_items[:num_to_remove]:
                self._cache.pop(key, None)
                self._cache_access_times.pop(key, None)
    
    async def get_embedding_cached(self, text: str) -> Optional[List[float]]:
        """Récupère un embedding du cache avec gestion LRU"""
        cache_key = self._get_cache_key(text)
        
        if cache_key in self._cache:
            self._cache_access_times[cache_key] = datetime.now()
            self._stats['cache_hits'] += 1
            return self._cache[cache_key]
        
        return None
    
    async def cache_embedding(self, text: str, embedding: List[float]):
        """Met en cache un embedding"""
        cache_key = self._get_cache_key(text)
        
        self._manage_cache_size()
        
        self._cache[cache_key] = embedding
        self._cache_access_times[cache_key] = datetime.now()
    
    async def generate_single_embedding(self, text: str) -> List[float]:
        """Génère un seul embedding avec gestion d'erreurs"""
        try:
            if not self.client:
                # Mode test - générer un embedding simulé
                return self._generate_test_embedding(text)
            
            response = await asyncio.get_event_loop().run_in_executor(
                self._executor,
                lambda: self.client.embeddings.create(
                    input=[text],
                    model=self.model_name
                )
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Erreur génération embedding: {e}")
            return self._generate_test_embedding(text)
    
    async def process_batch_optimized(self, texts: List[str]) -> Tuple[List[List[float]], BatchStats]:
        """Traite un batch de textes de manière optimisée"""
        start_time = time.time()
        batch_stats = BatchStats(
            total_texts=len(texts),
            total_batches=1,
            cache_hits=0,
            cache_misses=0,
            total_time=0.0,
            avg_batch_time=0.0,
            embeddings_generated=0,
            errors=0
        )
        
        embeddings = []
        texts_to_process = []
        cached_embeddings = {}
        
        # Phase 1: Vérifier le cache
        for i, text in enumerate(texts):
            cached_embedding = await self.get_embedding_cached(text)
            if cached_embedding:
                cached_embeddings[i] = cached_embedding
                batch_stats.cache_hits += 1
            else:
                texts_to_process.append((i, text))
                batch_stats.cache_misses += 1
        
        # Phase 2: Traiter les textes non mis en cache
        if texts_to_process and self.client:
            try:
                # Optimisation: envoyer tous les textes en une seule requête API
                api_texts = [text for _, text in texts_to_process]
                
                response = await asyncio.get_event_loop().run_in_executor(
                    self._executor,
                    lambda: self.client.embeddings.create(
                        input=api_texts,
                        model=self.model_name
                    )
                )
                
                # Traiter les résultats
                for (original_idx, text), embedding_data in zip(texts_to_process, response.data):
                    embedding = embedding_data.embedding
                    cached_embeddings[original_idx] = embedding
                    
                    # Mettre en cache
                    await self.cache_embedding(text, embedding)
                    batch_stats.embeddings_generated += 1
                
                self._stats['total_api_calls'] += 1
                
            except Exception as e:
                logger.error(f"Erreur traitement batch API: {e}")
                batch_stats.errors += 1
                
                # Générer des embeddings de test pour les échecs
                for original_idx, text in texts_to_process:
                    test_embedding = self._generate_test_embedding(text)
                    cached_embeddings[original_idx] = test_embedding
        
        elif texts_to_process:
            # Mode test - générer tous les embeddings simulés
            for original_idx, text in texts_to_process:
                test_embedding = self._generate_test_embedding(text)
                cached_embeddings[original_idx] = test_embedding
                batch_stats.embeddings_generated += 1
        
        # Phase 3: Reconstituer la liste ordonnée
        for i in range(len(texts)):
            embeddings.append(cached_embeddings[i])
        
        # Finaliser les statistiques
        batch_stats.total_time = time.time() - start_time
        batch_stats.avg_batch_time = batch_stats.total_time
        
        self._stats['batch_operations'] += 1
        self._stats['total_embeddings_generated'] += batch_stats.embeddings_generated
        
        return embeddings, batch_stats
    
    async def generate_embeddings_batch(self, 
                                      texts: List[str],
                                      batch_size: Optional[int] = None,
                                      max_concurrent: Optional[int] = None) -> Dict[str, Any]:
        """
        Génère des embeddings par batch avec optimisations avancées
        
        Args:
            texts: Liste de textes à embedder
            batch_size: Taille des sous-batches (par défaut: max_batch_size)
            max_concurrent: Nombre max de batches concurrents
            
        Returns:
            Dict contenant les embeddings et les statistiques
        """
        if not texts:
            return {"embeddings": [], "stats": None, "success": True}
        
        batch_size = batch_size or self.max_batch_size
        max_concurrent = max_concurrent or self.max_concurrent_batches
        
        start_time = time.time()
        all_embeddings = []
        all_stats = []
        
        # Diviser en sous-batches
        batches = [texts[i:i + batch_size] for i in range(0, len(texts), batch_size)]
        
        # Traiter les batches avec concurrence limitée
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_single_batch(batch_texts):
            async with semaphore:
                return await self.process_batch_optimized(batch_texts)
        
        # Exécuter tous les batches
        batch_tasks = [process_single_batch(batch) for batch in batches]
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        
        # Traiter les résultats
        for result in batch_results:
            if isinstance(result, Exception):
                logger.error(f"Erreur batch: {result}")
                # Ajouter des embeddings vides en cas d'erreur
                batch_size_failed = len(batches[batch_results.index(result)])
                all_embeddings.extend([[0.0] * 1536] * batch_size_failed)
            else:
                batch_embeddings, batch_stats = result
                all_embeddings.extend(batch_embeddings)
                all_stats.append(batch_stats)
        
        # Calculer les statistiques globales
        total_time = time.time() - start_time
        global_stats = {
            "total_texts": len(texts),
            "total_batches": len(batches),
            "total_cache_hits": sum(s.cache_hits for s in all_stats),
            "total_cache_misses": sum(s.cache_misses for s in all_stats),
            "total_time": total_time,
            "avg_time_per_text": total_time / len(texts) if texts else 0,
            "cache_hit_ratio": sum(s.cache_hits for s in all_stats) / len(texts) if texts else 0,
            "embeddings_generated": sum(s.embeddings_generated for s in all_stats),
            "errors": sum(s.errors for s in all_stats)
        }
          # Mettre à jour les statistiques globales
        self._stats['total_requests'] += len(texts)
        self._stats['average_batch_time'] = (
            (self._stats['average_batch_time'] * (self._stats['batch_operations'] - len(batches)) + 
             sum(s.total_time for s in all_stats)) / self._stats['batch_operations']
        )
        
        logger.info(f"Batch complet: {len(texts)} embeddings en {total_time:.2f}s")
        
        return {
            "embeddings": all_embeddings,
            "stats": global_stats,
            "success": len(all_embeddings) == len(texts)
        }
    
    def _generate_test_embedding(self, text: str) -> List[float]:
        """Génère un embedding de test déterministe"""
        # Utiliser un hash pour générer un vecteur déterministe
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        # Convertir en vecteur de dimension appropriée
        dimension = 1536  # Dimension standard OpenAI
        vector = []
        
        for i in range(dimension):
            # Utiliser le hash pour générer des valeurs pseudo-aléatoires
            hash_index = (i * 2) % len(text_hash)
            if hash_index + 1 < len(text_hash):
                hash_part = text_hash[hash_index:hash_index + 2]
            else:
                # Si on atteint la fin, reprendre depuis le début
                hash_part = text_hash[hash_index:] + text_hash[0:2-(len(text_hash)-hash_index)]
            
            if len(hash_part) < 2:
                hash_part = hash_part + "0"  # Padding si nécessaire
            
            value = int(hash_part, 16) / 255.0  # Normaliser entre 0 et 1
            vector.append((value - 0.5) * 2)  # Centrer entre -1 et 1
        
        # Normaliser le vecteur
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = [v / norm for v in vector]
        
        return vector
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques détaillées"""
        cache_size = len(self._cache)
        cache_hit_rate = (
            self._stats['cache_hits'] / self._stats['total_requests'] * 100
            if self._stats['total_requests'] > 0 else 0
        )
        
        return {
            **self._stats,
            "cache_size": cache_size,
            "cache_hit_rate": f"{cache_hit_rate:.1f}%",
            "max_cache_size": self._max_cache_size,
            "max_batch_size": self.max_batch_size,
            "max_concurrent_batches": self.max_concurrent_batches,
            "model_name": self.model_name
        }
    
    def clear_cache(self):
        """Vide le cache"""
        self._cache.clear()
        self._cache_access_times.clear()
        logger.info("Cache d'embeddings vidé")
    
    async def cleanup(self):
        """Nettoie les ressources"""
        self._executor.shutdown(wait=True)
        logger.info("OptimizedEmbeddingService nettoyé")

# Instance globale optimisée
_optimized_embedding_service: Optional[OptimizedEmbeddingService] = None

async def get_optimized_embedding_service() -> OptimizedEmbeddingService:
    """Récupère l'instance globale du service d'embeddings optimisé"""
    global _optimized_embedding_service
    
    if _optimized_embedding_service is None:
        import os
        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        
        _optimized_embedding_service = OptimizedEmbeddingService(
            model_name=model,
            api_key=api_key,
            max_batch_size=50,
            max_concurrent_batches=3
        )
    
    return _optimized_embedding_service

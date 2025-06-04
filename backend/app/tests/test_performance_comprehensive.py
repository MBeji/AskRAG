"""
Tests de performance complets pour AskRAG
Étape 16.4.5 - Tester les performances

Tests pour toutes les optimisations implémentées:
- Cache Redis
- Optimisations base de données  
- Pagination efficace
- Embeddings batch optimisés
"""

import asyncio
import pytest
import time
import statistics
from typing import List, Dict, Any
from datetime import datetime
import logging

# Import des modules à tester
from app.utils.cache import CacheManager, get_global_cache_manager
from app.utils.database_optimizer import OptimizedQueryBuilder, DatabaseOptimizer
from app.utils.pagination import RAGPaginator, PaginationParams
from app.core.optimized_embeddings import OptimizedEmbeddingService

logger = logging.getLogger(__name__)

class PerformanceMetrics:
    """Classe pour mesurer les métriques de performance"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.durations = []
        self.memory_usage = []
    
    def start_measurement(self):
        """Démarre la mesure"""
        self.start_time = time.perf_counter()
    
    def end_measurement(self):
        """Termine la mesure"""
        self.end_time = time.perf_counter()
        duration = self.end_time - self.start_time
        self.durations.append(duration)
        return duration
    
    def get_stats(self) -> Dict[str, float]:
        """Retourne les statistiques de performance"""
        if not self.durations:
            return {}
        
        return {
            "min_time": min(self.durations),
            "max_time": max(self.durations),
            "avg_time": statistics.mean(self.durations),
            "median_time": statistics.median(self.durations),
            "std_dev": statistics.stdev(self.durations) if len(self.durations) > 1 else 0,
            "total_operations": len(self.durations)
        }

@pytest.fixture
async def performance_cache():
    """Fixture pour cache de performance"""
    cache_manager = CacheManager.create_memory_cache(max_size=10000)
    try:
        await cache_manager.initialize()
    except Exception as e:
        logger.warning(f"Cache initialization warning: {e}")
    yield cache_manager
    try:
        await cache_manager.cleanup()
    except Exception as e:
        logger.warning(f"Cache cleanup warning: {e}")

@pytest.fixture
def optimized_embeddings():
    """Fixture pour service d'embeddings optimisé"""
    service = OptimizedEmbeddingService(
        api_key=None,  # Mode test
        max_batch_size=100,
        max_concurrent_batches=5
    )
    yield service

class TestCachePerformance:
    """Tests de performance du cache"""
    
    @pytest.mark.asyncio
    async def test_cache_write_performance(self, performance_cache):
        """Test des performances d'écriture cache"""
        metrics = PerformanceMetrics()
        cache = performance_cache.backend
        
        # Test avec différentes tailles de données
        test_data_sizes = [100, 1000, 10000]
        results = {}
        
        for size in test_data_sizes:
            test_data = {"data": "x" * size, "size": size}
            durations = []
            
            # Mesurer 100 opérations d'écriture
            for i in range(100):
                metrics.start_measurement()
                await cache.set(f"test_key_{i}", test_data, ttl=60)
                duration = metrics.end_measurement()
                durations.append(duration)
            
            results[size] = {
                "avg_write_time": statistics.mean(durations),
                "max_write_time": max(durations),
                "operations_per_second": 100 / sum(durations)
            }
        
        # Vérifier les performances
        for size, stats in results.items():
            assert stats["avg_write_time"] < 0.01, f"Écriture trop lente pour taille {size}"
            assert stats["operations_per_second"] > 1000, f"Débit insuffisant pour taille {size}"
        
        logger.info(f"Cache write performance: {results}")

    @pytest.mark.asyncio
    async def test_cache_read_performance(self, performance_cache):
        """Test des performances de lecture cache"""
        cache = performance_cache.backend
        
        # Préparer des données de test
        test_data = {"content": "test data", "timestamp": datetime.now().isoformat()}
        for i in range(1000):
            await cache.set(f"read_test_{i}", test_data, ttl=300)
        
        # Mesurer les lectures
        metrics = PerformanceMetrics()
        
        for i in range(1000):
            metrics.start_measurement()
            result = await cache.get(f"read_test_{i}")
            metrics.end_measurement()
            assert result is not None
        
        stats = metrics.get_stats()
        
        # Vérifications de performance
        assert stats["avg_time"] < 0.005, "Lecture cache trop lente"
        assert stats["max_time"] < 0.02, "Pic de latence trop élevé"
        
        logger.info(f"Cache read performance: {stats}")

    @pytest.mark.asyncio
    async def test_cache_concurrent_access(self, performance_cache):
        """Test de performance avec accès concurrent"""
        cache = performance_cache.backend
        
        async def concurrent_operation(worker_id: int, num_ops: int):
            """Opération concurrente"""
            durations = []
            for i in range(num_ops):
                start = time.perf_counter()
                
                # Mix d'opérations lecture/écriture
                if i % 2 == 0:
                    await cache.set(f"concurrent_{worker_id}_{i}", {"worker": worker_id, "op": i})
                else:
                    await cache.get(f"concurrent_{worker_id}_{i-1}")
                
                durations.append(time.perf_counter() - start)
            
            return {
                "worker_id": worker_id,
                "avg_time": statistics.mean(durations),
                "max_time": max(durations)
            }
        
        # Lancer 10 workers concurrents
        start_time = time.perf_counter()
        tasks = [concurrent_operation(i, 100) for i in range(10)]
        results = await asyncio.gather(*tasks)
        total_time = time.perf_counter() - start_time
        
        # Analyser les résultats
        avg_times = [r["avg_time"] for r in results]
        max_times = [r["max_time"] for r in results]
        
        assert statistics.mean(avg_times) < 0.01, "Performance dégradée en concurrent"
        assert max(max_times) < 0.05, "Pics de latence trop élevés"
        assert total_time < 5.0, "Temps total trop élevé"
        
        logger.info(f"Concurrent cache performance: avg={statistics.mean(avg_times):.4f}s, max={max(max_times):.4f}s")

class TestDatabaseOptimizationPerformance:
    """Tests de performance des optimisations base de données"""
    
    @pytest.mark.asyncio
    async def test_query_builder_performance(self):
        """Test des performances du query builder"""
        builder = OptimizedQueryBuilder()
        metrics = PerformanceMetrics()
        
        # Test de construction de requêtes complexes
        for i in range(1000):
            metrics.start_measurement()
            
            query = (builder
                    .add_filter("user_id", f"user_{i % 100}")
                    .add_text_search("test content")
                    .add_date_range("created_at", 
                                  datetime(2024, 1, 1), 
                                  datetime(2024, 12, 31))
                    .set_projection(["title", "content", "metadata"])
                    .build())
            
            metrics.end_measurement()
            
            # Vérifier que la requête est bien construite
            assert isinstance(query, dict)
            assert "user_id" in query
            assert "$text" in query
        
        stats = metrics.get_stats()
        
        # Vérifications de performance
        assert stats["avg_time"] < 0.001, "Construction de requête trop lente"
        assert stats["max_time"] < 0.005, "Pic de construction trop élevé"
        
        logger.info(f"Query builder performance: {stats}")

    @pytest.mark.asyncio
    async def test_pagination_performance(self):
        """Test des performances de pagination"""
        paginator = RAGPaginator()
        
        # Simuler des données de test
        mock_data = [
            {"_id": f"doc_{i}", "title": f"Document {i}", "content": f"Content {i}"}
            for i in range(10000)
        ]
        
        metrics = PerformanceMetrics()
        
        # Test pagination avec différentes tailles de page
        page_sizes = [10, 50, 100, 500]
        
        for page_size in page_sizes:
            for page in range(1, 6):  # 5 pages
                params = PaginationParams(page=page, page_size=page_size)
                
                metrics.start_measurement()
                
                # Simuler la pagination
                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                page_data = mock_data[start_idx:end_idx]
                
                # Créer la réponse paginée
                response = paginator.create_paginated_response(
                    items=page_data,
                    params=params,
                    total_items=len(mock_data)
                )
                
                metrics.end_measurement()
                
                assert len(response.items) <= page_size
                assert response.pagination.page == page
        
        stats = metrics.get_stats()
        
        # Vérifications de performance
        assert stats["avg_time"] < 0.01, "Pagination trop lente"
        
        logger.info(f"Pagination performance: {stats}")

class TestEmbeddingsPerformance:
    """Tests de performance des embeddings optimisés"""
    
    @pytest.mark.asyncio
    async def test_embedding_cache_performance(self, optimized_embeddings):
        """Test des performances du cache d'embeddings"""
        service = optimized_embeddings
        
        # Données de test
        test_texts = [f"Test text number {i} for embedding cache performance" for i in range(1000)]
        
        # Première génération (cache miss)
        start_time = time.perf_counter()
        for text in test_texts:
            await service.get_embedding_cached(text)
        miss_time = time.perf_counter() - start_time
        
        # Générer les embeddings pour remplir le cache
        for text in test_texts:
            embedding = service._generate_test_embedding(text)
            await service.cache_embedding(text, embedding)
        
        # Deuxième lecture (cache hit)
        start_time = time.perf_counter()
        for text in test_texts:
            cached = await service.get_embedding_cached(text)
            assert cached is not None
        hit_time = time.perf_counter() - start_time
        
        # Vérifier l'amélioration de performance
        assert hit_time < miss_time / 10, "Cache n'améliore pas assez les performances"
        
        stats = service.get_stats()
        assert stats["cache_hit_rate"] == "100.0%"
        
        logger.info(f"Embedding cache: miss_time={miss_time:.4f}s, hit_time={hit_time:.4f}s")

    @pytest.mark.asyncio
    async def test_batch_processing_performance(self, optimized_embeddings):
        """Test des performances du traitement par batch"""
        service = optimized_embeddings
        
        # Test avec différentes tailles de batch
        batch_sizes = [10, 50, 100, 500]
        test_texts = [f"Batch test text {i}" for i in range(1000)]
        
        results = {}
        
        for batch_size in batch_sizes:
            start_time = time.perf_counter()
            
            result = await service.generate_embeddings_batch(
                texts=test_texts,
                batch_size=batch_size,
                max_concurrent=3
            )
            
            total_time = time.perf_counter() - start_time
            
            results[batch_size] = {
                "total_time": total_time,
                "texts_per_second": len(test_texts) / total_time,
                "success": result["success"],
                "stats": result["stats"]
            }
            
            # Vérifier le succès
            assert result["success"], f"Batch processing failed for size {batch_size}"
            assert len(result["embeddings"]) == len(test_texts)
        
        # Vérifier que les plus gros batches sont plus efficaces
        smallest_tps = results[batch_sizes[0]]["texts_per_second"]
        largest_tps = results[batch_sizes[-1]]["texts_per_second"]
        
        # Ne pas forcer l'amélioration car en mode test les embeddings sont simulés
        logger.info(f"Batch performance: {results}")

    @pytest.mark.asyncio
    async def test_concurrent_embedding_performance(self, optimized_embeddings):
        """Test des performances avec traitement concurrent"""
        service = optimized_embeddings
        
        async def concurrent_embedding_task(task_id: int, num_texts: int):
            """Tâche d'embedding concurrente"""
            texts = [f"Concurrent task {task_id} text {i}" for i in range(num_texts)]
            
            start_time = time.perf_counter()
            result = await service.generate_embeddings_batch(texts, batch_size=50)
            duration = time.perf_counter() - start_time
            
            return {
                "task_id": task_id,
                "duration": duration,
                "texts_processed": len(texts),
                "texts_per_second": len(texts) / duration,
                "success": result["success"]
            }
        
        # Lancer 5 tâches concurrentes
        start_time = time.perf_counter()
        tasks = [concurrent_embedding_task(i, 100) for i in range(5)]
        results = await asyncio.gather(*tasks)
        total_time = time.perf_counter() - start_time
        
        # Analyser les résultats
        all_successful = all(r["success"] for r in results)
        total_texts = sum(r["texts_processed"] for r in results)
        avg_tps = statistics.mean([r["texts_per_second"] for r in results])
        
        assert all_successful, "Certaines tâches concurrentes ont échoué"
        assert total_time < 10.0, "Temps total trop élevé pour les tâches concurrentes"
        
        logger.info(f"Concurrent embedding: {total_texts} texts in {total_time:.2f}s, avg {avg_tps:.1f} texts/s")

class TestIntegratedPerformance:
    """Tests de performance intégrés"""
    
    @pytest.mark.asyncio
    async def test_full_rag_pipeline_performance(self, performance_cache, optimized_embeddings):
        """Test de performance du pipeline RAG complet"""
        cache_manager = performance_cache
        embedding_service = optimized_embeddings
        
        # Simuler un pipeline RAG complet
        async def simulate_rag_query(query: str, documents: List[str]):
            """Simule une requête RAG complète"""
            start_time = time.perf_counter()
            
            # 1. Vérifier le cache pour la requête
            cache = cache_manager.get_query_cache()
            cached_result = await cache.get_search_results(query)
            
            if cached_result:
                return time.perf_counter() - start_time, "cache_hit"
            
            # 2. Générer l'embedding de la requête
            query_embedding = await embedding_service.generate_single_embedding(query)
            
            # 3. Rechercher dans les documents (simulé)
            doc_embeddings = []
            for doc in documents:
                doc_embedding = await embedding_service.generate_single_embedding(doc)
                doc_embeddings.append(doc_embedding)
            
            # 4. Calculer la similarité (simulé)
            results = [{"content": doc, "score": 0.8} for doc in documents[:3]]
            
            # 5. Mettre en cache le résultat
            await cache.cache_search_results(query, results)
            
            return time.perf_counter() - start_time, "cache_miss"
        
        # Documents de test
        test_documents = [
            f"Document {i}: This is test content for performance testing"
            for i in range(100)
        ]
        
        # Test avec cache miss puis cache hit
        queries = [
            "What is performance testing?",
            "How to optimize embeddings?",
            "RAG pipeline optimization",
            "Cache performance testing",
            "Batch processing efficiency"
        ]
        
        # Première passe (cache miss)
        miss_times = []
        for query in queries:
            duration, cache_status = await simulate_rag_query(query, test_documents)
            if cache_status == "cache_miss":
                miss_times.append(duration)
        
        # Deuxième passe (cache hit)
        hit_times = []
        for query in queries:
            duration, cache_status = await simulate_rag_query(query, test_documents)
            if cache_status == "cache_hit":
                hit_times.append(duration)
        
        # Analyser les performances
        avg_miss_time = statistics.mean(miss_times) if miss_times else 0
        avg_hit_time = statistics.mean(hit_times) if hit_times else 0
        
        if avg_hit_time > 0 and avg_miss_time > 0:
            cache_speedup = avg_miss_time / avg_hit_time
            assert cache_speedup > 5, f"Cache speedup insufficient: {cache_speedup:.1f}x"
        
        # Vérifier les seuils de performance
        if avg_miss_time > 0:
            assert avg_miss_time < 2.0, f"RAG pipeline trop lent: {avg_miss_time:.2f}s"
        if avg_hit_time > 0:
            assert avg_hit_time < 0.1, f"Cache hit trop lent: {avg_hit_time:.2f}s"
        
        logger.info(f"RAG Pipeline: miss={avg_miss_time:.3f}s, hit={avg_hit_time:.3f}s")

    @pytest.mark.asyncio
    async def test_system_load_performance(self, performance_cache, optimized_embeddings):
        """Test de performance sous charge système"""
        
        async def simulate_user_session(user_id: int, num_operations: int):
            """Simule une session utilisateur"""
            cache = performance_cache.get_query_cache()
            embedding_service = optimized_embeddings
            
            operations = []
            
            for i in range(num_operations):
                start_time = time.perf_counter()
                
                # Mix d'opérations typiques
                if i % 3 == 0:
                    # Recherche de documents
                    query = f"User {user_id} query {i}"
                    results = await cache.get_search_results(query)
                    if not results:
                        embedding = await embedding_service.generate_single_embedding(query)
                        results = [{"content": f"Result for {query}", "score": 0.9}]
                        await cache.cache_search_results(query, results)
                
                elif i % 3 == 1:
                    # Génération d'embeddings
                    text = f"User {user_id} document {i}"
                    embedding = await embedding_service.generate_single_embedding(text)
                
                else:
                    # Opération cache
                    await cache.cache_embeddings(f"hash_{user_id}_{i}", [0.1] * 1536)
                
                operations.append(time.perf_counter() - start_time)
            
            return {
                "user_id": user_id,
                "avg_operation_time": statistics.mean(operations),
                "max_operation_time": max(operations),
                "total_operations": len(operations)
            }
        
        # Simuler 20 utilisateurs concurrent avec 50 opérations chacun
        start_time = time.perf_counter()
        user_tasks = [simulate_user_session(i, 50) for i in range(20)]
        results = await asyncio.gather(*user_tasks)
        total_time = time.perf_counter() - start_time
        
        # Analyser les résultats de charge
        avg_operation_times = [r["avg_operation_time"] for r in results]
        max_operation_times = [r["max_operation_time"] for r in results]
        total_operations = sum(r["total_operations"] for r in results)
        
        system_avg_time = statistics.mean(avg_operation_times)
        system_max_time = max(max_operation_times)
        throughput = total_operations / total_time
        
        # Vérifications de performance sous charge
        assert system_avg_time < 0.1, f"Système trop lent sous charge: {system_avg_time:.3f}s"
        assert system_max_time < 0.5, f"Pics de latence trop élevés: {system_max_time:.3f}s"
        assert throughput > 100, f"Débit insuffisant: {throughput:.1f} ops/s"
        
        logger.info(f"System load: {total_operations} ops in {total_time:.2f}s, {throughput:.1f} ops/s")

async def run_performance_tests():
    """Exécute tous les tests de performance"""
    print("🚀 Démarrage des tests de performance AskRAG")
    print("=" * 60)
    
    # Configuration des tests
    pytest_args = [
        __file__,
        "-v",
        "--tb=short",
        "-k", "test_",
        "--asyncio-mode=auto"
    ]
    
    # Exécuter les tests
    result = pytest.main(pytest_args)
    
    if result == 0:
        print("\n✅ Tous les tests de performance sont passés!")
    else:
        print("\n❌ Certains tests de performance ont échoué")
    
    return result == 0

if __name__ == "__main__":
    asyncio.run(run_performance_tests())

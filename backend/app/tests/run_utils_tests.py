"""
Test runner simple pour les modules utilitaires
Test direct des fonctionnalités sans pytest complexe
"""

import asyncio
import sys
import os

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.utils.validation import InputValidator, ValidationError
from app.utils.response_formatter import ResponseFormatter
from app.utils.cache import CacheManager, MemoryCache, QueryCache
from app.utils.debug_helpers import RAGDebugger, DebugTimer, PerformanceMonitor
from app.utils.metrics import MetricsCollector, Counter, Gauge, Histogram, Timer


def test_input_validator():
    """Test du module de validation"""
    print("🧪 Testing InputValidator...")
    
    validator = InputValidator()
    
    # Test requête valide
    result = validator.validate_query("Qu'est-ce que l'IA ?")
    assert result["valid"] == True, "Requête valide devrait passer la validation"
    
    # Test requête vide
    result = validator.validate_query("")
    assert result["valid"] == False, "Requête vide devrait échouer"
    
    # Test requête trop longue
    result = validator.validate_query("x" * 2001)
    assert result["valid"] == False, "Requête trop longue devrait échouer"
    
    # Test session ID valide
    result = validator.validate_session_id("session_123")
    assert result["valid"] == True, "Session ID valide devrait passer"
    
    print("✅ InputValidator tests passed!")


def test_response_formatter():
    """Test du module de formatage des réponses"""
    print("🧪 Testing ResponseFormatter...")
    
    formatter = ResponseFormatter()
    
    # Test réponse de succès
    response = formatter.success({"key": "value"}, "Success message")
    assert response.success == True
    assert response.message == "Success message"
    assert response.data == {"key": "value"}
    
    # Test réponse d'erreur
    response = formatter.error("Error message", 400, "ERROR_CODE")
    assert response.success == False
    assert response.status_code == 400
    assert response.error == "ERROR_CODE"
    
    # Test réponse paginée
    response = formatter.paginated([1, 2, 3], total=100, page=1, per_page=3)
    assert response.success == True
    assert response.data["pagination"]["total"] == 100
    
    print("✅ ResponseFormatter tests passed!")


async def test_cache_system():
    """Test du système de cache"""
    print("🧪 Testing Cache System...")
    
    cache_manager = CacheManager.create_memory_cache()
    cache = cache_manager.backend
    
    # Test opérations de base
    await cache.set("key1", "value1")
    value = await cache.get("key1")
    assert value == "value1", "Cache set/get should work"
    
    # Test existence
    exists = await cache.exists("key1")
    assert exists == True, "Key should exist"
    
    # Test suppression
    deleted = await cache.delete("key1")
    assert deleted == True, "Key should be deleted"
    
    # Test QueryCache
    query_cache = cache_manager.get_query_cache()
    
    # Test cache de recherche
    query = "test query"
    results = [{"content": "result1"}]
    
    # Cache miss
    cached = await query_cache.get_search_results(query)
    assert cached is None, "Should be cache miss initially"
    
    # Cache set
    success = await query_cache.cache_search_results(query, results)
    assert success == True, "Cache set should succeed"
    
    # Cache hit
    cached = await query_cache.get_search_results(query)
    assert cached == results, "Should get cached results"
    
    # Test health check
    health = await cache_manager.health_check()
    assert health["status"] == "healthy", "Cache should be healthy"
    
    print("✅ Cache System tests passed!")


def test_debug_helpers():
    """Test des helpers de debug"""
    print("🧪 Testing Debug Helpers...")
    
    # Test DebugTimer
    import time
    
    timer = DebugTimer("test_timer")
    timer.start()
    time.sleep(0.01)  # 10ms
    duration = timer.stop()
    assert duration >= 0.01, "Timer should measure at least 10ms"
    
    # Test RAGDebugger
    debugger = RAGDebugger(enabled=True)
    
    debugger.log_step("step1", {"data": "value1"})
    debugger.log_step("step2", {"data": "value2"})
    
    summary = debugger.get_debug_summary()
    assert summary["total_steps"] == 2, "Should have 2 steps"
    assert len(summary["steps"]) == 2, "Should have 2 step records"
    
    # Test PerformanceMonitor
    monitor = PerformanceMonitor()
    monitor.record_call("function1", 0.1)
    monitor.record_call("function1", 0.2)
    
    report = monitor.get_performance_report()
    assert "function1" in report["performance_metrics"]
    assert report["performance_metrics"]["function1"]["call_count"] == 2
    
    print("✅ Debug Helpers tests passed!")


def test_metrics_system():
    """Test du système de métriques"""
    print("🧪 Testing Metrics System...")
    
    # Test Counter
    counter = Counter("test_counter")
    counter.increment()
    counter.increment(5)
    assert counter.get_value() == 6, "Counter should be 6"
    
    # Test Gauge
    gauge = Gauge("test_gauge")
    gauge.set(10)
    gauge.increment(5)
    assert gauge.get_value() == 15, "Gauge should be 15"
    
    # Test Histogram
    histogram = Histogram("test_histogram")
    for value in [1, 2, 3, 4, 5]:
        histogram.observe(value)
    
    summary = histogram.get_summary()
    assert summary.count == 5, "Should have 5 observations"
    assert summary.average == 3, "Average should be 3"
    
    # Test MetricsCollector
    collector = MetricsCollector()
    
    # Test métriques RAG
    collector.rag_metrics.record_query(duration=1.0, results_count=3, confidence=0.8)
    assert collector.rag_metrics.total_queries.get_value() == 1
    
    # Test aperçu système
    overview = collector.get_system_overview()
    assert "overview" in overview
    assert "performance" in overview
    
    print("✅ Metrics System tests passed!")


async def test_integration():
    """Test d'intégration simple"""
    print("🧪 Testing Integration...")
    
    validator = InputValidator()
    formatter = ResponseFormatter()
    cache = CacheManager.create_memory_cache()
    debugger = RAGDebugger(enabled=True)
    metrics = MetricsCollector()
    
    # Workflow simple
    query = "Test query for integration"
    
    # 1. Validation
    validation = validator.validate_query(query)
    assert validation["valid"] == True
    
    # 2. Cache check
    query_cache = cache.get_query_cache()
    cached = await query_cache.get_search_results(query)
    assert cached is None  # Cache miss
    
    # 3. Simulation de traitement
    debugger.log_step("processing", {"query": query})
    results = [{"content": "Simulated result", "score": 0.9}]
    
    # 4. Cache set
    await query_cache.cache_search_results(query, results)
    
    # 5. Métriques
    metrics.rag_metrics.record_query(duration=0.5, results_count=1, confidence=0.9)
    
    # 6. Formatage réponse
    response = formatter.rag_response(
        answer="Simulated answer",
        sources=results,
        citations=[],
        confidence=0.9,
        processing_time=0.5
    )
    
    assert response.success == True
    assert response.data["answer"] == "Simulated answer"
    
    # Vérifications finales
    debug_summary = debugger.get_debug_summary()
    assert debug_summary["total_steps"] >= 1
    
    overview = metrics.get_system_overview()
    assert overview["overview"]["total_queries"] >= 1
    
    print("✅ Integration tests passed!")


async def run_all_tests():
    """Exécute tous les tests"""
    print("🚀 Starting utility modules tests...\n")
    
    try:
        test_input_validator()
        test_response_formatter()
        await test_cache_system()
        test_debug_helpers()
        test_metrics_system()
        await test_integration()
        
        print("\n🎉 All tests passed successfully!")
        print("✅ Step 16.3.6 - All utility modules tested and working!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

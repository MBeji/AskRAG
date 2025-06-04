"""
Tests pour les modules utilitaires RAG
Étape 16.3.6 - Tester les utilitaires
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from app.utils.validation import InputValidator, ValidationError
from app.utils.response_formatter import ResponseFormatter, APIResponse
from app.utils.cache import CacheManager, MemoryCache, QueryCache, CacheKey
from app.utils.debug_helpers import RAGDebugger, DebugTimer, PerformanceMonitor, debug_timing
from app.utils.metrics import MetricsCollector, Counter, Gauge, Histogram, Timer, RAGMetrics


class TestInputValidator:
    """Tests pour le module de validation"""
    
    def setup_method(self):
        self.validator = InputValidator()
    
    def test_validate_query_valid(self):
        """Test validation d'une requête valide"""
        query = "Qu'est-ce que l'intelligence artificielle ?"
        result = self.validator.validate_query(query)
        
        assert result["valid"] == True
        assert result["cleaned_query"] == query
        assert len(result["errors"]) == 0
    
    def test_validate_query_empty(self):
        """Test validation d'une requête vide"""
        result = self.validator.validate_query("")
        
        assert result["valid"] == False
        assert "Requête vide" in result["errors"]
    
    def test_validate_query_too_long(self):
        """Test validation d'une requête trop longue"""
        long_query = "x" * 2001
        result = self.validator.validate_query(long_query)
        
        assert result["valid"] == False
        assert "trop longue" in result["errors"][0]
    
    def test_validate_query_with_xss(self):
        """Test validation avec tentative XSS"""
        xss_query = "<script>alert('xss')</script>Quelle est ma question ?"
        result = self.validator.validate_query(xss_query)
        
        assert result["valid"] == True
        assert "<script>" not in result["cleaned_query"]
        assert "Quelle est ma question ?" in result["cleaned_query"]
    
    def test_validate_session_id_valid(self):
        """Test validation d'un session_id valide"""
        session_id = "session_123456"
        result = self.validator.validate_session_id(session_id)
        
        assert result["valid"] == True
        assert result["session_id"] == session_id
    
    def test_validate_session_id_invalid(self):
        """Test validation d'un session_id invalide"""
        result = self.validator.validate_session_id("../../../etc/passwd")
        
        assert result["valid"] == False
        assert "caractères invalides" in result["errors"][0]
    
    def test_validate_upload_file_valid(self):
        """Test validation d'un fichier valide"""
        mock_file = Mock()
        mock_file.filename = "document.pdf"
        mock_file.size = 1024 * 1024  # 1MB
        
        result = self.validator.validate_upload_file(mock_file)
        
        assert result["valid"] == True
        assert result["file_type"] == "pdf"
    
    def test_validate_upload_file_too_large(self):
        """Test validation d'un fichier trop volumineux"""
        mock_file = Mock()
        mock_file.filename = "huge.pdf"
        mock_file.size = 100 * 1024 * 1024  # 100MB
        
        result = self.validator.validate_upload_file(mock_file)
        
        assert result["valid"] == False
        assert "trop volumineux" in result["errors"][0]
    
    def test_validate_search_params_valid(self):
        """Test validation de paramètres de recherche valides"""
        result = self.validator.validate_search_params(
            query="test",
            limit=10,
            threshold=0.8
        )
        
        assert result["valid"] == True
        assert result["cleaned_params"]["limit"] == 10
        assert result["cleaned_params"]["threshold"] == 0.8
    
    def test_validate_search_params_invalid_limit(self):
        """Test validation avec limite invalide"""
        result = self.validator.validate_search_params(
            query="test",
            limit=200,  # Trop élevé
            threshold=0.8
        )
        
        assert result["valid"] == False
        assert "limite invalide" in result["errors"][0]


class TestResponseFormatter:
    """Tests pour le module de formatage des réponses"""
    
    def setup_method(self):
        self.formatter = ResponseFormatter()
    
    def test_success_response(self):
        """Test formatage d'une réponse de succès"""
        data = {"key": "value"}
        response = self.formatter.success(data, "Opération réussie")
        
        assert response.success == True
        assert response.message == "Opération réussie"
        assert response.data == data
        assert response.error is None
    
    def test_error_response(self):
        """Test formatage d'une réponse d'erreur"""
        response = self.formatter.error("Erreur de test", 400, "VALIDATION_ERROR")
        
        assert response.success == False
        assert response.message == "Erreur de test"
        assert response.error == "VALIDATION_ERROR"
        assert response.status_code == 400
    
    def test_paginated_response(self):
        """Test formatage d'une réponse paginée"""
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        response = self.formatter.paginated(
            items=items,
            total=100,
            page=2,
            per_page=3
        )
        
        assert response.success == True
        assert response.data["items"] == items
        assert response.data["pagination"]["total"] == 100
        assert response.data["pagination"]["page"] == 2
        assert response.data["pagination"]["total_pages"] == 34
    
    def test_rag_response(self):
        """Test formatage d'une réponse RAG"""
        sources = [{"content": "source1"}]
        citations = [{"text": "citation1"}]
        
        response = self.formatter.rag_response(
            answer="Réponse test",
            sources=sources,
            citations=citations,
            confidence=0.9,
            processing_time=1.5
        )
        
        assert response.success == True
        assert response.data["answer"] == "Réponse test"
        assert response.data["sources"] == sources
        assert response.data["confidence"] == 0.9
        assert response.data["processing_time"] == 1.5


class TestCacheSystem:
    """Tests pour le système de cache"""
    
    @pytest.fixture
    def cache_manager(self):
        return CacheManager.create_memory_cache(max_size=100)
    
    @pytest.mark.asyncio
    async def test_memory_cache_basic_operations(self, cache_manager):
        """Test opérations de base du cache mémoire"""
        cache = cache_manager.backend
        
        # Test set/get
        await cache.set("key1", "value1", ttl=60)
        value = await cache.get("key1")
        assert value == "value1"
        
        # Test exists
        exists = await cache.exists("key1")
        assert exists == True
        
        # Test delete
        deleted = await cache.delete("key1")
        assert deleted == True
        
        # Vérifier suppression
        value = await cache.get("key1")
        assert value is None
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self, cache_manager):
        """Test expiration du cache"""
        cache = cache_manager.backend
        
        # Ajouter avec TTL court
        await cache.set("expiring_key", "value", ttl=1)
        
        # Vérifier présence immédiate
        value = await cache.get("expiring_key")
        assert value == "value"
        
        # Attendre expiration
        await asyncio.sleep(1.1)
        
        # Vérifier expiration
        value = await cache.get("expiring_key")
        assert value is None
    
    @pytest.mark.asyncio
    async def test_query_cache_operations(self, cache_manager):
        """Test opérations du cache de requêtes"""
        query_cache = cache_manager.get_query_cache()
        
        # Test cache de recherche
        query = "test query"
        results = [{"content": "result1"}, {"content": "result2"}]
        
        # Cache miss initial
        cached_results = await query_cache.get_search_results(query)
        assert cached_results is None
        
        # Mise en cache
        success = await query_cache.cache_search_results(query, results)
        assert success == True
        
        # Cache hit
        cached_results = await query_cache.get_search_results(query)
        assert cached_results == results
    
    @pytest.mark.asyncio
    async def test_cache_key_generation(self):
        """Test génération des clés de cache"""
        # Test clé de requête
        key1 = CacheKey.for_query("test query", {"filter": "value"})
        key2 = CacheKey.for_query("test query", {"filter": "value"})
        key3 = CacheKey.for_query("different query", {"filter": "value"})
        
        assert key1 == key2  # Même requête = même clé
        assert key1 != key3  # Requête différente = clé différente
        
        # Test clé de document
        doc_key = CacheKey.for_document_chunks("doc123")
        assert doc_key == "doc_chunks:doc123"
    
    @pytest.mark.asyncio
    async def test_cache_health_check(self, cache_manager):
        """Test health check du cache"""
        health = await cache_manager.health_check()
        
        assert health["status"] == "healthy"
        assert health["backend"] == "MemoryCache"
        assert "stats" in health


class TestDebugHelpers:
    """Tests pour les helpers de debug"""
    
    def test_debug_timer(self):
        """Test du timer de debug"""
        timer = DebugTimer("test_operation")
        
        timer.start()
        time.sleep(0.1)
        duration = timer.stop()
        
        assert duration >= 0.1
        assert timer.duration == duration
    
    def test_debug_timer_context_manager(self):
        """Test du timer comme context manager"""
        with DebugTimer("test_context") as timer:
            time.sleep(0.05)
        
        assert timer.duration >= 0.05
    
    def test_rag_debugger_logging(self):
        """Test du debugger RAG"""
        debugger = RAGDebugger(enabled=True)
        
        # Log quelques étapes
        debugger.log_step("step1", {"data": "value1"})
        debugger.log_step("step2", {"data": "value2"})
        
        summary = debugger.get_debug_summary()
        
        assert summary["enabled"] == True
        assert summary["total_steps"] == 2
        assert len(summary["steps"]) == 2
        assert summary["steps"][0]["name"] == "step1"
    
    def test_rag_debugger_timers(self):
        """Test des timers du debugger"""
        debugger = RAGDebugger(enabled=True)
        
        timer = debugger.start_timer("test_timer")
        time.sleep(0.05)
        duration = debugger.stop_timer("test_timer")
        
        assert duration >= 0.05
        
        summary = debugger.get_debug_summary()
        assert "test_timer" in summary["timers"]
    
    def test_performance_monitor(self):
        """Test du moniteur de performances"""
        monitor = PerformanceMonitor()
        
        # Enregistrer quelques appels
        monitor.record_call("function1", 0.1)
        monitor.record_call("function1", 0.2)
        monitor.record_call("function2", 0.05)
        
        report = monitor.get_performance_report()
        
        assert "function1" in report["performance_metrics"]
        assert report["performance_metrics"]["function1"]["call_count"] == 2
        assert report["performance_metrics"]["function1"]["average_time"] == 0.15
        assert report["summary"]["total_functions"] == 2
    
    @pytest.mark.asyncio
    async def test_debug_timing_decorator(self):
        """Test du décorateur de timing"""
        
        @debug_timing("test_function")
        async def async_test_function():
            await asyncio.sleep(0.05)
            return "result"
        
        result = await async_test_function()
        assert result == "result"


class TestMetrics:
    """Tests pour le système de métriques"""
    
    def test_counter_operations(self):
        """Test opérations de compteur"""
        counter = Counter("test_counter")
        
        # Test incrémentation
        counter.increment()
        assert counter.get_value() == 1
        
        counter.increment(5)
        assert counter.get_value() == 6
        
        # Test summary
        summary = counter.get_summary()
        assert summary.current_value == 6
        assert summary.type.value == "counter"
    
    def test_gauge_operations(self):
        """Test opérations de jauge"""
        gauge = Gauge("test_gauge")
        
        # Test set/increment/decrement
        gauge.set(10)
        assert gauge.get_value() == 10
        
        gauge.increment(5)
        assert gauge.get_value() == 15
        
        gauge.decrement(3)
        assert gauge.get_value() == 12
        
        summary = gauge.get_summary()
        assert summary.current_value == 12
        assert summary.type.value == "gauge"
    
    def test_histogram_operations(self):
        """Test opérations d'histogramme"""
        histogram = Histogram("test_histogram", max_size=10)
        
        # Ajouter des valeurs
        values = [1, 2, 3, 4, 5]
        for value in values:
            histogram.observe(value)
        
        summary = histogram.get_summary()
        assert summary.count == 5
        assert summary.sum_value == 15
        assert summary.min_value == 1
        assert summary.max_value == 5
        assert summary.average == 3
        
        # Test percentiles
        p50 = histogram.get_percentile(50)
        assert p50 == 3
    
    def test_timer_operations(self):
        """Test opérations de timer"""
        timer = Timer("test_timer")
        
        # Observer quelques durées
        timer.observe(0.1)
        timer.observe(0.2)
        timer.observe(0.15)
        
        summary = timer.get_summary()
        assert summary.count == 3
        assert summary.average == 0.15
        assert summary.type.value == "timer"
    
    def test_rag_metrics_integration(self):
        """Test intégration des métriques RAG"""
        rag_metrics = RAGMetrics()
        
        # Enregistrer quelques opérations
        rag_metrics.record_query(duration=1.5, results_count=3, confidence=0.8)
        rag_metrics.record_document_upload(success=True, processing_time=2.0, chunks_count=10)
        rag_metrics.record_llm_call(duration=0.5, success=True)
        
        # Vérifier les métriques
        assert rag_metrics.total_queries.get_value() == 1
        assert rag_metrics.document_uploads.get_value() == 1
        assert rag_metrics.llm_calls.get_value() == 1
        
        # Test cache hit rate
        rag_metrics.record_cache_operation(hit=True)
        rag_metrics.record_cache_operation(hit=False)
        
        hit_rate = rag_metrics.get_cache_hit_rate()
        assert hit_rate == 0.5
    
    def test_metrics_collector(self):
        """Test du collecteur de métriques"""
        collector = MetricsCollector()
        
        # Créer des métriques personnalisées
        custom_counter = collector.create_counter("custom_metric")
        custom_counter.increment(5)
        
        # Récupérer toutes les métriques
        all_metrics = collector.get_all_metrics()
        
        assert "custom_metric" in all_metrics
        assert all_metrics["custom_metric"].current_value == 5
        
        # Test aperçu système
        overview = collector.get_system_overview()
        
        assert "overview" in overview
        assert "performance" in overview
        assert "quality" in overview
        assert overview["overview"]["total_queries"] >= 0
    
    def test_prometheus_export(self):
        """Test export format Prometheus"""
        collector = MetricsCollector()
        
        # Ajouter quelques métriques
        counter = collector.create_counter("test_counter", "Test counter metric")
        counter.increment(42)
        
        prometheus_output = collector.export_prometheus_format()
        
        assert "# TYPE test_counter counter" in prometheus_output
        assert "# HELP test_counter Test counter metric" in prometheus_output
        assert "test_counter 42" in prometheus_output


if __name__ == "__main__":
    # Exécuter les tests avec pytest
    pytest.main([__file__, "-v"])

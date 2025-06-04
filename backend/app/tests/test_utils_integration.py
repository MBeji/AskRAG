"""
Test d'intégration pour tous les modules utilitaires
Vérifie que tous les modules fonctionnent ensemble correctement
"""

import asyncio
import pytest
import time
from unittest.mock import Mock

from app.utils import (
    InputValidator, ResponseFormatter, CacheManager, 
    RAGDebugger, MetricsCollector, debug_timing
)


class TestUtilsIntegration:
    """Test d'intégration des modules utilitaires"""
    
    @pytest.fixture
    def utils_setup(self):
        """Setup pour tous les utilitaires"""
        return {
            "validator": InputValidator(),
            "formatter": ResponseFormatter(),
            "cache": CacheManager.create_memory_cache(),
            "debugger": RAGDebugger(enabled=True),
            "metrics": MetricsCollector()
        }
    
    @pytest.mark.asyncio
    async def test_complete_rag_workflow_simulation(self, utils_setup):
        """Simule un workflow RAG complet avec tous les utilitaires"""
        validator = utils_setup["validator"]
        formatter = utils_setup["formatter"]
        cache = utils_setup["cache"]
        debugger = utils_setup["debugger"]
        metrics = utils_setup["metrics"]
        
        # === 1. Validation d'une requête utilisateur ===
        user_query = "Qu'est-ce que l'intelligence artificielle ?"
        validation_result = validator.validate_query(user_query)
        
        assert validation_result["valid"] == True
        cleaned_query = validation_result["cleaned_query"]
        
        # Métriques : enregistrer la validation
        if validation_result["valid"]:
            metrics.rag_metrics.total_queries.increment()
        
        # Debug : log de l'étape de validation
        debugger.log_step("query_validation", {
            "original_query": user_query,
            "cleaned_query": cleaned_query,
            "valid": validation_result["valid"]
        })
        
        # === 2. Vérification du cache ===
        query_cache = cache.get_query_cache()
        
        # Simuler une vérification de cache
        start_time = time.time()
        cached_result = await query_cache.get_search_results(cleaned_query)
        cache_time = time.time() - start_time
        
        # Métriques : opération de cache
        metrics.rag_metrics.record_cache_operation(hit=cached_result is not None)
        
        # Debug : log de l'opération de cache
        debugger.log_cache_operation("get", cleaned_query, cached_result is not None, cache_time)
        
        # === 3. Simulation de recherche sémantique ===
        if cached_result is None:
            # Simuler une recherche
            search_timer = debugger.start_timer("semantic_search")
            
            # Simulation d'une recherche de 100ms
            await asyncio.sleep(0.1)
            
            search_duration = debugger.stop_timer("semantic_search")
            
            # Résultats simulés
            search_results = [
                {"content": "L'IA est une technologie...", "score": 0.9},
                {"content": "L'intelligence artificielle permet...", "score": 0.8},
                {"content": "Les algorithmes d'IA...", "score": 0.7}
            ]
            
            # Métriques de recherche
            scores = [r["score"] for r in search_results]
            metrics.rag_metrics.record_search(search_duration, len(search_results), scores)
            
            # Debug de la recherche
            debugger.log_search_results(cleaned_query, len(search_results), search_duration)
            
            # Mise en cache des résultats
            await query_cache.cache_search_results(cleaned_query, search_results)
            
        else:
            search_results = cached_result
            debugger.log_step("cache_hit", {"query": cleaned_query})
        
        # === 4. Simulation d'appel LLM ===
        llm_timer = debugger.start_timer("llm_call")
        
        # Simulation d'un appel LLM de 200ms
        await asyncio.sleep(0.2)
        
        llm_duration = debugger.stop_timer("llm_call")
        
        # Réponse simulée
        llm_response = {
            "answer": "L'intelligence artificielle (IA) est une technologie qui permet aux machines d'imiter l'intelligence humaine...",
            "confidence": 0.85
        }
        
        # Métriques LLM
        metrics.rag_metrics.record_llm_call(llm_duration, success=True)
        
        # Debug LLM
        debugger.log_llm_call(
            prompt_length=500,
            response_length=len(llm_response["answer"]),
            call_time=llm_duration
        )
        
        # === 5. Formatage de la réponse finale ===
        total_time = time.time() - start_time
        
        final_response = formatter.rag_response(
            answer=llm_response["answer"],
            sources=search_results,
            citations=[],
            confidence=llm_response["confidence"],
            processing_time=total_time
        )
        
        # Métriques finales
        metrics.rag_metrics.record_query(
            duration=total_time,
            results_count=len(search_results),
            confidence=llm_response["confidence"]
        )
        
        # Debug final
        debugger.log_step("response_generated", {
            "total_time": total_time,
            "confidence": llm_response["confidence"],
            "sources_count": len(search_results)
        })
        
        # === 6. Vérifications ===
        assert final_response.success == True
        assert final_response.data["answer"] == llm_response["answer"]
        assert final_response.data["confidence"] == llm_response["confidence"]
        assert len(final_response.data["sources"]) == len(search_results)
        
        # Vérifier les métriques
        assert metrics.rag_metrics.total_queries.get_value() >= 1
        assert metrics.rag_metrics.llm_calls.get_value() >= 1
        
        # Vérifier le debug
        debug_summary = debugger.get_debug_summary()
        assert debug_summary["total_steps"] >= 4
        assert "semantic_search" in debug_summary["timers"]
        assert "llm_call" in debug_summary["timers"]
        
        return final_response
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self, utils_setup):
        """Test la gestion d'erreurs dans le workflow"""
        validator = utils_setup["validator"]
        formatter = utils_setup["formatter"]
        debugger = utils_setup["debugger"]
        metrics = utils_setup["metrics"]
        
        # === Test avec requête invalide ===
        invalid_query = ""  # Requête vide
        validation_result = validator.validate_query(invalid_query)
        
        assert validation_result["valid"] == False
        
        # Formater la réponse d'erreur
        error_response = formatter.error(
            message="Requête invalide",
            status_code=400,
            error_code="INVALID_QUERY",
            details={"errors": validation_result["errors"]}
        )
        
        # Debug de l'erreur
        debugger.log_error(
            ValueError("Requête invalide"),
            context={"validation_errors": validation_result["errors"]}
        )
        
        # Métriques d'erreur
        metrics.rag_metrics.query_errors.increment()
        
        # Vérifications
        assert error_response.success == False
        assert error_response.status_code == 400
        assert error_response.error == "INVALID_QUERY"
        
        # Vérifier les métriques d'erreur
        assert metrics.rag_metrics.query_errors.get_value() >= 1
        
        # Vérifier le debug d'erreur
        debug_summary = debugger.get_debug_summary()
        error_steps = [step for step in debug_summary["steps"] if step["name"] == "error"]
        assert len(error_steps) >= 1
    
    @pytest.mark.asyncio 
    async def test_performance_monitoring_workflow(self, utils_setup):
        """Test du monitoring de performance"""
        metrics = utils_setup["metrics"]
        debugger = utils_setup["debugger"]
        
        # Simuler plusieurs opérations pour collecter des métriques
        for i in range(5):
            # Simuler des requêtes avec des temps variables
            query_time = 0.1 + (i * 0.05)  # De 0.1 à 0.3 secondes
            
            metrics.rag_metrics.record_query(
                duration=query_time,
                results_count=3 + i,
                confidence=0.7 + (i * 0.05)
            )
            
            # Simuler des uploads
            if i % 2 == 0:
                metrics.rag_metrics.record_document_upload(
                    success=True,
                    processing_time=1.0 + i,
                    chunks_count=10 + i
                )
        
        # Obtenir l'aperçu système
        overview = metrics.get_system_overview()
        
        # Vérifications
        assert overview["overview"]["total_queries"] == 5
        assert overview["overview"]["total_documents"] == 3  # 3 uploads (indices pairs)
        assert overview["performance"]["avg_query_duration"] > 0
        
        # Vérifier les métriques détaillées
        all_metrics = metrics.get_all_metrics()
        assert "total_queries" in all_metrics
        assert all_metrics["total_queries"].current_value == 5
        
        # Test export Prometheus
        prometheus_export = metrics.export_prometheus_format()
        assert "total_queries 5" in prometheus_export
        assert "# TYPE total_queries counter" in prometheus_export
    
    @pytest.mark.asyncio
    async def test_cache_invalidation_workflow(self, utils_setup):
        """Test de l'invalidation de cache"""
        cache = utils_setup["cache"]
        debugger = utils_setup["debugger"]
        
        query_cache = cache.get_query_cache()
        
        # === Scénario : Upload d'un nouveau document ===
        document_id = "doc_123"
        query = "test query"
        
        # 1. Mettre en cache des résultats initiaux
        initial_results = [{"content": "old content", "score": 0.8}]
        await query_cache.cache_search_results(query, initial_results)
        
        # Vérifier la présence en cache
        cached = await query_cache.get_search_results(query)
        assert cached == initial_results
        
        debugger.log_step("initial_cache", {"query": query, "cached": True})
        
        # 2. Simuler l'upload d'un nouveau document qui affecte les résultats
        # Invalider le cache du document
        invalidated = await query_cache.invalidate_document_cache(document_id)
        
        debugger.log_step("document_uploaded", {
            "document_id": document_id,
            "cache_invalidated": invalidated
        })
        
        # 3. Les prochaines requêtes devraient donner de nouveaux résultats
        # (simulation - en réalité il faudrait refaire la recherche)
        new_results = [
            {"content": "old content", "score": 0.8},
            {"content": "new content from uploaded doc", "score": 0.9}
        ]
        
        await query_cache.cache_search_results(query, new_results)
        
        # Vérifier les nouveaux résultats
        updated_cached = await query_cache.get_search_results(query)
        assert len(updated_cached) == 2
        assert any("new content" in result["content"] for result in updated_cached)
        
        debugger.log_step("cache_updated", {
            "query": query,
            "new_results_count": len(new_results)
        })
        
        # Vérifier le debug
        debug_summary = debugger.get_debug_summary()
        assert debug_summary["total_steps"] >= 3
    
    def test_all_modules_health_check(self, utils_setup):
        """Test de santé de tous les modules"""
        validator = utils_setup["validator"]
        formatter = utils_setup["formatter"]
        cache = utils_setup["cache"]
        debugger = utils_setup["debugger"]
        metrics = utils_setup["metrics"]
        
        # Test validator
        validation_result = validator.validate_query("test")
        assert validation_result["valid"] == True
        
        # Test formatter  
        response = formatter.success({"test": "data"})
        assert response.success == True
        
        # Test cache health
        cache_health = asyncio.run(cache.health_check())
        assert cache_health["status"] == "healthy"
        
        # Test debugger
        debugger.log_step("health_check")
        debug_summary = debugger.get_debug_summary()
        assert debug_summary["enabled"] == True
        
        # Test metrics
        test_counter = metrics.create_counter("health_check_counter")
        test_counter.increment()
        assert test_counter.get_value() == 1
        
        overview = metrics.get_system_overview()
        assert "overview" in overview


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

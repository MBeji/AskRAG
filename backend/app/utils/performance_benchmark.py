"""
Utilitaires de benchmark pour AskRAG
Étape 16.4.5 - Métriques et mesures de performance
"""

import time
import asyncio
import statistics
from typing import List, Dict, Any, Callable, Optional
from datetime import datetime
import psutil
import logging

logger = logging.getLogger(__name__)

class PerformanceBenchmark:
    """Classe utilitaire pour mesurer les performances"""
    
    def __init__(self, name: str):
        self.name = name
        self.measurements = []
        self.start_time = None
        self.memory_start = None
        
    def start(self):
        """Démarre la mesure"""
        self.start_time = time.perf_counter()
        self.memory_start = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
    def stop(self) -> Dict[str, Any]:
        """Arrête la mesure et retourne les métriques"""
        if self.start_time is None:
            raise ValueError("Benchmark non démarré")
            
        duration = time.perf_counter() - self.start_time
        memory_end = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_used = memory_end - self.memory_start
        
        measurement = {
            "duration": duration,
            "memory_used": memory_used,
            "timestamp": datetime.now().isoformat()
        }
        
        self.measurements.append(measurement)
        
        # Reset pour la prochaine mesure
        self.start_time = None
        self.memory_start = None
        
        return measurement
        
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques agrégées"""
        if not self.measurements:
            return {}
            
        durations = [m["duration"] for m in self.measurements]
        memory_usage = [m["memory_used"] for m in self.measurements]
        
        return {
            "name": self.name,
            "total_measurements": len(self.measurements),
            "duration": {
                "min": min(durations),
                "max": max(durations),
                "avg": statistics.mean(durations),
                "median": statistics.median(durations),
                "std_dev": statistics.stdev(durations) if len(durations) > 1 else 0
            },
            "memory": {
                "min": min(memory_usage),
                "max": max(memory_usage),
                "avg": statistics.mean(memory_usage)
            },
            "throughput": {
                "ops_per_second": len(self.measurements) / sum(durations) if sum(durations) > 0 else 0
            }
        }

class AsyncBenchmark:
    """Benchmark pour fonctions asynchrones"""
    
    def __init__(self, name: str):
        self.name = name
        self.benchmark = PerformanceBenchmark(name)
        
    async def measure(self, func: Callable, *args, **kwargs) -> Any:
        """Mesure l'exécution d'une fonction async"""
        self.benchmark.start()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            self.benchmark.stop()
            
    async def measure_multiple(self, func: Callable, iterations: int, *args, **kwargs) -> List[Any]:
        """Mesure plusieurs exécutions"""
        results = []
        for _ in range(iterations):
            result = await self.measure(func, *args, **kwargs)
            results.append(result)
        return results
        
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques"""
        return self.benchmark.get_stats()

class LoadTester:
    """Testeur de charge pour fonctions concurrentes"""
    
    def __init__(self, name: str):
        self.name = name
        self.results = []
        
    async def run_concurrent_load(self, 
                                func: Callable,
                                concurrent_users: int,
                                operations_per_user: int,
                                *args, **kwargs) -> Dict[str, Any]:
        """Exécute un test de charge concurrent"""
        
        async def user_session(user_id: int):
            """Simule une session utilisateur"""
            user_times = []
            for op in range(operations_per_user):
                start = time.perf_counter()
                try:
                    await func(*args, **kwargs)
                    duration = time.perf_counter() - start
                    user_times.append(duration)
                except Exception as e:
                    logger.error(f"Erreur user {user_id}, op {op}: {e}")
                    user_times.append(float('inf'))  # Marquer comme échec
                    
            return {
                "user_id": user_id,
                "operations": operations_per_user,
                "avg_time": statistics.mean([t for t in user_times if t != float('inf')]),
                "errors": sum(1 for t in user_times if t == float('inf')),
                "total_time": sum(user_times)
            }
        
        # Démarrer tous les utilisateurs en parallèle
        start_time = time.perf_counter()
        
        tasks = [user_session(i) for i in range(concurrent_users)]
        user_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.perf_counter() - start_time
        
        # Analyser les résultats
        successful_results = [r for r in user_results if isinstance(r, dict)]
        total_operations = concurrent_users * operations_per_user
        successful_operations = sum(r["operations"] - r["errors"] for r in successful_results)
        total_errors = sum(r["errors"] for r in successful_results)
        
        avg_response_time = statistics.mean([r["avg_time"] for r in successful_results]) if successful_results else 0
        throughput = successful_operations / total_time if total_time > 0 else 0
        
        return {
            "test_name": self.name,
            "concurrent_users": concurrent_users,
            "operations_per_user": operations_per_user,
            "total_operations": total_operations,
            "successful_operations": successful_operations,
            "total_errors": total_errors,
            "error_rate": total_errors / total_operations if total_operations > 0 else 0,
            "total_time": total_time,
            "avg_response_time": avg_response_time,
            "throughput": throughput,
            "user_results": successful_results
        }

def benchmark_decorator(name: str):
    """Décorateur pour mesurer automatiquement les performances"""
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                benchmark = AsyncBenchmark(name)
                result = await benchmark.measure(func, *args, **kwargs)
                stats = benchmark.get_stats()
                logger.info(f"Benchmark {name}: {stats['duration']['avg']:.4f}s avg")
                return result
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                benchmark = PerformanceBenchmark(name)
                benchmark.start()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    measurement = benchmark.stop()
                    logger.info(f"Benchmark {name}: {measurement['duration']:.4f}s")
            return sync_wrapper
    return decorator

class PerformanceReporter:
    """Générateur de rapports de performance"""
    
    @staticmethod
    def generate_report(benchmarks: Dict[str, Dict[str, Any]]) -> str:
        """Génère un rapport de performance"""
        report = []
        report.append("=" * 60)
        report.append("📊 RAPPORT DE PERFORMANCE ASKRAG")
        report.append("=" * 60)
        report.append(f"Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        for name, stats in benchmarks.items():
            report.append(f"🧪 {name}")
            report.append("-" * 40)
            
            if "duration" in stats:
                duration = stats["duration"]
                report.append(f"⏱️  Temps d'exécution:")
                report.append(f"   • Moyenne: {duration['avg']*1000:.2f}ms")
                report.append(f"   • Médiane: {duration['median']*1000:.2f}ms")
                report.append(f"   • Min/Max: {duration['min']*1000:.2f}ms / {duration['max']*1000:.2f}ms")
                if duration['std_dev'] > 0:
                    report.append(f"   • Écart-type: {duration['std_dev']*1000:.2f}ms")
            
            if "throughput" in stats:
                throughput = stats["throughput"]
                report.append(f"🚀 Débit: {throughput['ops_per_second']:.1f} ops/sec")
            
            if "memory" in stats:
                memory = stats["memory"]
                report.append(f"💾 Mémoire:")
                report.append(f"   • Moyenne: {memory['avg']:.1f}MB")
                report.append(f"   • Min/Max: {memory['min']:.1f}MB / {memory['max']:.1f}MB")
            
            # Métriques spécifiques aux tests de charge
            if "concurrent_users" in stats:
                report.append(f"👥 Utilisateurs concurrents: {stats['concurrent_users']}")
                report.append(f"📈 Taux d'erreur: {stats['error_rate']*100:.1f}%")
                report.append(f"⚡ Débit: {stats['throughput']:.1f} ops/sec")
            
            report.append("")
        
        return "\n".join(report)
    
    @staticmethod
    def save_report(report: str, filename: str = None):
        """Sauvegarde le rapport dans un fichier"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_report_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"📄 Rapport sauvegardé: {filename}")

# Fonctions utilitaires pour les mesures courantes

async def measure_cache_performance(cache, num_operations: int = 1000):
    """Mesure les performances d'un cache"""
    benchmark = AsyncBenchmark("Cache Performance")
    
    # Test écriture
    write_results = await benchmark.measure_multiple(
        lambda: cache.set(f"test_key_{time.time()}", {"test": "data"}),
        num_operations
    )
    
    # Test lecture
    test_key = f"read_test_{time.time()}"
    await cache.set(test_key, {"test": "data"})
    
    read_results = await benchmark.measure_multiple(
        lambda: cache.get(test_key),
        num_operations
    )
    
    return benchmark.get_stats()

async def measure_embedding_performance(service, texts: List[str]):
    """Mesure les performances d'un service d'embedding"""
    benchmark = AsyncBenchmark("Embedding Performance")
    
    # Test génération simple
    single_results = await benchmark.measure_multiple(
        lambda: service.generate_single_embedding(texts[0]),
        len(texts)
    )
    
    # Test batch
    await benchmark.measure(
        service.generate_embeddings_batch,
        texts
    )
    
    return benchmark.get_stats()

# Seuils de performance recommandés pour AskRAG
PERFORMANCE_THRESHOLDS = {
    "cache_read_ms": 5.0,       # Cache read < 5ms
    "cache_write_ms": 10.0,     # Cache write < 10ms
    "query_build_ms": 1.0,      # Query building < 1ms
    "pagination_ms": 10.0,      # Pagination < 10ms
    "embedding_single_ms": 100.0,  # Single embedding < 100ms
    "rag_pipeline_ms": 2000.0,  # Full RAG pipeline < 2s
    "cache_hit_ratio": 0.8,     # Cache hit ratio > 80%
    "throughput_ops_sec": 100.0  # Minimum throughput 100 ops/sec
}

def check_performance_thresholds(stats: Dict[str, Any]) -> Dict[str, bool]:
    """Vérifie si les performances respectent les seuils"""
    results = {}
    
    if "duration" in stats and "avg" in stats["duration"]:
        avg_ms = stats["duration"]["avg"] * 1000
        
        # Déterminer le seuil approprié basé sur le nom du test
        test_name = stats.get("name", "").lower()
        if "cache" in test_name and "read" in test_name:
            threshold = PERFORMANCE_THRESHOLDS["cache_read_ms"]
        elif "cache" in test_name and "write" in test_name:
            threshold = PERFORMANCE_THRESHOLDS["cache_write_ms"]
        elif "query" in test_name:
            threshold = PERFORMANCE_THRESHOLDS["query_build_ms"]
        elif "pagination" in test_name:
            threshold = PERFORMANCE_THRESHOLDS["pagination_ms"]
        elif "embedding" in test_name:
            threshold = PERFORMANCE_THRESHOLDS["embedding_single_ms"]
        else:
            threshold = PERFORMANCE_THRESHOLDS["rag_pipeline_ms"]
        
        results["avg_time_ok"] = avg_ms <= threshold
    
    if "throughput" in stats and "ops_per_second" in stats["throughput"]:
        results["throughput_ok"] = stats["throughput"]["ops_per_second"] >= PERFORMANCE_THRESHOLDS["throughput_ops_sec"]
    
    return results

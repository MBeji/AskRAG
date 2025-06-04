"""
Module de gestion des métriques pour RAG
Étape 16.3.5 - Implémenter la gestion des métriques
"""

import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
import logging
import threading
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types de métriques supportées"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class MetricValue:
    """Valeur d'une métrique avec timestamp"""
    value: Union[int, float]
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class MetricSummary:
    """Résumé statistique d'une métrique"""
    name: str
    type: MetricType
    current_value: Union[int, float]
    count: int
    sum_value: float
    min_value: float
    max_value: float
    average: float
    last_updated: datetime
    labels: Dict[str, str] = field(default_factory=dict)


class BaseMetric(ABC):
    """Classe de base pour les métriques"""
    
    def __init__(self, name: str, description: str = "", labels: Dict[str, str] = None):
        self.name = name
        self.description = description
        self.labels = labels or {}
        self.created_at = datetime.now()
    
    @abstractmethod
    def record(self, value: Union[int, float], labels: Dict[str, str] = None):
        """Enregistre une valeur"""
        pass
    
    @abstractmethod
    def get_summary(self) -> MetricSummary:
        """Retourne un résumé de la métrique"""
        pass
    
    @abstractmethod
    def reset(self):
        """Remet à zéro la métrique"""
        pass


class Counter(BaseMetric):
    """Métrique de comptage (toujours croissante)"""
    
    def __init__(self, name: str, description: str = "", labels: Dict[str, str] = None):
        super().__init__(name, description, labels)
        self._value = 0
        self._lock = threading.Lock()
    
    def record(self, value: Union[int, float] = 1, labels: Dict[str, str] = None):
        """Incrémente le compteur"""
        if value < 0:
            raise ValueError("Counter ne peut pas décroître")
        
        with self._lock:
            self._value += value
    
    def increment(self, amount: Union[int, float] = 1):
        """Incrémente le compteur"""
        self.record(amount)
    
    def get_value(self) -> Union[int, float]:
        """Retourne la valeur actuelle"""
        return self._value
    
    def get_summary(self) -> MetricSummary:
        return MetricSummary(
            name=self.name,
            type=MetricType.COUNTER,
            current_value=self._value,
            count=1,
            sum_value=self._value,
            min_value=0,
            max_value=self._value,
            average=self._value,
            last_updated=datetime.now(),
            labels=self.labels
        )
    
    def reset(self):
        """Remet le compteur à zéro"""
        with self._lock:
            self._value = 0


class Gauge(BaseMetric):
    """Métrique de jauge (peut monter et descendre)"""
    
    def __init__(self, name: str, description: str = "", labels: Dict[str, str] = None):
        super().__init__(name, description, labels)
        self._value = 0
        self._lock = threading.Lock()
    
    def record(self, value: Union[int, float], labels: Dict[str, str] = None):
        """Définit la valeur de la jauge"""
        with self._lock:
            self._value = value
    
    def set(self, value: Union[int, float]):
        """Définit la valeur"""
        self.record(value)
    
    def increment(self, amount: Union[int, float] = 1):
        """Incrémente la valeur"""
        with self._lock:
            self._value += amount
    
    def decrement(self, amount: Union[int, float] = 1):
        """Décrémente la valeur"""
        with self._lock:
            self._value -= amount
    
    def get_value(self) -> Union[int, float]:
        """Retourne la valeur actuelle"""
        return self._value
    
    def get_summary(self) -> MetricSummary:
        return MetricSummary(
            name=self.name,
            type=MetricType.GAUGE,
            current_value=self._value,
            count=1,
            sum_value=self._value,
            min_value=self._value,
            max_value=self._value,
            average=self._value,
            last_updated=datetime.now(),
            labels=self.labels
        )
    
    def reset(self):
        """Remet la jauge à zéro"""
        with self._lock:
            self._value = 0


class Histogram(BaseMetric):
    """Métrique d'histogramme pour les distributions"""
    
    def __init__(self, name: str, description: str = "", labels: Dict[str, str] = None, max_size: int = 1000):
        super().__init__(name, description, labels)
        self._values = deque(maxlen=max_size)
        self._lock = threading.Lock()
    
    def record(self, value: Union[int, float], labels: Dict[str, str] = None):
        """Enregistre une valeur dans l'histogramme"""
        with self._lock:
            self._values.append(MetricValue(
                value=value,
                timestamp=datetime.now(),
                labels=labels or {}
            ))
    
    def observe(self, value: Union[int, float]):
        """Enregistre une observation"""
        self.record(value)
    
    def get_percentile(self, percentile: float) -> float:
        """Calcule un percentile"""
        if not self._values:
            return 0.0
        
        values = sorted([v.value for v in self._values])
        k = (len(values) - 1) * percentile / 100
        f = int(k)
        c = k - f
        
        if f == len(values) - 1:
            return values[f]
        
        return values[f] * (1 - c) + values[f + 1] * c
    
    def get_summary(self) -> MetricSummary:
        if not self._values:
            return MetricSummary(
                name=self.name,
                type=MetricType.HISTOGRAM,
                current_value=0,
                count=0,
                sum_value=0,
                min_value=0,
                max_value=0,
                average=0,
                last_updated=datetime.now(),
                labels=self.labels
            )
        
        values = [v.value for v in self._values]
        return MetricSummary(
            name=self.name,
            type=MetricType.HISTOGRAM,
            current_value=values[-1],
            count=len(values),
            sum_value=sum(values),
            min_value=min(values),
            max_value=max(values),
            average=sum(values) / len(values),
            last_updated=self._values[-1].timestamp,
            labels=self.labels
        )
    
    def reset(self):
        """Vide l'histogramme"""
        with self._lock:
            self._values.clear()


class Timer(Histogram):
    """Métrique de temps (extension d'histogramme)"""
    
    def __init__(self, name: str, description: str = "", labels: Dict[str, str] = None, max_size: int = 1000):
        super().__init__(name, description, labels, max_size)
    
    def time_function(self, func):
        """Décorateur pour mesurer le temps d'exécution"""
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                self.observe(duration)
        
        return wrapper
    
    def get_summary(self) -> MetricSummary:
        summary = super().get_summary()
        summary.type = MetricType.TIMER
        return summary


class RAGMetrics:
    """Métriques spécifiques pour le système RAG"""
    
    def __init__(self):
        # Métriques de performance
        self.query_duration = Timer("rag_query_duration", "Durée des requêtes RAG")
        self.embedding_duration = Timer("embedding_duration", "Durée de génération d'embeddings")
        self.llm_call_duration = Timer("llm_call_duration", "Durée des appels LLM")
        self.search_duration = Timer("search_duration", "Durée des recherches sémantiques")
        
        # Métriques de volume
        self.total_queries = Counter("total_queries", "Nombre total de requêtes")
        self.document_uploads = Counter("document_uploads", "Nombre de documents uploadés")
        self.embedding_generations = Counter("embedding_generations", "Nombre d'embeddings générés")
        self.llm_calls = Counter("llm_calls", "Nombre d'appels LLM")
        
        # Métriques de qualité
        self.search_results_count = Histogram("search_results_count", "Nombre de résultats de recherche")
        self.response_confidence = Histogram("response_confidence", "Confiance des réponses")
        self.chunk_relevance_scores = Histogram("chunk_relevance_scores", "Scores de pertinence des chunks")
        
        # Métriques de cache
        self.cache_hits = Counter("cache_hits", "Hits de cache")
        self.cache_misses = Counter("cache_misses", "Misses de cache")
        
        # Métriques d'erreur
        self.query_errors = Counter("query_errors", "Erreurs de requêtes")
        self.upload_errors = Counter("upload_errors", "Erreurs d'upload")
        self.llm_errors = Counter("llm_errors", "Erreurs LLM")
        
        # Métriques système
        self.active_sessions = Gauge("active_sessions", "Sessions actives")
        self.documents_count = Gauge("documents_count", "Nombre de documents")
        self.vectors_count = Gauge("vectors_count", "Nombre de vecteurs")
    
    def record_query(self, duration: float, results_count: int, confidence: float = None):
        """Enregistre une requête RAG"""
        self.query_duration.observe(duration)
        self.total_queries.increment()
        self.search_results_count.observe(results_count)
        
        if confidence is not None:
            self.response_confidence.observe(confidence)
    
    def record_document_upload(self, success: bool, processing_time: float, chunks_count: int):
        """Enregistre un upload de document"""
        if success:
            self.document_uploads.increment()
            self.embedding_duration.observe(processing_time)
            self.documents_count.increment()
        else:
            self.upload_errors.increment()
    
    def record_llm_call(self, duration: float, success: bool):
        """Enregistre un appel LLM"""
        self.llm_call_duration.observe(duration)
        
        if success:
            self.llm_calls.increment()
        else:
            self.llm_errors.increment()
    
    def record_search(self, duration: float, results_count: int, scores: List[float]):
        """Enregistre une recherche sémantique"""
        self.search_duration.observe(duration)
        self.search_results_count.observe(results_count)
        
        for score in scores:
            self.chunk_relevance_scores.observe(score)
    
    def record_cache_operation(self, hit: bool):
        """Enregistre une opération de cache"""
        if hit:
            self.cache_hits.increment()
        else:
            self.cache_misses.increment()
    
    def get_cache_hit_rate(self) -> float:
        """Calcule le taux de hit du cache"""
        hits = self.cache_hits.get_value()
        misses = self.cache_misses.get_value()
        total = hits + misses
        
        if total == 0:
            return 0.0
        
        return hits / total
    
    def get_all_metrics(self) -> Dict[str, MetricSummary]:
        """Retourne toutes les métriques"""
        metrics = {}
        
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if isinstance(attr, BaseMetric):
                metrics[attr.name] = attr.get_summary()
        
        return metrics


class MetricsCollector:
    """Collecteur principal de métriques"""
    
    def __init__(self):
        self.rag_metrics = RAGMetrics()
        self.custom_metrics: Dict[str, BaseMetric] = {}
        self.collection_started = datetime.now()
    
    def create_counter(self, name: str, description: str = "", labels: Dict[str, str] = None) -> Counter:
        """Crée un nouveau compteur"""
        counter = Counter(name, description, labels)
        self.custom_metrics[name] = counter
        return counter
    
    def create_gauge(self, name: str, description: str = "", labels: Dict[str, str] = None) -> Gauge:
        """Crée une nouvelle jauge"""
        gauge = Gauge(name, description, labels)
        self.custom_metrics[name] = gauge
        return gauge
    
    def create_histogram(self, name: str, description: str = "", labels: Dict[str, str] = None, max_size: int = 1000) -> Histogram:
        """Crée un nouvel histogramme"""
        histogram = Histogram(name, description, labels, max_size)
        self.custom_metrics[name] = histogram
        return histogram
    
    def create_timer(self, name: str, description: str = "", labels: Dict[str, str] = None, max_size: int = 1000) -> Timer:
        """Crée un nouveau timer"""
        timer = Timer(name, description, labels, max_size)
        self.custom_metrics[name] = timer
        return timer
    
    def get_metric(self, name: str) -> Optional[BaseMetric]:
        """Récupère une métrique par nom"""
        if hasattr(self.rag_metrics, name):
            return getattr(self.rag_metrics, name)
        
        return self.custom_metrics.get(name)
    
    def get_all_metrics(self) -> Dict[str, MetricSummary]:
        """Retourne toutes les métriques"""
        all_metrics = self.rag_metrics.get_all_metrics()
        
        for name, metric in self.custom_metrics.items():
            all_metrics[name] = metric.get_summary()
        
        return all_metrics
    
    def get_system_overview(self) -> Dict[str, Any]:
        """Retourne un aperçu du système"""
        rag_metrics = self.rag_metrics
        
        return {
            "collection_started": self.collection_started.isoformat(),
            "uptime_minutes": (datetime.now() - self.collection_started).total_seconds() / 60,
            "overview": {
                "total_queries": rag_metrics.total_queries.get_value(),
                "total_documents": rag_metrics.document_uploads.get_value(),
                "active_sessions": rag_metrics.active_sessions.get_value(),
                "cache_hit_rate": rag_metrics.get_cache_hit_rate(),
                "average_query_time": rag_metrics.query_duration.get_summary().average,
                "total_errors": (
                    rag_metrics.query_errors.get_value() +
                    rag_metrics.upload_errors.get_value() +
                    rag_metrics.llm_errors.get_value()
                )
            },
            "performance": {
                "avg_query_duration": rag_metrics.query_duration.get_summary().average,
                "avg_embedding_duration": rag_metrics.embedding_duration.get_summary().average,
                "avg_llm_call_duration": rag_metrics.llm_call_duration.get_summary().average,
                "avg_search_duration": rag_metrics.search_duration.get_summary().average
            },
            "quality": {
                "avg_confidence": rag_metrics.response_confidence.get_summary().average,
                "avg_results_count": rag_metrics.search_results_count.get_summary().average,
                "avg_relevance_score": rag_metrics.chunk_relevance_scores.get_summary().average
            }
        }
    
    def reset_all_metrics(self):
        """Remet à zéro toutes les métriques"""
        for attr_name in dir(self.rag_metrics):
            attr = getattr(self.rag_metrics, attr_name)
            if isinstance(attr, BaseMetric):
                attr.reset()
        
        for metric in self.custom_metrics.values():
            metric.reset()
        
        self.collection_started = datetime.now()
    
    def export_prometheus_format(self) -> str:
        """Exporte les métriques au format Prometheus"""
        lines = []
        all_metrics = self.get_all_metrics()
        
        for name, summary in all_metrics.items():
            # Type de métrique
            metric_type = summary.type.value
            lines.append(f"# TYPE {name} {metric_type}")
            
            # Description
            if hasattr(summary, 'description') and summary.description:
                lines.append(f"# HELP {name} {summary.description}")
            
            # Valeur
            if summary.type == MetricType.HISTOGRAM:
                lines.append(f"{name}_count {summary.count}")
                lines.append(f"{name}_sum {summary.sum_value}")
                lines.append(f"{name}_min {summary.min_value}")
                lines.append(f"{name}_max {summary.max_value}")
                lines.append(f"{name}_avg {summary.average}")
            else:
                lines.append(f"{name} {summary.current_value}")
            
            lines.append("")  # Ligne vide entre les métriques
        
        return "\n".join(lines)


# Instance globale du collecteur de métriques
metrics_collector = MetricsCollector()

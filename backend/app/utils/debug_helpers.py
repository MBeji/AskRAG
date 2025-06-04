"""
Module de helpers de debug pour RAG
Étape 16.3.4 - Créer les helpers de debug
"""

import json
import time
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from functools import wraps
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DebugTimer:
    """Timer pour mesurer les performances"""
    
    def __init__(self, name: str):
        self.name = name
        self.start_time = None
        self.end_time = None
        self.duration = None
    
    def start(self):
        """Démarre le timer"""
        self.start_time = time.time()
        return self
    
    def stop(self):
        """Arrête le timer"""
        self.end_time = time.time()
        if self.start_time:
            self.duration = self.end_time - self.start_time
        return self.duration
    
    def __enter__(self):
        return self.start()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = self.stop()
        logger.debug(f"⏱️  {self.name}: {duration:.3f}s")


class RAGDebugger:
    """Debugger spécialisé pour le pipeline RAG"""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.debug_data = {}
        self.timers = {}
        self.step_counter = 0
    
    def log_step(self, step_name: str, data: Any = None, level: str = "debug"):
        """Log une étape du pipeline avec des données"""
        if not self.enabled:
            return
        
        self.step_counter += 1
        timestamp = datetime.now().isoformat()
        
        step_info = {
            "step": self.step_counter,
            "name": step_name,
            "timestamp": timestamp,
            "data": self._serialize_data(data) if data else None
        }
        
        self.debug_data[f"step_{self.step_counter}"] = step_info
        
        # Log selon le niveau
        log_msg = f"📋 Step {self.step_counter}: {step_name}"
        if data:
            log_msg += f" | Data: {self._format_data_summary(data)}"
        
        getattr(logger, level)(log_msg)
    
    def log_document_processing(self, document_id: str, chunks_count: int, processing_time: float):
        """Log le traitement d'un document"""
        self.log_step("document_processing", {
            "document_id": document_id,
            "chunks_count": chunks_count,
            "processing_time": processing_time
        })
    
    def log_search_results(self, query: str, results_count: int, search_time: float):
        """Log les résultats de recherche"""
        self.log_step("search_results", {
            "query": query,
            "results_count": results_count,
            "search_time": search_time
        })
    
    def log_llm_call(self, prompt_length: int, response_length: int, call_time: float):
        """Log un appel LLM"""
        self.log_step("llm_call", {
            "prompt_length": prompt_length,
            "response_length": response_length,
            "call_time": call_time
        })
    
    def log_embedding_generation(self, text_count: int, embedding_dim: int, generation_time: float):
        """Log la génération d'embeddings"""
        self.log_step("embedding_generation", {
            "text_count": text_count,
            "embedding_dim": embedding_dim,
            "generation_time": generation_time
        })
    
    def log_cache_operation(self, operation: str, key: str, hit: bool, operation_time: float):
        """Log une opération de cache"""
        self.log_step("cache_operation", {
            "operation": operation,
            "key": key,
            "hit": hit,
            "operation_time": operation_time
        })
    
    def log_error(self, error: Exception, context: Dict = None):
        """Log une erreur avec contexte"""
        error_info = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "context": context or {}
        }
        
        self.log_step("error", error_info, level="error")
    
    def start_timer(self, name: str) -> DebugTimer:
        """Démarre un timer nommé"""
        timer = DebugTimer(name)
        self.timers[name] = timer
        return timer.start()
    
    def stop_timer(self, name: str) -> Optional[float]:
        """Arrête un timer nommé"""
        if name in self.timers:
            return self.timers[name].stop()
        return None
    
    def get_debug_summary(self) -> Dict[str, Any]:
        """Génère un résumé de debug"""
        summary = {
            "enabled": self.enabled,
            "total_steps": self.step_counter,
            "steps": list(self.debug_data.values()),
            "timers": {
                name: {
                    "duration": timer.duration,
                    "start_time": timer.start_time,
                    "end_time": timer.end_time
                }
                for name, timer in self.timers.items()
                if timer.duration is not None
            }
        }
        
        return summary
    
    def clear(self):
        """Vide les données de debug"""
        self.debug_data.clear()
        self.timers.clear()
        self.step_counter = 0
    
    def _serialize_data(self, data: Any) -> Any:
        """Sérialise les données pour le debug"""
        try:
            # Essayer la sérialisation JSON
            json.dumps(data)
            return data
        except (TypeError, ValueError):
            # Fallback vers une représentation string
            if hasattr(data, '__dict__'):
                return {k: str(v) for k, v in data.__dict__.items()}
            return str(data)
    
    def _format_data_summary(self, data: Any) -> str:
        """Formate un résumé des données"""
        if isinstance(data, dict):
            return f"dict({len(data)} keys)"
        elif isinstance(data, (list, tuple)):
            return f"{type(data).__name__}({len(data)} items)"
        elif isinstance(data, str):
            return f"str({len(data)} chars)"
        else:
            return f"{type(data).__name__}"


def debug_timing(name: str = None):
    """Décorateur pour mesurer le temps d'exécution"""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            timer_name = name or f"{func.__module__}.{func.__name__}"
            
            with DebugTimer(timer_name) as timer:
                try:
                    result = await func(*args, **kwargs)
                    logger.debug(f"✅ {timer_name} completed in {timer.duration:.3f}s")
                    return result
                except Exception as e:
                    logger.error(f"❌ {timer_name} failed after {timer.duration:.3f}s: {e}")
                    raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            timer_name = name or f"{func.__module__}.{func.__name__}"
            
            with DebugTimer(timer_name) as timer:
                try:
                    result = func(*args, **kwargs)
                    logger.debug(f"✅ {timer_name} completed in {timer.duration:.3f}s")
                    return result
                except Exception as e:
                    logger.error(f"❌ {timer_name} failed after {timer.duration:.3f}s: {e}")
                    raise
        
        # Détecter si la fonction est async
        if hasattr(func, '__code__') and func.__code__.co_flags & 0x80:
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def debug_log_inputs_outputs(log_inputs: bool = True, log_outputs: bool = True):
    """Décorateur pour logger les entrées et sorties de fonction"""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            func_name = f"{func.__module__}.{func.__name__}"
            
            if log_inputs:
                # Logger les inputs de manière sécurisée
                safe_args = [str(arg)[:100] for arg in args]
                safe_kwargs = {k: str(v)[:100] for k, v in kwargs.items()}
                logger.debug(f"🔵 {func_name} called with args={safe_args}, kwargs={safe_kwargs}")
            
            try:
                result = await func(*args, **kwargs)
                
                if log_outputs:
                    if isinstance(result, (dict, list)):
                        logger.debug(f"🟢 {func_name} returned {type(result).__name__} with {len(result)} items")
                    else:
                        logger.debug(f"🟢 {func_name} returned {type(result).__name__}")
                
                return result
            except Exception as e:
                logger.error(f"🔴 {func_name} raised {type(e).__name__}: {e}")
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            func_name = f"{func.__module__}.{func.__name__}"
            
            if log_inputs:
                safe_args = [str(arg)[:100] for arg in args]
                safe_kwargs = {k: str(v)[:100] for k, v in kwargs.items()}
                logger.debug(f"🔵 {func_name} called with args={safe_args}, kwargs={safe_kwargs}")
            
            try:
                result = func(*args, **kwargs)
                
                if log_outputs:
                    if isinstance(result, (dict, list)):
                        logger.debug(f"🟢 {func_name} returned {type(result).__name__} with {len(result)} items")
                    else:
                        logger.debug(f"🟢 {func_name} returned {type(result).__name__}")
                
                return result
            except Exception as e:
                logger.error(f"🔴 {func_name} raised {type(e).__name__}: {e}")
                raise
        
        if hasattr(func, '__code__') and func.__code__.co_flags & 0x80:
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class PerformanceMonitor:
    """Moniteur de performances pour identifier les goulots d'étranglement"""
    
    def __init__(self):
        self.metrics = {}
        self.call_counts = {}
        self.total_times = {}
        self.max_times = {}
        self.min_times = {}
    
    def record_call(self, function_name: str, duration: float):
        """Enregistre l'appel d'une fonction"""
        self.call_counts[function_name] = self.call_counts.get(function_name, 0) + 1
        self.total_times[function_name] = self.total_times.get(function_name, 0) + duration
        
        if function_name not in self.max_times or duration > self.max_times[function_name]:
            self.max_times[function_name] = duration
        
        if function_name not in self.min_times or duration < self.min_times[function_name]:
            self.min_times[function_name] = duration
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Génère un rapport de performances"""
        report = {}
        
        for func_name in self.call_counts:
            calls = self.call_counts[func_name]
            total_time = self.total_times[func_name]
            avg_time = total_time / calls
            
            report[func_name] = {
                "call_count": calls,
                "total_time": total_time,
                "average_time": avg_time,
                "max_time": self.max_times[func_name],
                "min_time": self.min_times[func_name]
            }
        
        # Trier par temps total décroissant
        sorted_report = dict(sorted(
            report.items(),
            key=lambda x: x[1]["total_time"],
            reverse=True
        ))
        
        return {
            "performance_metrics": sorted_report,
            "summary": {
                "total_functions": len(report),
                "total_calls": sum(self.call_counts.values()),
                "total_time": sum(self.total_times.values())
            }
        }
    
    def reset(self):
        """Remet à zéro les métriques"""
        self.metrics.clear()
        self.call_counts.clear()
        self.total_times.clear()
        self.max_times.clear()
        self.min_times.clear()


@contextmanager
def debug_context(debugger: RAGDebugger, context_name: str):
    """Context manager pour le debug"""
    debugger.log_step(f"start_{context_name}")
    timer = debugger.start_timer(context_name)
    
    try:
        yield debugger
    except Exception as e:
        debugger.log_error(e, {"context": context_name})
        raise
    finally:
        duration = debugger.stop_timer(context_name)
        debugger.log_step(f"end_{context_name}", {"duration": duration})


def create_debug_middleware():
    """Crée un middleware de debug pour FastAPI"""
    async def debug_middleware(request, call_next):
        start_time = time.time()
        
        # Log de la requête
        logger.debug(f"🌐 {request.method} {request.url}")
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            logger.debug(f"✅ {request.method} {request.url} - {response.status_code} - {duration:.3f}s")
            
            # Ajouter les headers de debug
            response.headers["X-Debug-Duration"] = str(duration)
            response.headers["X-Debug-Timestamp"] = datetime.now().isoformat()
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ {request.method} {request.url} - Error: {e} - {duration:.3f}s")
            raise
    
    return debug_middleware


# Instance globale pour le debug RAG
rag_debugger = RAGDebugger()
performance_monitor = PerformanceMonitor()

#!/usr/bin/env python3
"""
AskRAG Performance Monitoring Dashboard
Real-time performance metrics and monitoring for production systems
"""

import asyncio
import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

class PerformanceMonitor:
    """Production performance monitoring system"""
    
    def __init__(self):
        self.metrics = {
            "requests": [],
            "cache_hits": 0,
            "cache_misses": 0,
            "response_times": [],
            "errors": [],
            "concurrent_users": 0,
            "uptime_start": datetime.now()
        }
        self.alert_thresholds = {
            "response_time_ms": 100,
            "error_rate_percent": 5,
            "cache_hit_rate_percent": 80,
            "memory_usage_percent": 80
        }
    
    def record_request(self, response_time_ms: float, cache_hit: bool = False, error: bool = False):
        """Record a request metric"""
        timestamp = datetime.now()
        
        self.metrics["requests"].append({
            "timestamp": timestamp,
            "response_time": response_time_ms,
            "cache_hit": cache_hit,
            "error": error
        })
        
        if cache_hit:
            self.metrics["cache_hits"] += 1
        else:
            self.metrics["cache_misses"] += 1
            
        self.metrics["response_times"].append(response_time_ms)
        
        if error:
            self.metrics["errors"].append(timestamp)
            
        # Keep only last hour of data
        cutoff_time = timestamp - timedelta(hours=1)
        self.metrics["requests"] = [
            r for r in self.metrics["requests"] 
            if r["timestamp"] > cutoff_time
        ]
        self.metrics["response_times"] = self.metrics["response_times"][-1000:]
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        now = datetime.now()
        uptime = now - self.metrics["uptime_start"]
        
        # Calculate metrics for last hour
        recent_requests = [
            r for r in self.metrics["requests"]
            if r["timestamp"] > now - timedelta(hours=1)
        ]
        
        if not recent_requests:
            return self._empty_metrics(uptime)
        
        # Response time metrics
        response_times = [r["response_time"] for r in recent_requests]
        avg_response_time = statistics.mean(response_times)
        p95_response_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max(response_times)
        
        # Cache metrics
        total_cache_requests = self.metrics["cache_hits"] + self.metrics["cache_misses"]
        cache_hit_rate = (self.metrics["cache_hits"] / total_cache_requests * 100) if total_cache_requests > 0 else 0
        
        # Error rate
        error_count = len([r for r in recent_requests if r["error"]])
        error_rate = (error_count / len(recent_requests) * 100) if recent_requests else 0
        
        # Throughput (requests per second)
        throughput = len(recent_requests) / 3600  # requests per second over last hour
        
        return {
            "uptime": str(uptime),
            "requests_last_hour": len(recent_requests),
            "throughput_per_sec": throughput,
            "avg_response_time_ms": round(avg_response_time, 2),
            "p95_response_time_ms": round(p95_response_time, 2),
            "cache_hit_rate_percent": round(cache_hit_rate, 1),
            "error_rate_percent": round(error_rate, 2),
            "concurrent_users": self.metrics["concurrent_users"],
            "status": self._get_system_status()
        }
    
    def _empty_metrics(self, uptime):
        """Return empty metrics structure"""
        return {
            "uptime": str(uptime),
            "requests_last_hour": 0,
            "throughput_per_sec": 0,
            "avg_response_time_ms": 0,
            "p95_response_time_ms": 0,
            "cache_hit_rate_percent": 0,
            "error_rate_percent": 0,
            "concurrent_users": 0,
            "status": "HEALTHY"
        }
    
    def _get_system_status(self) -> str:
        """Determine system health status"""
        metrics = self.get_current_metrics() if hasattr(self, '_temp_metrics') else self._calculate_temp_metrics()
        
        # Check against thresholds
        if metrics["error_rate_percent"] > self.alert_thresholds["error_rate_percent"]:
            return "CRITICAL"
        elif metrics["avg_response_time_ms"] > self.alert_thresholds["response_time_ms"]:
            return "WARNING"
        elif metrics["cache_hit_rate_percent"] < self.alert_thresholds["cache_hit_rate_percent"]:
            return "WARNING"
        else:
            return "HEALTHY"
    
    def _calculate_temp_metrics(self):
        """Calculate temporary metrics for status check"""
        now = datetime.now()
        recent_requests = [
            r for r in self.metrics["requests"]
            if r["timestamp"] > now - timedelta(hours=1)
        ]
        
        if not recent_requests:
            return {"error_rate_percent": 0, "avg_response_time_ms": 0, "cache_hit_rate_percent": 100}
        
        response_times = [r["response_time"] for r in recent_requests]
        avg_response_time = statistics.mean(response_times)
        
        error_count = len([r for r in recent_requests if r["error"]])
        error_rate = (error_count / len(recent_requests) * 100) if recent_requests else 0
        
        total_cache_requests = self.metrics["cache_hits"] + self.metrics["cache_misses"]
        cache_hit_rate = (self.metrics["cache_hits"] / total_cache_requests * 100) if total_cache_requests > 0 else 100
        
        return {
            "error_rate_percent": error_rate,
            "avg_response_time_ms": avg_response_time,
            "cache_hit_rate_percent": cache_hit_rate
        }
    
    def print_dashboard(self):
        """Print performance dashboard to console"""
        metrics = self.get_current_metrics()
        
        print("\n" + "="*60)
        print("🚀 AskRAG PERFORMANCE DASHBOARD")
        print("="*60)
        print(f"📊 System Status: {metrics['status']}")
        print(f"⏱️  Uptime: {metrics['uptime']}")
        print(f"📈 Requests (last hour): {metrics['requests_last_hour']}")
        print(f"🔥 Throughput: {metrics['throughput_per_sec']:.2f} req/sec")
        print()
        
        print("⚡ RESPONSE TIME METRICS")
        print("-" * 30)
        print(f"Average: {metrics['avg_response_time_ms']}ms")
        print(f"95th Percentile: {metrics['p95_response_time_ms']}ms")
        print()
        
        print("💾 CACHE PERFORMANCE")
        print("-" * 30)
        print(f"Hit Rate: {metrics['cache_hit_rate_percent']}%")
        print(f"Total Hits: {self.metrics['cache_hits']}")
        print(f"Total Misses: {self.metrics['cache_misses']}")
        print()
        
        print("🚨 ERROR MONITORING")
        print("-" * 30)
        print(f"Error Rate: {metrics['error_rate_percent']}%")
        print(f"Concurrent Users: {metrics['concurrent_users']}")
        print()
        
        # Status indicators
        status_color = {
            "HEALTHY": "🟢",
            "WARNING": "🟡", 
            "CRITICAL": "🔴"
        }
        print(f"{status_color.get(metrics['status'], '⚪')} Overall Status: {metrics['status']}")
        print("="*60)

# Example usage and simulation
async def simulate_production_load():
    """Simulate production load for monitoring demonstration"""
    monitor = PerformanceMonitor()
    
    print("🚀 Starting performance monitoring simulation...")
    print("Simulating production load for 30 seconds...")
    
    # Simulate requests over 30 seconds
    for i in range(100):
        # Simulate various request scenarios
        if i % 10 == 0:
            # Slow request (cache miss)
            monitor.record_request(response_time_ms=50, cache_hit=False)
        elif i % 15 == 0:
            # Error request
            monitor.record_request(response_time_ms=100, cache_hit=False, error=True)
        else:
            # Fast request (cache hit)
            monitor.record_request(response_time_ms=2, cache_hit=True)
        
        # Update concurrent users
        monitor.metrics["concurrent_users"] = min(20, i // 5)
        
        # Print dashboard every 20 requests
        if i % 20 == 0:
            monitor.print_dashboard()
        
        await asyncio.sleep(0.1)  # 100ms between requests
    
    # Final dashboard
    print("\n🏁 FINAL PERFORMANCE REPORT")
    monitor.print_dashboard()
    
    # Export metrics to JSON
    final_metrics = monitor.get_current_metrics()
    with open("performance_metrics.json", "w") as f:
        json.dump(final_metrics, f, indent=2, default=str)
    
    print("\n✅ Performance metrics exported to performance_metrics.json")

if __name__ == "__main__":
    # Run the performance monitoring simulation
    asyncio.run(simulate_production_load())

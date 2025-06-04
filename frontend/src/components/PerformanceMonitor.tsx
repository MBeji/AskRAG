import React, { useState, useEffect } from 'react';
import { ChartBarIcon, XMarkIcon } from '@heroicons/react/24/outline';

interface PerformanceMetrics {
  messageCount: number;
  renderTime: number;
  memoryUsage: number;
  lastUpdate: Date;
}

interface PerformanceMonitorProps {
  messageCount: number;
  isVisible: boolean;
  onToggle: () => void;
}

const PerformanceMonitor: React.FC<PerformanceMonitorProps> = ({
  messageCount,
  isVisible,
  onToggle
}) => {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    messageCount: 0,
    renderTime: 0,
    memoryUsage: 0,
    lastUpdate: new Date()
  });

  useEffect(() => {
    const updateMetrics = () => {
      const startTime = performance.now();
      
      // Simulate render time measurement
      requestAnimationFrame(() => {
        const renderTime = performance.now() - startTime;
        
        // Get memory usage if available
        const memoryUsage = (performance as any).memory 
          ? (performance as any).memory.usedJSHeapSize / 1024 / 1024
          : 0;

        setMetrics({
          messageCount,
          renderTime: Math.round(renderTime * 100) / 100,
          memoryUsage: Math.round(memoryUsage * 100) / 100,
          lastUpdate: new Date()
        });
      });
    };

    updateMetrics();
  }, [messageCount]);

  if (!isVisible) {
    return (
      <button
        onClick={onToggle}
        className="fixed bottom-4 right-4 w-12 h-12 bg-slate-800/90 hover:bg-slate-700/90 border border-slate-600 rounded-full flex items-center justify-center text-slate-400 hover:text-slate-200 transition-all z-50 backdrop-blur-sm"
        title="Show Performance Monitor"
      >
        <ChartBarIcon className="w-5 h-5" />
      </button>
    );
  }

  const getPerformanceColor = (renderTime: number) => {
    if (renderTime < 16) return 'text-emerald-400'; // Good (60fps)
    if (renderTime < 33) return 'text-yellow-400';  // OK (30fps)
    return 'text-red-400'; // Poor
  };

  const getMemoryColor = (memoryUsage: number) => {
    if (memoryUsage < 50) return 'text-emerald-400'; // Good
    if (memoryUsage < 100) return 'text-yellow-400'; // OK
    return 'text-red-400'; // High usage
  };

  return (
    <div className="fixed bottom-4 right-4 w-80 bg-slate-800/95 backdrop-blur-xl border border-slate-700 rounded-lg shadow-xl z-50">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-700">
        <div className="flex items-center gap-2">
          <ChartBarIcon className="w-5 h-5 text-purple-400" />
          <h3 className="text-sm font-medium text-slate-200">Performance Monitor</h3>
        </div>
        <button
          onClick={onToggle}
          className="w-6 h-6 flex items-center justify-center rounded bg-slate-700/50 hover:bg-slate-600/50 transition-colors"
        >
          <XMarkIcon className="w-4 h-4 text-slate-400" />
        </button>
      </div>

      {/* Metrics */}
      <div className="p-4 space-y-4">
        {/* Message Count */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-400">Messages</span>
          <span className="text-sm font-medium text-slate-200">
            {metrics.messageCount}
          </span>
        </div>

        {/* Render Time */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-400">Render Time</span>
          <span className={`text-sm font-medium ${getPerformanceColor(metrics.renderTime)}`}>
            {metrics.renderTime}ms
          </span>
        </div>

        {/* Memory Usage */}
        {metrics.memoryUsage > 0 && (
          <div className="flex items-center justify-between">
            <span className="text-sm text-slate-400">Memory Usage</span>
            <span className={`text-sm font-medium ${getMemoryColor(metrics.memoryUsage)}`}>
              {metrics.memoryUsage}MB
            </span>
          </div>
        )}

        {/* Performance Status */}
        <div className="pt-3 border-t border-slate-700">
          <div className="flex items-center justify-between">
            <span className="text-sm text-slate-400">Status</span>
            <div className="flex items-center gap-2">
              <div 
                className={`w-2 h-2 rounded-full ${
                  metrics.renderTime < 16 ? 'bg-emerald-400' :
                  metrics.renderTime < 33 ? 'bg-yellow-400' : 'bg-red-400'
                }`}
              />
              <span className={`text-xs font-medium ${getPerformanceColor(metrics.renderTime)}`}>
                {metrics.renderTime < 16 ? 'Excellent' :
                 metrics.renderTime < 33 ? 'Good' : 'Needs Optimization'}
              </span>
            </div>
          </div>
        </div>

        {/* Recommendations */}
        {metrics.messageCount > 50 && (
          <div className="p-3 bg-yellow-400/10 border border-yellow-400/20 rounded-lg">
            <p className="text-xs text-yellow-400">
              💡 Large conversation detected. Consider using message virtualization for better performance.
            </p>
          </div>
        )}

        {metrics.renderTime > 33 && (
          <div className="p-3 bg-red-400/10 border border-red-400/20 rounded-lg">
            <p className="text-xs text-red-400">
              ⚠️ Slow rendering detected. Check for performance bottlenecks.
            </p>
          </div>
        )}

        {/* Last Update */}
        <div className="text-xs text-slate-500 text-center pt-2 border-t border-slate-700">
          Updated: {metrics.lastUpdate.toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
};

export default PerformanceMonitor;

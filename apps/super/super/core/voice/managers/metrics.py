"""
MetricsCollector - Observability and metrics collection for SuperVoiceAgent

This module provides Prometheus-compatible metrics collection, structured logging,
and tracing functionality for monitoring voice call performance.
"""

import asyncio
import json
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import logging


class Counter:
    """Simple counter metric"""
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.value = 0
    
    def inc(self, amount: int = 1):
        """Increment counter"""
        self.value += amount
    
    def get(self) -> int:
        """Get current value"""
        return self.value
    
    def reset(self):
        """Reset counter"""
        self.value = 0


class Histogram:
    """Simple histogram metric"""
    def __init__(self, name: str, description: str = "", buckets: List[float] = None):
        self.name = name
        self.description = description
        self.buckets = buckets or [0.1, 0.25, 0.5, 1, 2.5, 5, 10]
        self.samples = deque(maxlen=1000)  # Keep last 1000 samples
        self.bucket_counts = {bucket: 0 for bucket in self.buckets}
        self.sum = 0
        self.count = 0
    
    def observe(self, value: float):
        """Record an observation"""
        self.samples.append(value)
        self.sum += value
        self.count += 1
        
        # Update bucket counts
        for bucket in self.buckets:
            if value <= bucket:
                self.bucket_counts[bucket] += 1
    
    def get_percentile(self, percentile: float) -> float:
        """Get percentile value"""
        if not self.samples:
            return 0.0
        
        sorted_samples = sorted(self.samples)
        index = int(len(sorted_samples) * percentile / 100)
        return sorted_samples[min(index, len(sorted_samples) - 1)]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get histogram statistics"""
        return {
            'count': self.count,
            'sum': self.sum,
            'avg': self.sum / self.count if self.count > 0 else 0,
            'p50': self.get_percentile(50),
            'p95': self.get_percentile(95),
            'p99': self.get_percentile(99),
            'buckets': self.bucket_counts
        }


class Gauge:
    """Simple gauge metric"""
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.value = 0
    
    def set(self, value: float):
        """Set gauge value"""
        self.value = value
    
    def inc(self, amount: float = 1):
        """Increment gauge"""
        self.value += amount
    
    def dec(self, amount: float = 1):
        """Decrement gauge"""
        self.value -= amount
    
    def get(self) -> float:
        """Get current value"""
        return self.value


class TransportEvent:
    pass


class MetricsCollector:
    """Metrics collection and monitoring"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        
        # Metrics storage
        self.counters: Dict[str, Counter] = {}
        self.histograms: Dict[str, Histogram] = {}
        self.gauges: Dict[str, Gauge] = {}
        
        # Call metrics
        self.call_started_counter = self._get_counter("calls_started_total", "Total calls started")
        self.call_ended_counter = self._get_counter("calls_ended_total", "Total calls ended")
        self.call_failed_counter = self._get_counter("calls_failed_total", "Total calls failed")
        
        # Session metrics
        self.active_sessions_gauge = self._get_gauge("active_sessions", "Currently active sessions")
        
        # Transport metrics
        self.transport_events_counter = self._get_counter("transport_events_total", "Total transport events")
        self.transport_errors_counter = self._get_counter("transport_errors_total", "Total transport errors")
        
        # Audio metrics
        self.audio_frames_in_counter = self._get_counter("audio_frames_in_total", "Total inbound audio frames")
        self.audio_frames_out_counter = self._get_counter("audio_frames_out_total", "Total outbound audio frames")
        self.audio_bytes_in_counter = self._get_counter("audio_bytes_in_total", "Total inbound audio bytes")
        self.audio_bytes_out_counter = self._get_counter("audio_bytes_out_total", "Total outbound audio bytes")
        
        # Latency metrics
        self.sdp_latency_histogram = self._get_histogram("sdp_negotiation_duration_seconds", "SDP negotiation latency")
        self.transport_connect_histogram = self._get_histogram("transport_connect_duration_seconds", "Transport connection latency")
        self.agent_response_histogram = self._get_histogram("agent_response_duration_seconds", "Agent response latency")
        
        # Performance metrics
        self.cpu_usage_gauge = self._get_gauge("cpu_usage_percent", "CPU usage percentage")
        self.memory_usage_gauge = self._get_gauge("memory_usage_bytes", "Memory usage in bytes")
        
        # Error tracking
        self.error_rates: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Background tasks
        self._running = False
        self._metrics_task = None
        
        self.logger.info("MetricsCollector initialized")
    
    def _get_counter(self, name: str, description: str = "") -> Counter:
        """Get or create a counter"""
        if name not in self.counters:
            self.counters[name] = Counter(name, description)
        return self.counters[name]
    
    def _get_histogram(self, name: str, description: str = "", buckets: List[float] = None) -> Histogram:
        """Get or create a histogram"""
        if name not in self.histograms:
            self.histograms[name] = Histogram(name, description, buckets)
        return self.histograms[name]
    
    def _get_gauge(self, name: str, description: str = "") -> Gauge:
        """Get or create a gauge"""
        if name not in self.gauges:
            self.gauges[name] = Gauge(name, description)
        return self.gauges[name]
    
    async def start(self) -> bool:
        """Start metrics collection"""
        try:
            self._running = True
            self._metrics_task = asyncio.create_task(self._collect_system_metrics())
            self.logger.info("MetricsCollector started")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start MetricsCollector: {e}")
            return False
    
    async def stop(self) -> bool:
        """Stop metrics collection"""
        try:
            self._running = False
            if self._metrics_task:
                self._metrics_task.cancel()
                try:
                    await self._metrics_task
                except asyncio.CancelledError:
                    pass
            
            self.logger.info("MetricsCollector stopped")
            return True
        except Exception as e:
            self.logger.error(f"Error stopping MetricsCollector: {e}")
            return False
    
    async def record_call_started(self, transport: str, direction: str):
        """Record call started"""
        try:
            self.call_started_counter.inc()
            
            # Transport-specific counter
            transport_counter = self._get_counter(f"calls_started_by_transport_{transport}_total")
            transport_counter.inc()
            
            # Direction-specific counter
            direction_counter = self._get_counter(f"calls_started_by_direction_{direction}_total")
            direction_counter.inc()
            
            self.logger.debug(f"Recorded call started: transport={transport}, direction={direction}")
            
        except Exception as e:
            self.logger.error(f"Error recording call started: {e}")
    
    async def record_call_ended(self, transport: str, reason: str):
        """Record call ended"""
        try:
            self.call_ended_counter.inc()
            
            # Transport-specific counter
            transport_counter = self._get_counter(f"calls_ended_by_transport_{transport}_total")
            transport_counter.inc()
            
            # Reason-specific counter
            reason_counter = self._get_counter(f"calls_ended_by_reason_{reason}_total")
            reason_counter.inc()
            
            self.logger.debug(f"Recorded call ended: transport={transport}, reason={reason}")
            
        except Exception as e:
            self.logger.error(f"Error recording call ended: {e}")
    
    async def record_call_failed(self, transport: str, direction: str, error: str):
        """Record call failure"""
        try:
            self.call_failed_counter.inc()
            
            # Transport-specific counter
            transport_counter = self._get_counter(f"calls_failed_by_transport_{transport}_total")
            transport_counter.inc()
            
            # Track error rate
            now = time.time()
            self.error_rates[transport].append(now)
            
            self.logger.debug(f"Recorded call failed: transport={transport}, direction={direction}, error={error}")
            
        except Exception as e:
            self.logger.error(f"Error recording call failed: {e}")
    
    async def record_transport_event(self, event: TransportEvent):
        """Record transport event"""
        try:
            self.transport_events_counter.inc()
            
            # Event type specific counter
            event_counter = self._get_counter(f"transport_events_by_type_{event.event_type.value}_total")
            event_counter.inc()
            
            # Track errors separately
            if event.event_type.value == "error":
                self.transport_errors_counter.inc()
            
            self.logger.debug(f"Recorded transport event: {event.event_type.value}")
            
        except Exception as e:
            self.logger.error(f"Error recording transport event: {e}")
    
    async def record_audio_frame(self, direction: str, frame_size: int):
        """Record audio frame metrics"""
        try:
            if direction == "inbound":
                self.audio_frames_in_counter.inc()
                self.audio_bytes_in_counter.inc(frame_size)
            else:
                self.audio_frames_out_counter.inc()
                self.audio_bytes_out_counter.inc(frame_size)
                
        except Exception as e:
            self.logger.error(f"Error recording audio frame: {e}")
    
    async def record_latency(self, metric_name: str, duration_seconds: float):
        """Record latency metric"""
        try:
            if metric_name == "sdp_negotiation":
                self.sdp_latency_histogram.observe(duration_seconds)
            elif metric_name == "transport_connect":
                self.transport_connect_histogram.observe(duration_seconds)
            elif metric_name == "agent_response":
                self.agent_response_histogram.observe(duration_seconds)
            else:
                # Generic latency histogram
                histogram = self._get_histogram(f"{metric_name}_duration_seconds")
                histogram.observe(duration_seconds)
                
        except Exception as e:
            self.logger.error(f"Error recording latency: {e}")
    
    async def update_active_sessions(self, count: int):
        """Update active sessions count"""
        try:
            self.active_sessions_gauge.set(count)
        except Exception as e:
            self.logger.error(f"Error updating active sessions: {e}")
    
    async def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot"""
        try:
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'counters': {},
                'histograms': {},
                'gauges': {},
                'error_rates': {}
            }
            
            # Collect counters
            for name, counter in self.counters.items():
                metrics['counters'][name] = counter.get()
            
            # Collect histograms
            for name, histogram in self.histograms.items():
                metrics['histograms'][name] = histogram.get_stats()
            
            # Collect gauges
            for name, gauge in self.gauges.items():
                metrics['gauges'][name] = gauge.get()
            
            # Calculate error rates (errors per minute in last 5 minutes)
            now = time.time()
            five_minutes_ago = now - 300
            
            for transport, errors in self.error_rates.items():
                recent_errors = [t for t in errors if t > five_minutes_ago]
                error_rate = len(recent_errors) / 5.0  # errors per minute
                metrics['error_rates'][f"{transport}_errors_per_minute"] = error_rate
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error getting current metrics: {e}")
            return {}
    
    async def get_prometheus_metrics(self) -> str:
        """Get metrics in Prometheus format"""
        try:
            lines = []
            
            # Add counters
            for name, counter in self.counters.items():
                lines.append(f"# HELP {name} {counter.description}")
                lines.append(f"# TYPE {name} counter")
                lines.append(f"{name} {counter.get()}")
                lines.append("")
            
            # Add gauges
            for name, gauge in self.gauges.items():
                lines.append(f"# HELP {name} {gauge.description}")
                lines.append(f"# TYPE {name} gauge")
                lines.append(f"{name} {gauge.get()}")
                lines.append("")
            
            # Add histograms
            for name, histogram in self.histograms.items():
                lines.append(f"# HELP {name} {histogram.description}")
                lines.append(f"# TYPE {name} histogram")
                
                stats = histogram.get_stats()
                
                # Bucket counts
                for bucket, count in stats['buckets'].items():
                    lines.append(f'{name}_bucket{{le="{bucket}"}} {count}')
                
                lines.append(f'{name}_bucket{{le="+Inf"}} {stats["count"]}')
                lines.append(f"{name}_sum {stats['sum']}")
                lines.append(f"{name}_count {stats['count']}")
                lines.append("")
            
            return "\n".join(lines)
            
        except Exception as e:
            self.logger.error(f"Error generating Prometheus metrics: {e}")
            return ""
    
    async def log_structured_event(
        self,
        event_type: str,
        session_id: str,
        **kwargs
    ):
        """Log structured event"""
        try:
            log_data = {
                'timestamp': datetime.now().isoformat(),
                'event_type': event_type,
                'session_id': session_id,
                **kwargs
            }
            
            # Log as JSON for structured logging
            self.logger.info(json.dumps(log_data))
            
        except Exception as e:
            self.logger.error(f"Error logging structured event: {e}")
    
    async def _collect_system_metrics(self):
        """Background task to collect system metrics"""
        while self._running:
            try:
                await asyncio.sleep(10)  # Collect every 10 seconds
                
                if not self._running:
                    break
                
                # Collect system metrics (placeholder implementation)
                # In a real implementation, you'd use psutil or similar
                import os
                import psutil
                
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                self.cpu_usage_gauge.set(cpu_percent)
                
                # Memory usage
                process = psutil.Process(os.getpid())
                memory_info = process.memory_info()
                self.memory_usage_gauge.set(memory_info.rss)
                
            except asyncio.CancelledError:
                break
            except ImportError:
                # psutil not available, skip system metrics
                await asyncio.sleep(60)
            except Exception as e:
                self.logger.error(f"Error collecting system metrics: {e}")
                await asyncio.sleep(30)
    
    def get_call_rate(self, window_minutes: int = 5) -> float:
        """Get call rate (calls per minute) over specified window"""
        try:
            now = time.time()
            window_start = now - (window_minutes * 60)
            
            # This is a simplified calculation
            # In a real implementation, you'd track timestamps of call events
            total_calls = self.call_started_counter.get()
            
            # Approximate rate based on total calls
            # This is not accurate for sliding windows
            return total_calls / window_minutes if window_minutes > 0 else 0
            
        except Exception as e:
            self.logger.error(f"Error calculating call rate: {e}")
            return 0.0
    
    def reset_metrics(self):
        """Reset all metrics (useful for testing)"""
        try:
            for counter in self.counters.values():
                counter.reset()
            
            for gauge in self.gauges.values():
                gauge.set(0)
            
            # Clear histogram samples
            for histogram in self.histograms.values():
                histogram.samples.clear()
                histogram.sum = 0
                histogram.count = 0
                histogram.bucket_counts = {bucket: 0 for bucket in histogram.buckets}
            
            # Clear error rates
            self.error_rates.clear()
            
            self.logger.info("All metrics reset")
            
        except Exception as e:
            self.logger.error(f"Error resetting metrics: {e}")

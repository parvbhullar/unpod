"""
Task Queue Metrics and Observability Module

This module provides comprehensive metrics tracking for the active/passive agent architecture.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import json


@dataclass
class TaskMetrics:
    """Metrics for individual task execution."""
    task_name: str
    status: str
    processing_time: Optional[float] = None
    retry_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class TaskQueueMetrics:
    """
    Comprehensive metrics tracker for the task queue system.

    Tracks:
    - Task lifecycle events (created, started, completed, failed, timeout)
    - Performance metrics (processing time, queue depth, throughput)
    - Error rates and retry statistics
    - Real-time observability data
    """

    def __init__(self):
        # Event counters
        self.tasks_created = 0
        self.tasks_started = 0
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.tasks_timeout = 0
        self.tasks_retried = 0

        # Performance tracking
        self.processing_times: List[float] = []
        self.completed_tasks: List[TaskMetrics] = []
        self.failed_tasks: List[TaskMetrics] = []

        # Queue depth tracking (snapshots over time)
        self.queue_depth_history: List[tuple] = []  # (timestamp, depth)
        self.last_queue_depth_snapshot = datetime.now()

        # Task type statistics
        self.task_type_stats: Dict[str, Dict] = defaultdict(
            lambda: {
                "count": 0,
                "completed": 0,
                "failed": 0,
                "avg_processing_time": 0.0,
                "total_processing_time": 0.0
            }
        )

        # Error tracking
        self.error_types: Dict[str, int] = defaultdict(int)

        # Session start time
        self.session_start = datetime.now()

    def record_task_created(self, task):
        """Record when a task is created and added to queue."""
        self.tasks_created += 1
        task_type = task.task_name.split('_')[0] if '_' in task.task_name else task.task_name
        self.task_type_stats[task_type]["count"] += 1

    def record_task_started(self, task):
        """Record when a task starts processing."""
        self.tasks_started += 1

    def record_task_completed(self, task):
        """Record successful task completion."""
        self.tasks_completed += 1

        # Track processing time
        if task.get_processing_time():
            processing_time = task.get_processing_time()
            self.processing_times.append(processing_time)

            # Update task type stats
            task_type = task.task_name.split('_')[0] if '_' in task.task_name else task.task_name
            stats = self.task_type_stats[task_type]
            stats["completed"] += 1
            stats["total_processing_time"] += processing_time
            stats["avg_processing_time"] = stats["total_processing_time"] / stats["completed"]

        # Store completed task metrics
        self.completed_tasks.append(TaskMetrics(
            task_name=task.task_name,
            status="completed",
            processing_time=task.get_processing_time(),
            retry_count=task.retry_count,
            created_at=task.created_at,
            completed_at=task.completed_at
        ))

        # Keep only recent tasks (last 100)
        if len(self.completed_tasks) > 100:
            self.completed_tasks = self.completed_tasks[-100:]

    def record_task_failed(self, task):
        """Record task failure."""
        self.tasks_failed += 1

        # Update task type stats
        task_type = task.task_name.split('_')[0] if '_' in task.task_name else task.task_name
        self.task_type_stats[task_type]["failed"] += 1

        # Track error type
        if task.error_message:
            error_type = task.error_message.split(':')[0] if ':' in task.error_message else "Unknown"
            self.error_types[error_type] += 1

        # Store failed task metrics
        self.failed_tasks.append(TaskMetrics(
            task_name=task.task_name,
            status="failed",
            processing_time=task.get_processing_time(),
            retry_count=task.retry_count,
            created_at=task.created_at,
            completed_at=task.completed_at,
            error_message=task.error_message
        ))

        # Keep only recent failures (last 50)
        if len(self.failed_tasks) > 50:
            self.failed_tasks = self.failed_tasks[-50:]

    def record_task_timeout(self, task):
        """Record task timeout."""
        self.tasks_timeout += 1
        # Also count as failed
        self.record_task_failed(task)

    def record_task_retry(self, task):
        """Record task retry attempt."""
        self.tasks_retried += 1

    def snapshot_queue_depth(self, current_depth: int):
        """Take a snapshot of current queue depth."""
        now = datetime.now()
        self.queue_depth_history.append((now, current_depth))

        # Keep only last hour of snapshots
        one_hour_ago = now - timedelta(hours=1)
        self.queue_depth_history = [
            (ts, depth) for ts, depth in self.queue_depth_history
            if ts > one_hour_ago
        ]
        self.last_queue_depth_snapshot = now

    def get_current_stats(self, task_queue: List) -> Dict:
        """
        Get current real-time statistics.

        Args:
            task_queue: The current task queue to analyze

        Returns:
            Dictionary containing current metrics
        """
        # Current queue state
        pending_count = sum(1 for t in task_queue if t.task_status == "pending")
        processing_count = sum(1 for t in task_queue if t.task_status == "processing")
        done_count = sum(1 for t in task_queue if t.task_status == "done")
        failed_count = sum(1 for t in task_queue if t.task_status == "failed")
        timeout_count = sum(1 for t in task_queue if t.task_status == "timeout")

        # Performance metrics
        avg_processing_time = (
            sum(self.processing_times) / len(self.processing_times)
            if self.processing_times else 0.0
        )
        p95_processing_time = (
            sorted(self.processing_times)[int(len(self.processing_times) * 0.95)]
            if len(self.processing_times) > 0 else 0.0
        )

        # Throughput (tasks per minute)
        session_duration_minutes = (datetime.now() - self.session_start).total_seconds() / 60
        throughput = (
            self.tasks_completed / session_duration_minutes
            if session_duration_minutes > 0 else 0.0
        )

        # Success rate
        total_finished = self.tasks_completed + self.tasks_failed
        success_rate = (
            (self.tasks_completed / total_finished * 100)
            if total_finished > 0 else 0.0
        )

        return {
            # Queue state
            "queue": {
                "total_size": len(task_queue),
                "pending": pending_count,
                "processing": processing_count,
                "done": done_count,
                "failed": failed_count,
                "timeout": timeout_count,
            },

            # Lifecycle counters
            "lifecycle": {
                "created": self.tasks_created,
                "started": self.tasks_started,
                "completed": self.tasks_completed,
                "failed": self.tasks_failed,
                "timeout": self.tasks_timeout,
                "retried": self.tasks_retried,
            },

            # Performance
            "performance": {
                "avg_processing_time_sec": round(avg_processing_time, 2),
                "p95_processing_time_sec": round(p95_processing_time, 2),
                "throughput_per_min": round(throughput, 2),
                "success_rate_pct": round(success_rate, 1),
            },

            # Task type breakdown
            "task_types": dict(self.task_type_stats),

            # Error analysis
            "errors": {
                "total_errors": self.tasks_failed,
                "error_types": dict(self.error_types),
                "retry_rate_pct": round(
                    (self.tasks_retried / self.tasks_created * 100)
                    if self.tasks_created > 0 else 0.0,
                    1
                ),
            },

            # Session info
            "session": {
                "start_time": self.session_start.isoformat(),
                "uptime_minutes": round(session_duration_minutes, 1),
            }
        }

    def get_health_status(self, task_queue: List) -> Dict:
        """
        Get system health status with alerts.

        Returns:
            Dictionary with health status and alerts
        """
        stats = self.get_current_stats(task_queue)

        alerts = []
        health = "healthy"

        # Check for high queue depth
        if stats["queue"]["pending"] > 10:
            alerts.append({
                "level": "warning",
                "message": f"High queue depth: {stats['queue']['pending']} pending tasks"
            })
            health = "degraded"

        # Check for low success rate
        if stats["performance"]["success_rate_pct"] < 80 and stats["lifecycle"]["completed"] > 5:
            alerts.append({
                "level": "critical",
                "message": f"Low success rate: {stats['performance']['success_rate_pct']}%"
            })
            health = "unhealthy"

        # Check for high timeout rate
        timeout_rate = (
            stats["lifecycle"]["timeout"] / stats["lifecycle"]["created"] * 100
            if stats["lifecycle"]["created"] > 0 else 0
        )
        if timeout_rate > 20:
            alerts.append({
                "level": "warning",
                "message": f"High timeout rate: {timeout_rate:.1f}%"
            })
            health = "degraded"

        # Check for processing backlog
        if stats["queue"]["processing"] > 5:
            alerts.append({
                "level": "warning",
                "message": f"Multiple tasks processing: {stats['queue']['processing']}"
            })

        return {
            "health": health,
            "alerts": alerts,
            "stats": stats
        }

    def export_metrics_json(self, task_queue: List) -> str:
        """Export metrics as JSON string."""
        stats = self.get_current_stats(task_queue)
        return json.dumps(stats, indent=2)

    def print_metrics_summary(self, task_queue: List):
        """Print a formatted metrics summary to console."""
        stats = self.get_current_stats(task_queue)

        print("\n" + "="*60)
        print("📊 TASK QUEUE METRICS SUMMARY")
        print("="*60)

        print("\n🔢 Queue State:")
        print(f"  Total Size: {stats['queue']['total_size']}")
        print(f"  Pending: {stats['queue']['pending']}")
        print(f"  Processing: {stats['queue']['processing']}")
        print(f"  Done: {stats['queue']['done']}")
        print(f"  Failed: {stats['queue']['failed']}")
        print(f"  Timeout: {stats['queue']['timeout']}")

        print("\n📈 Performance:")
        print(f"  Avg Processing Time: {stats['performance']['avg_processing_time_sec']}s")
        print(f"  P95 Processing Time: {stats['performance']['p95_processing_time_sec']}s")
        print(f"  Throughput: {stats['performance']['throughput_per_min']} tasks/min")
        print(f"  Success Rate: {stats['performance']['success_rate_pct']}%")

        print("\n🔄 Lifecycle:")
        print(f"  Created: {stats['lifecycle']['created']}")
        print(f"  Completed: {stats['lifecycle']['completed']}")
        print(f"  Failed: {stats['lifecycle']['failed']}")
        print(f"  Retried: {stats['lifecycle']['retried']}")

        if stats['errors']['error_types']:
            print("\n❌ Top Errors:")
            for error_type, count in sorted(
                stats['errors']['error_types'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]:
                print(f"  {error_type}: {count}")

        print("\n⏱️  Session:")
        print(f"  Uptime: {stats['session']['uptime_minutes']} minutes")

        print("="*60 + "\n")

    def reset(self):
        """Reset all metrics (useful for testing or session restart)."""
        self.__init__()
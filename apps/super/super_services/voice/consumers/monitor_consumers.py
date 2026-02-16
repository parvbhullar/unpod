#!/usr/bin/env python3
"""
Voice Task Consumer Monitoring Dashboard

Real-time monitoring of consumer health, worker utilization, and latency metrics.
"""

import os
import sys
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from super_services.libs.core.redis import REDIS
from super_services.voice.consumers.voice_task_consumer import MetricsCollector


def clear_screen():
    """Clear terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def get_worker_counts(mode):
    """Get worker counts for all providers in a specific mode."""
    providers = ["vapi", "pipecat", "livekit"]
    counts = {}
    total = 0

    for provider in providers:
        key = f"{mode}_{provider}_call_workers"
        try:
            value = REDIS.get(key)
            count = int(value) if value else 0
            counts[provider] = count
            total += count
        except Exception:
            counts[provider] = 0

    return counts, total


def get_latency_stats(mode):
    """Get latency statistics for a specific mode."""
    try:
        avg = MetricsCollector.get_average_latency(mode)
        p95 = MetricsCollector.get_p95_latency(mode)

        # Count recent entries
        redis_key = f"metrics:task_latency:{mode}"
        entries = REDIS.lrange(redis_key, 0, -1)
        sample_count = len(entries)

        return {
            "avg": avg,
            "p95": p95,
            "sample_count": sample_count
        }
    except Exception:
        return {"avg": 0.0, "p95": 0.0, "sample_count": 0}


def format_latency(latency_ms, sla_ms):
    """Format latency with color coding based on SLA."""
    if latency_ms == 0:
        return "     N/A"
    elif latency_ms > sla_ms:
        return f"\033[91m{latency_ms:7.1f}ms ⚠\033[0m"  # Red
    elif latency_ms > sla_ms * 0.8:
        return f"\033[93m{latency_ms:7.1f}ms ⚠\033[0m"  # Yellow
    else:
        return f"\033[92m{latency_ms:7.1f}ms ✓\033[0m"  # Green


def format_worker_count(current, max_workers):
    """Format worker count with utilization percentage."""
    if max_workers == 0:
        return "0/0 (0%)"

    utilization = (current / max_workers) * 100

    if utilization >= 90:
        color = "\033[91m"  # Red
    elif utilization >= 70:
        color = "\033[93m"  # Yellow
    else:
        color = "\033[92m"  # Green

    return f"{color}{current}/{max_workers} ({utilization:.0f}%)\033[0m"


def print_dashboard():
    """Print the monitoring dashboard."""
    clear_screen()

    # Header
    print("\033[1;34m" + "=" * 80)
    print("           VOICE TASK CONSUMER MONITORING DASHBOARD")
    print("=" * 80 + "\033[0m")
    print(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Configuration
    total_workers = int(os.getenv("AGENT_OUTBOUND_MAX_WORKERS", 4))
    normal_max = max(1, int(total_workers * 0.7))
    bulk_max = max(1, int(total_workers * 0.4))

    print("\033[1mConfiguration:\033[0m")
    print(f"  Total Workers:     {total_workers}")
    print(f"  Normal Max:        {normal_max} (70%)")
    print(f"  Bulk Max:          {bulk_max} (40%)")
    print()

    # Worker Utilization
    print("\033[1;36m" + "-" * 80)
    print("WORKER UTILIZATION")
    print("-" * 80 + "\033[0m")
    print()

    normal_counts, normal_total = get_worker_counts("normal")
    bulk_counts, bulk_total = get_worker_counts("bulk")

    print(f"\033[1mNormal Mode:\033[0m  {format_worker_count(normal_total, normal_max)}")
    for provider, count in normal_counts.items():
        print(f"  {provider:10s}: {count}")

    print()

    print(f"\033[1mBulk Mode:\033[0m    {format_worker_count(bulk_total, bulk_max)}")
    for provider, count in bulk_counts.items():
        print(f"  {provider:10s}: {count}")

    print()

    # Latency Metrics
    print("\033[1;36m" + "-" * 80)
    print("LATENCY METRICS")
    print("-" * 80 + "\033[0m")
    print()

    normal_stats = get_latency_stats("normal")
    bulk_stats = get_latency_stats("bulk")

    print(f"{'Mode':<10} {'Avg Latency':<15} {'P95 Latency':<15} {'Samples':<10} {'SLA':<10}")
    print("-" * 80)

    normal_sla = 5000  # 5 seconds
    bulk_sla = 30000   # 30 seconds

    print(
        f"{'Normal':<10} "
        f"{format_latency(normal_stats['avg'], normal_sla):<24} "
        f"{format_latency(normal_stats['p95'], normal_sla):<24} "
        f"{normal_stats['sample_count']:<10} "
        f"{normal_sla/1000:.0f}s"
    )

    print(
        f"{'Bulk':<10} "
        f"{format_latency(bulk_stats['avg'], bulk_sla):<24} "
        f"{format_latency(bulk_stats['p95'], bulk_sla):<24} "
        f"{bulk_stats['sample_count']:<10} "
        f"{bulk_sla/1000:.0f}s"
    )

    print()

    # Health Status
    print("\033[1;36m" + "-" * 80)
    print("HEALTH STATUS")
    print("-" * 80 + "\033[0m")
    print()

    # Check if consumers are processing (recent latency entries)
    normal_healthy = normal_stats['sample_count'] > 0
    bulk_healthy = bulk_stats['sample_count'] > 0

    normal_status = "\033[92m✓ HEALTHY\033[0m" if normal_healthy else "\033[91m✗ NO ACTIVITY\033[0m"
    bulk_status = "\033[92m✓ HEALTHY\033[0m" if bulk_healthy else "\033[93m⚠ NO ACTIVITY\033[0m"

    print(f"Normal Consumer: {normal_status}")
    print(f"Bulk Consumer:   {bulk_status}")

    # Warnings
    warnings = []

    if normal_total >= normal_max:
        warnings.append("⚠️  Normal consumer at max capacity")

    if bulk_total >= bulk_max:
        warnings.append("⚠️  Bulk consumer at max capacity")

    if normal_stats['avg'] > normal_sla:
        warnings.append(f"⚠️  Normal SLA breach: {normal_stats['avg']:.0f}ms > {normal_sla}ms")

    if bulk_stats['avg'] > bulk_sla:
        warnings.append(f"⚠️  Bulk SLA breach: {bulk_stats['avg']:.0f}ms > {bulk_sla}ms")

    if not normal_healthy:
        warnings.append("⚠️  Normal consumer not processing tasks")

    if warnings:
        print()
        print("\033[1;33mWARNINGS:\033[0m")
        for warning in warnings:
            print(f"  {warning}")

    print()
    print("\033[90mPress Ctrl+C to exit | Refreshing every 5 seconds...\033[0m")


def main():
    """Main monitoring loop."""
    print("\033[1;32mStarting Voice Task Consumer Monitoring...\033[0m")
    print("Connecting to Redis...")

    try:
        # Test Redis connection
        REDIS.ping()
        print("\033[92m✓ Redis connected\033[0m")
        time.sleep(1)
    except Exception as ex:
        print(f"\033[91m✗ Redis connection failed: {ex}\033[0m")
        sys.exit(1)

    # Main monitoring loop
    try:
        while True:
            print_dashboard()
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n\n\033[1;32mMonitoring stopped.\033[0m")
        sys.exit(0)


if __name__ == "__main__":
    main()

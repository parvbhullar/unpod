"""
Temporal worker for voice task processing.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from temporalio.client import Client
from temporalio.worker import Worker

from super.core.logging.logging import print_log
from super_services.voice.workflows.workflows import VoiceTaskWorkflow
from super_services.voice.workflows.activities import execute_call_activity


async def main():
    """
    Start the Temporal worker for voice task processing.
    """
    # Get Temporal server address from environment or use default
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    task_queue = os.getenv("VOICE_TASK_QUEUE", "voice-task-queue")
    temporal_api_key = os.getenv("TEMPORAL_API_KEY", "")

    print_log(f"Connecting to Temporal server at {temporal_address}", "temporal_worker_init")

    # Connect to Temporal server
    client = await Client.connect(
        temporal_address,
        namespace=temporal_namespace,
        api_key=temporal_api_key if temporal_api_key else None,
        tls=True,
    )

    print_log(f"Connected to Temporal server, starting worker on task queue: {task_queue}", "temporal_worker_start")

    # Initialize CUDA before starting worker
    try:
        from super_services.voice.consumers.voice_task_consumer import TaskServiceQueueManager
        manager = TaskServiceQueueManager()
        manager.init_cuda()
        print_log("CUDA initialized successfully", "cuda_init")
    except Exception as e:
        print_log(f"CUDA initialization warning: {str(e)}", "cuda_init_warning")

    # Create and run worker
    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[VoiceTaskWorkflow],
        activities=[execute_call_activity],
    )

    print_log(f"Worker started successfully on task queue: {task_queue}", "temporal_worker_running")

    # Run worker until shutdown
    await worker.run()


if __name__ == "__main__":
    print_log("Starting Temporal Worker for Voice Tasks", "service_start")
    asyncio.run(main())

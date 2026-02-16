"""
Queue Processor - Passive Agent Frame Processor for Pipecat
This processor monitors the task queue and processes tasks in the background
without interfering with the main conversation pipeline.
"""
from pipecat.frames.frames import Frame, TextFrame, SystemFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from dataclasses import asdict
import asyncio
from typing import Optional
from super.core.logging.logging import print_log


class QueueProcessorFrame(SystemFrame):
    """Custom frame to trigger queue processing"""
    pass


class TaskQueueProcessor(FrameProcessor):
    """
    Passive Agent Frame Processor

    This processor runs in the background of the Pipecat pipeline,
    monitoring the task_queue and processing tasks without blocking
    the main conversation flow.

    Usage:
        processor = TaskQueueProcessor(handler, processing_interval=2.0)
        # Add to pipeline before or after the LLM
    """

    def __init__(
        self,
        handler,
        processing_interval: float = 2.0,
        max_concurrent_tasks: int = 3,
        **kwargs
    ):
        """
        Initialize the Task Queue Processor

        Args:
            handler: BaseHandler instance with task_queue attribute
            processing_interval: How often to check the queue (seconds)
            max_concurrent_tasks: Maximum number of tasks to process concurrently
        """
        super().__init__(**kwargs)
        self.handler = handler
        self.processing_interval = processing_interval
        self.max_concurrent_tasks = max_concurrent_tasks
        self._processing_task: Optional[asyncio.Task] = None
        self._running = False
        self._active_tasks = set()

    async def start(self, frame: Frame):
        """Start the background queue processing"""
        self._running = True
        self._processing_task = asyncio.create_task(self._process_queue_loop())
        print_log("✅ TaskQueueProcessor started - monitoring queue")

    async def stop(self, frame: Frame):
        """Stop the background queue processing"""
        self._running = False
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass

        # Wait for active tasks to complete
        if self._active_tasks:
            print_log(f"⏳ Waiting for {len(self._active_tasks)} active tasks to complete...")
            await asyncio.gather(*self._active_tasks, return_exceptions=True)

        print_log("🛑 TaskQueueProcessor stopped")

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        """
        Process frames - we don't modify the pipeline, just pass through
        """
        # Handle system frames (StartFrame, StopFrame, etc) before passing through
        from pipecat.frames.frames import StartFrame, StopFrame

        if isinstance(frame, StartFrame):
            await self.start(frame)
        elif isinstance(frame, StopFrame):
            await self.stop(frame)

        # Pass all frames through unchanged
        await self.push_frame(frame, direction)

    async def _process_queue_loop(self):
        """
        Background loop that monitors and processes the task queue
        """
        print_log("🔄 Queue processing loop started")

        while self._running:
            try:
                # Check if there are pending tasks
                pending_tasks = [
                    task for task in self.handler.task_queue
                    if hasattr(task, 'task_status') and task.task_status == "pending"
                ]

                if pending_tasks:
                    print_log(f"📋 Found {len(pending_tasks)} pending tasks in queue")

                    # Process tasks up to max_concurrent_tasks
                    for task in pending_tasks[:self.max_concurrent_tasks - len(self._active_tasks)]:
                        if len(self._active_tasks) >= self.max_concurrent_tasks:
                            break

                        # Create background task for processing
                        task_coro = self._process_task(task)
                        bg_task = asyncio.create_task(task_coro)
                        self._active_tasks.add(bg_task)
                        bg_task.add_done_callback(self._active_tasks.discard)

                # Clean up completed background tasks
                self._active_tasks = {t for t in self._active_tasks if not t.done()}

                # Wait before next check
                await asyncio.sleep(self.processing_interval)

            except asyncio.CancelledError:
                print_log("⚠️ Queue processing loop cancelled")
                break
            except Exception as e:
                print_log(f"❌ Error in queue processing loop: {str(e)}", level="error")
                await asyncio.sleep(self.processing_interval)

    async def _process_task(self, task):
        """
        Process a single task from the queue

        Args:
            task: PipelineTasks instance
        """
        try:
            print_log(f"🔧 Processing task: {task.task_name} - {task.task_description}")

            # Mark task as processing
            task.task_status = "processing"

            # Route task based on task_name or assignee
            result = await self._execute_task(task)

            # Update task with result
            task.task_status = "completed"
            task.task_result = result

            print_log(f"✅ Task completed: {task.task_name}")

        except Exception as e:
            task.task_status = "failed"
            task.task_result = f"Error: {str(e)}"
            print_log(f"❌ Task failed: {task.task_name} - {str(e)}", level="error")

    async def _execute_task(self, task) -> str:
        """
        Execute the task based on its type

        Override this method to add custom task handlers

        Args:
            task: PipelineTasks instance

        Returns:
            str: Result of task execution
        """
        # Default handlers based on task_name or task_description
        task_name_lower = task.task_name.lower()

        # Knowledge base search
        if any(keyword in task_name_lower for keyword in ["search", "find", "query", "kb", "knowledge"]):
            return await self._handle_kb_search(task)

        # Document fetching
        elif "fetch" in task_name_lower or "get_docs" in task_name_lower:
            return await self._handle_fetch_docs(task)

        # Custom task handlers
        elif hasattr(self.handler, 'custom_task_handlers'):
            handler = self.handler.custom_task_handlers.get(task.task_name)
            if handler:
                return await handler(task)

        # Default: log the task
        print_log(f"⚠️ No specific handler for task: {task.task_name}")
        return f"Task '{task.task_name}' queued but no handler found"

    async def _handle_kb_search(self, task) -> str:
        """Handle knowledge base search tasks"""
        try:
            # Extract query from task description
            query = task.task_description

            if hasattr(self.handler, 'get_docs'):
                print_log(f"🔍 Searching KB for: {query}")
                results = await self.handler.get_docs(query=query)
                return str(results)
            else:
                return "Knowledge base not available"

        except Exception as e:
            print_log(f"❌ KB search error: {str(e)}", level="error")
            return f"KB search failed: {str(e)}"

    async def _handle_fetch_docs(self, task) -> str:
        """Handle document fetching tasks"""
        try:
            # Parse task description to extract query
            query = task.task_description

            if hasattr(self.handler, 'get_docs'):
                print_log(f"📄 Fetching docs for: {query}")
                docs = await self.handler.get_docs(query=query)
                return str(docs)
            else:
                return "Document fetching not available"

        except Exception as e:
            print_log(f"❌ Fetch docs error: {str(e)}", level="error")
            return f"Fetch failed: {str(e)}"

    def get_queue_status(self) -> dict:
        """
        Get current queue status

        Returns:
            dict: Queue statistics
        """
        pending = sum(1 for t in self.handler.task_queue if hasattr(t, 'task_status') and t.task_status == "pending")
        processing = sum(1 for t in self.handler.task_queue if hasattr(t, 'task_status') and t.task_status == "processing")
        completed = sum(1 for t in self.handler.task_queue if hasattr(t, 'task_status') and t.task_status == "completed")
        failed = sum(1 for t in self.handler.task_queue if hasattr(t, 'task_status') and t.task_status == "failed")

        return {
            "total": len(self.handler.task_queue),
            "pending": pending,
            "processing": processing,
            "completed": completed,
            "failed": failed,
            "active_background_tasks": len(self._active_tasks)
        }
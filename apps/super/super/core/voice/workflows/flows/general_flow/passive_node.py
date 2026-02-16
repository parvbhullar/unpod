from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext
import asyncio

load_dotenv(verbose=True)
from super.core.voice.workflows.shared_queue import ActionDirection ,ActionType ,ActionStatus

@dataclass
class PipelineTasks:
    assignee: str
    task_name: str
    task_description: str
    task_status: str  # "pending" | "processing" | "done" | "failed" | "timeout"
    task_result: Optional[str] = None

    # Lifecycle tracking
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Error handling
    retry_count: int = 0
    max_retries: int = 2
    error_message: Optional[str] = None

    # Performance tracking
    timeout_seconds: int = 30

    # Event for race condition handling
    completion_event: asyncio.Event = field(default_factory=asyncio.Event, repr=False, compare=False)

    def get_processing_time(self) -> Optional[float]:
        """Get task processing time in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def get_age(self) -> float:
        """Get task age in seconds."""
        return (datetime.now() - self.created_at).total_seconds()

    def is_timed_out(self) -> bool:
        """Check if task has exceeded timeout."""
        return self.get_age() > self.timeout_seconds and self.task_status in ["pending", "processing"]

    def to_serializable_dict(self) -> dict:
        """Convert task to a serializable dictionary (excludes non-serializable fields)."""
        return {
            "assignee": self.assignee,
            "task_name": self.task_name,
            "task_description": self.task_description,
            "task_status": self.task_status,
            "task_result": self.task_result,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "error_message": self.error_message,
            "timeout_seconds": self.timeout_seconds,
            "processing_time": self.get_processing_time(),
            "age_seconds": self.get_age()
        }


class PassiveAgent:
    def __init__(self, handler):
        self.handler = handler
        self.agent = None

    def create_task_agent(self):
        """Create the pydantic-ai agent with tools."""
        agent = Agent(
            'openai:gpt-4o-mini',
            system_prompt=(
                '''
                You are an information retrieval agent. Your ONLY job is to fetch and return raw information.

                When given a task:
                1. Call the `get_docs` tool with the user's query
                2. Return EXACTLY what the tool provides - DO NOT summarize, rephrase, or add commentary
                3. Just pass through the raw information as-is
                4. Use 'handover_call' to transfer call to Supervisor 

                CRITICAL: Your response should be the exact content from get_docs, nothing more, nothing less.
                Do not add phrases like "Here is the information" or "Based on the documents".
                Just return the raw content.

                Example:
                Task: "Find information about courses in Delhi"
                Action: Call get_docs("courses in Delhi")
                Response: [Return only the exact content from get_docs]
                '''
            ),
        )

        # Register the tool after agent creation
        @agent.tool
        async def get_docs(ctx: RunContext[str], query: str) -> str:
            """Tool used to fetch docs based on user query to answer the question."""
            doc_list = await self.handler.get_docs(query)
            # Convert SearchDoc objects to formatted text
            if doc_list:
                serialized_docs = []
                for doc in doc_list:
                    if hasattr(doc, 'to_dict'):
                        serialized_docs.append(doc.to_dict())
                    elif isinstance(doc, dict):
                        serialized_docs.append(doc)
                    else:
                        # Fallback: convert to string
                        serialized_docs.append(str(doc))
                return str(serialized_docs)
            return ""


        return agent

    async def run(self):
        """Run the passive agent loop to process pending tasks."""
        import asyncio

        # Create agent if not already created
        if not self.agent:
            self.agent = self.create_task_agent()

        while self.handler.agent_running:
            if self.handler.shared_queue:

                # print("using shared queue manager")
                action = await self.handler.shared_queue.pop_action(direction=ActionDirection.TO_PROCESSING)
                # print(action)
                if action:
                    print(f"PA received action with  in payload: {action.payload}")
                    task = action.payload
                    if task:
                        print(f"📥 PA received task: {task.get('task',{}).get('query')}...")
                        response = await self.agent.run(task.get("task",{}).get("query"))
                        print(f"✅ PA completed task, sending response ({len(str(response))} chars)")

                        await self.handler.shared_queue.push_action(
                            action_type=ActionType.SEND_RESPONSE,
                            direction=ActionDirection.TO_COMMUNICATION,
                            payload={
                                "response": response.output if hasattr(response, 'output') else str(response),
                                "user_query": task,
                                "original_action_id": action.id
                            }
                        )
                        await self.handler.shared_queue.update_action_status(
                            action_id=action.id,
                            status=ActionStatus.COMPLETED,
                        )
                        # Action status will be marked COMPLETED by CA after it executes the response
                    else:
                        print(f"⚠️ PA received action with no 'task' in payload: {action.payload}")
            else:
                # Check for timed out tasks first
                for task in self.handler.task_queue:
                    if task.is_timed_out():
                        task.task_status = "timeout"
                        task.completed_at = datetime.now()
                        task.error_message = f"Task timed out after {task.timeout_seconds}s"
                        task.completion_event.set()  # Signal completion
                        print(f"⏰ Task timed out: {task.task_name}")
                        self.handler.metrics.record_task_timeout(task)

                # Find pending tasks (prioritize retries)
                pending_task = next(
                    (t for t in self.handler.task_queue
                     if t.task_status == "pending" and t.retry_count > 0),
                    None
                )

                if not pending_task:
                    # No retry tasks, get regular pending task
                    pending_task = next(
                        (t for t in self.handler.task_queue if t.task_status == "pending"),
                        None
                    )

                if pending_task:
                    try:
                        # Mark as processing
                        pending_task.task_status = "processing"
                        pending_task.started_at = datetime.now()
                        self.handler.metrics.record_task_started(pending_task)

                        # Run the agent with the task description
                        response = await self.agent.run(pending_task.task_description)

                        if response:
                            # Update task with result
                            pending_task.task_result = response.output
                            pending_task.task_status = "done"
                            pending_task.completed_at = datetime.now()
                            pending_task.completion_event.set()  # Signal completion (fixes race condition)

                            # Record metrics
                            self.handler.metrics.record_task_completed(pending_task)
                            print(f"✅ Task completed: {pending_task.task_name} (took {pending_task.get_processing_time():.2f}s)")

                    except Exception as e:
                        print(f"❌ Error processing task {pending_task.task_name}: {e}")
                        pending_task.error_message = str(e)

                        # Retry logic
                        if pending_task.retry_count < pending_task.max_retries:
                            pending_task.retry_count += 1
                            pending_task.task_status = "pending"  # Retry
                            pending_task.started_at = None  # Reset start time
                            print(f"🔄 Retrying task {pending_task.task_name} (attempt {pending_task.retry_count + 1}/{pending_task.max_retries + 1})")
                            self.handler.metrics.record_task_retry(pending_task)
                        else:
                            # Max retries exceeded
                            pending_task.task_status = "failed"
                            pending_task.completed_at = datetime.now()
                            pending_task.task_result = f"Error: {str(e)}"
                            pending_task.completion_event.set()  # Signal completion
                            self.handler.metrics.record_task_failed(pending_task)

            # Yield control back to the event loop to prevent blocking
            await asyncio.sleep(0.1)
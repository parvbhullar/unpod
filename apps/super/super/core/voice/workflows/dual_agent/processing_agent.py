"""
Processing Agent - Compute-intensive task executor

This agent handles heavy computation using LangGraph:
- Polls Task Queue for pending tasks
- Executes tools (KB search, DB query, API calls, etc.)
- Updates task status in real-time
- Pushes results to Context Aggregator
- Complex reasoning with LLM
"""

import asyncio
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime
import logging

from super.core.voice.workflows.dual_agent.task_queue import TaskQueue, Task, TaskType, TaskStatus
from super.core.voice.workflows.dual_agent.context_aggregator import ContextAggregator


logger = logging.getLogger(__name__)


class ProcessingAgent:
    """
    Background task executor for compute-intensive operations.

    Responsibilities:
    - Poll Task Queue for pending tasks (non-blocking)
    - Execute tools with proper error handling
    - Update task status in real-time
    - Cache results in Context Aggregator
    - Handle task timeouts gracefully
    """

    def __init__(
        self,
        session_id: str,
        context: ContextAggregator,
        task_queue: TaskQueue,
        tools: Dict[str, Callable]
    ):
        """
        Initialize Processing Agent.

        Args:
            session_id: Session identifier
            context: Shared context aggregator
            task_queue: Task queue for async communication
            tools: Available tools mapped by name
                   e.g., {"search_docs": search_func, "query_db": db_func}
        """
        self.session_id = session_id
        self.context = context
        self.task_queue = task_queue
        self.tools = tools

        # Agent state
        self._is_running = False
        self._poll_interval = 0.5  # Poll every 500ms
        self._executor_tasks: Dict[str, asyncio.Task] = {}

    async def start(self):
        """Start the processing agent"""
        self._is_running = True
        logger.info(f"[ProcessingAgent] Started for session {self.session_id}")

        # Start polling loop
        asyncio.create_task(self._poll_loop())

    async def stop(self):
        """Stop the processing agent"""
        self._is_running = False

        # Cancel all running executor tasks
        for task_id, task in self._executor_tasks.items():
            if not task.done():
                task.cancel()
                logger.info(f"[ProcessingAgent] Cancelled task {task_id}")

        logger.info(f"[ProcessingAgent] Stopped for session {self.session_id}")

    async def _poll_loop(self):
        """
        Main polling loop - checks Task Queue for pending tasks.

        Runs continuously while agent is active.
        """
        logger.info("[ProcessingAgent] Poll loop started")

        while self._is_running:
            try:
                # Get pending tasks (priority-sorted)
                pending_tasks = await self.task_queue.get_pending_tasks(limit=5)

                if pending_tasks:
                    logger.debug(f"[ProcessingAgent] Found {len(pending_tasks)} pending tasks")

                    for task in pending_tasks:
                        # Skip if already executing
                        if task.task_id in self._executor_tasks:
                            continue

                        # Execute task in background
                        executor_task = asyncio.create_task(self._execute_task(task))
                        self._executor_tasks[task.task_id] = executor_task

                # Clean up completed executor tasks
                completed = [
                    task_id for task_id, task in self._executor_tasks.items()
                    if task.done()
                ]
                for task_id in completed:
                    del self._executor_tasks[task_id]

                # Wait before next poll
                await asyncio.sleep(self._poll_interval)

            except Exception as e:
                logger.error(f"[ProcessingAgent] Error in poll loop: {e}", exc_info=True)
                await asyncio.sleep(self._poll_interval)

        logger.info("[ProcessingAgent] Poll loop stopped")

    async def _execute_task(self, task: Task):
        """
        Execute a single task.

        Args:
            task: Task to execute
        """
        task_id = task.task_id
        logger.info(f"[ProcessingAgent] Executing task {task_id} (type: {task.task_type.value})")

        try:
            # Mark task as in-progress
            await self.task_queue.update_task_status(
                task_id,
                "IN_PROGRESS",
                started_at=datetime.now()
            )

            # Execute based on task type
            if task.task_type == TaskType.KB_SEARCH:
                result = await self._execute_kb_search(task)

            elif task.task_type == TaskType.DB_QUERY:
                result = await self._execute_db_query(task)

            elif task.task_type == TaskType.ELIGIBILITY_CHECK:
                result = await self._execute_eligibility_check(task)

            elif task.task_type == TaskType.API_CALL:
                result = await self._execute_api_call(task)

            elif task.task_type == TaskType.COMPUTE:
                result = await self._execute_compute(task)

            else:
                raise ValueError(f"Unknown task type: {task.task_type}")

            # Mark task as completed
            await self.task_queue.complete_task(task_id, result)

            # Cache result in context
            await self.context.cache_tool_result(
                tool_name=task.task_type.value,
                result=result,
                ttl_seconds=300
            )

            logger.info(f"[ProcessingAgent] Task {task_id} completed successfully")

        except asyncio.CancelledError:
            # Task was cancelled
            await self.task_queue.fail_task(task_id, "Task cancelled")
            logger.warning(f"[ProcessingAgent] Task {task_id} cancelled")
            raise

        except Exception as e:
            # Task failed
            error_msg = f"{type(e).__name__}: {str(e)}"
            await self.task_queue.fail_task(task_id, error_msg)
            logger.error(f"[ProcessingAgent] Task {task_id} failed: {error_msg}", exc_info=True)

    async def _execute_kb_search(self, task: Task) -> Any:
        """
        Execute knowledge base semantic search.

        Args:
            task: Task with query and context

        Returns:
            Search results
        """
        logger.debug(f"[ProcessingAgent] KB Search: {task.query}")

        # Get search function
        search_func = self.tools.get("search_docs")
        if not search_func:
            raise RuntimeError("search_docs tool not available")

        # Execute search
        result = await search_func(task.query)

        return result

    async def _execute_db_query(self, task: Task) -> Any:
        """
        Execute database query.

        Args:
            task: Task with query and context

        Returns:
            Query results
        """
        logger.debug(f"[ProcessingAgent] DB Query: {task.query}")

        # Get query function
        query_func = self.tools.get("query_database")
        if not query_func:
            raise RuntimeError("query_database tool not available")

        # Execute query
        result = await query_func(task.query, task.context)

        return result

    async def _execute_eligibility_check(self, task: Task) -> Any:
        """
        Execute business logic eligibility check.

        Args:
            task: Task with user data and check criteria

        Returns:
            Eligibility result
        """
        logger.debug(f"[ProcessingAgent] Eligibility Check: {task.query}")

        # Get eligibility function
        check_func = self.tools.get("check_eligibility")
        if not check_func:
            raise RuntimeError("check_eligibility tool not available")

        # Execute check
        user_data = task.context.get("user_attributes", {})
        result = await check_func(user_data, task.query)

        return result

    async def _execute_api_call(self, task: Task) -> Any:
        """
        Execute external API call.

        Args:
            task: Task with API endpoint and params

        Returns:
            API response
        """
        logger.debug(f"[ProcessingAgent] API Call: {task.query}")

        # Get API function
        api_func = self.tools.get("call_api")
        if not api_func:
            raise RuntimeError("call_api tool not available")

        # Execute API call
        result = await api_func(task.query, task.context)

        return result

    async def _execute_compute(self, task: Task) -> Any:
        """
        Execute heavy computation.

        Args:
            task: Task with computation details

        Returns:
            Computation result
        """
        logger.debug(f"[ProcessingAgent] Compute: {task.query}")

        # Get compute function
        compute_func = self.tools.get("compute")
        if not compute_func:
            raise RuntimeError("compute tool not available")

        # Execute computation
        result = await compute_func(task.query, task.context)

        return result

    async def register_tool(self, name: str, func: Callable):
        """
        Register a new tool at runtime.

        Args:
            name: Tool name
            func: Tool function (must be async)
        """
        self.tools[name] = func
        logger.info(f"[ProcessingAgent] Registered tool: {name}")

    async def unregister_tool(self, name: str):
        """
        Unregister a tool.

        Args:
            name: Tool name
        """
        if name in self.tools:
            del self.tools[name]
            logger.info(f"[ProcessingAgent] Unregistered tool: {name}")

    async def get_stats(self) -> Dict[str, Any]:
        """Get processing agent statistics"""
        return {
            "session_id": self.session_id,
            "is_running": self._is_running,
            "active_tasks": len(self._executor_tasks),
            "registered_tools": list(self.tools.keys()),
            "poll_interval_ms": self._poll_interval * 1000
        }


class LangGraphProcessingAgent(ProcessingAgent):
    """
    Extended Processing Agent with LangGraph integration.

    Adds LangGraph capabilities for complex multi-step reasoning.
    """

    def __init__(
        self,
        session_id: str,
        context: ContextAggregator,
        task_queue: TaskQueue,
        tools: Dict[str, Callable],
        llm_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize LangGraph Processing Agent.

        Args:
            session_id: Session identifier
            context: Shared context aggregator
            task_queue: Task queue for async communication
            tools: Available tools
            llm_config: LLM configuration for reasoning
        """
        super().__init__(session_id, context, task_queue, tools)
        self.llm_config = llm_config or {}

        # LangGraph state
        self._graph = None
        self._llm = None

    async def _execute_kb_search(self, task: Task) -> Any:
        """
        Execute KB search with LangGraph reasoning.

        Enhanced to use LLM for query refinement and result synthesis.
        """
        logger.debug(f"[LangGraphAgent] KB Search with reasoning: {task.query}")

        # Step 1: Refine query using LLM (if needed)
        refined_query = await self._refine_query(task.query, task.context)

        # Step 2: Execute search
        search_func = self.tools.get("search_docs")
        if not search_func:
            raise RuntimeError("search_docs tool not available")

        raw_results = await search_func(refined_query)

        # Step 3: Synthesize results using LLM
        synthesized = await self._synthesize_results(raw_results, task.query, task.context)

        return synthesized

    async def _refine_query(self, query: str, context: Dict[str, Any]) -> str:
        """
        Refine user query using LLM and conversation context.

        Args:
            query: Original query
            context: Conversation context

        Returns:
            Refined query
        """
        # Placeholder - in production:
        # - Use LLM to understand user intent
        # - Incorporate conversation history
        # - Expand abbreviations, fix typos
        # - Add relevant context from user_attributes

        logger.debug(f"[LangGraphAgent] Refining query: {query}")

        # For now, return original query
        return query

    async def _synthesize_results(
        self,
        results: Any,
        original_query: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Synthesize search results into natural language response.

        Args:
            results: Raw search results
            original_query: User's original question
            context: Conversation context

        Returns:
            Synthesized natural language answer
        """
        # Placeholder - in production:
        # - Use LLM to generate natural response
        # - Cite sources
        # - Handle "no results found" gracefully
        # - Personalize based on user_attributes

        logger.debug(f"[LangGraphAgent] Synthesizing results for: {original_query}")

        # For now, return results as-is
        if isinstance(results, str):
            return results
        else:
            return str(results)

    async def _execute_compute(self, task: Task) -> Any:
        """
        Execute complex computation with multi-step reasoning (LangGraph).

        Args:
            task: Task with computation requirements

        Returns:
            Computation result
        """
        logger.debug(f"[LangGraphAgent] Complex compute with LangGraph: {task.query}")

        # Placeholder for LangGraph execution
        # In production:
        # - Define LangGraph workflow
        # - Execute multi-step reasoning
        # - Use tools as needed
        # - Return final result

        compute_func = self.tools.get("compute")
        if compute_func:
            return await compute_func(task.query, task.context)
        else:
            return {"result": "Computation not implemented"}

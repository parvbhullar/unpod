"""
Communication Agent - Real-time conversation flow handler

This agent maintains conversational flow with users using Pipecat-flows:
- Handles conversation nodes (Instruction, Question, Explanation)
- Delegates compute-intensive tasks to Processing Agent via Task Queue
- Provides filler responses during task execution
- Implements 90% TTS overlap rule
- Target latency: <200ms for all responses
"""

import asyncio
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime

from super.core.voice.workflows.dual_agent.task_queue import TaskQueue, Task, TaskType
from super.core.voice.workflows.dual_agent.context_aggregator import (
    ContextAggregator,
    ConversationNode,
    NodeType,
    ConversationPhase
)


class CommunicationAgent:
    """
    Real-time conversation flow manager.

    Responsibilities:
    - Maintain conversation flow (Pipecat-flows integration)
    - Check task queue for pending tasks
    - Provide filler messages during processing
    - Handle simple Q&A from cached context
    - Delegate complex queries to Processing Agent
    - Implement 90% TTS overlap rule
    """

    def __init__(
        self,
        session_id: str,
        context: ContextAggregator,
        task_queue: TaskQueue,
        conversation_flow: List[ConversationNode]
    ):
        self.session_id = session_id
        self.context = context
        self.task_queue = task_queue
        self.conversation_flow = conversation_flow

        # Agent state
        self._is_running = False
        self._current_task_id: Optional[str] = None
        self._last_check_time = datetime.now()

        # Filler messages for different task types
        self._filler_messages = {
            TaskType.KB_SEARCH: "Let me search that for you...",
            TaskType.DB_QUERY: "I'm looking up that information...",
            TaskType.ELIGIBILITY_CHECK: "Let me check that for you...",
            TaskType.API_CALL: "I'm checking the system...",
            TaskType.COMPUTE: "Give me a moment to process that..."
        }

    async def start(self):
        """Initialize and start the communication agent"""
        self._is_running = True
        await self.context.set_conversation_flow(self.conversation_flow)

        # Start with first node
        if self.conversation_flow:
            await self.context.advance_to_node(self.conversation_flow[0].id)

    async def stop(self):
        """Stop the communication agent"""
        self._is_running = False

    async def process_user_input(self, user_message: str) -> Dict[str, Any]:
        """
        Process user input and determine next response.

        This is the main entry point called by the voice pipeline when
        user speaks or provides input.

        Args:
            user_message: User's spoken/typed message

        Returns:
            Response dict with:
            - type: "speak" | "wait" | "function_call" | "end"
            - content: Response text (for "speak")
            - action: Action to take
            - metadata: Additional info
        """
        # Check 90% TTS overlap rule
        can_proceed = await self.context.can_speak_next()
        if not can_proceed:
            return {
                "type": "wait",
                "reason": "tts_overlap",
                "message": "Waiting for TTS to reach 90% completion"
            }

        # Add user turn to context
        current_node = await self.context.get_current_node()
        await self.context.add_exchange(
            speaker="user",
            content=user_message,
            node_id=current_node.id if current_node else None
        )

        # Check if waiting for task completion
        if self._current_task_id:
            return await self._check_task_status()

        # Process based on current node type
        if not current_node:
            # No current node - likely conversation ended
            return await self._handle_end()

        if current_node.type == NodeType.INSTRUCTION:
            return await self._handle_instruction(current_node)

        elif current_node.type == NodeType.QUESTION:
            return await self._handle_question(current_node, user_message)

        elif current_node.type == NodeType.TOOL:
            return await self._handle_tool(current_node, user_message)

        elif current_node.type == NodeType.EXPLANATION:
            return await self._handle_explanation(current_node)

        elif current_node.type == NodeType.REACT:
            return await self._handle_react(current_node, user_message)

        else:
            return {"type": "error", "message": f"Unknown node type: {current_node.type}"}

    async def _handle_instruction(self, node: ConversationNode) -> Dict[str, Any]:
        """
        Handle INSTRUCTION node - Agent speaks, no user input needed.

        Args:
            node: Instruction conversation node

        Returns:
            Response to speak to user
        """
        # Add agent turn
        await self.context.add_exchange(
            speaker="agent",
            content=node.prompt,
            node_id=node.id
        )

        # Mark complete and advance
        await self.context.mark_node_complete(node.id)
        if node.next_node:
            await self.context.advance_to_node(node.next_node)

        return {
            "type": "speak",
            "content": node.prompt,
            "metadata": {
                "node_id": node.id,
                "node_type": "instruction",
                "auto_advance": True
            }
        }

    async def _handle_question(self, node: ConversationNode, user_message: str) -> Dict[str, Any]:
        """
        Handle QUESTION node - Agent asks, waits for user response.

        Extracts required information from user response and stores in context.

        Args:
            node: Question conversation node
            user_message: User's response

        Returns:
            Confirmation response or follow-up question
        """
        # Extract required fields from user message
        # In real implementation, use NER/LLM to extract
        # For now, simple placeholder
        extracted_data = await self._extract_user_data(user_message, node.required_fields)

        # Store in context
        for key, value in extracted_data.items():
            await self.context.update_user_attribute(key, value)

        # Check if all required fields collected
        collection_status = await self.context.check_required_fields(node.required_fields)
        all_collected = all(collection_status.values())

        if all_collected:
            # Confirm and advance
            confirmation = f"Got it! {', '.join(extracted_data.values())}"

            await self.context.add_exchange(
                speaker="agent",
                content=confirmation,
                node_id=node.id
            )

            await self.context.mark_node_complete(node.id)
            if node.next_node:
                await self.context.advance_to_node(node.next_node)

            return {
                "type": "speak",
                "content": confirmation,
                "metadata": {
                    "node_id": node.id,
                    "node_type": "question",
                    "collected_fields": list(extracted_data.keys())
                }
            }
        else:
            # Ask again for missing fields
            missing = [f for f, collected in collection_status.items() if not collected]
            follow_up = f"Could you provide your {', '.join(missing)}?"

            return {
                "type": "speak",
                "content": follow_up,
                "metadata": {
                    "node_id": node.id,
                    "node_type": "question",
                    "missing_fields": missing
                }
            }

    async def _handle_tool(self, node: ConversationNode, user_message: str) -> Dict[str, Any]:
        """
        Handle TOOL node - Delegate to Processing Agent via Task Queue.

        Args:
            node: Tool conversation node
            user_message: User's message (context for tool)

        Returns:
            Filler message while task executes
        """
        tool_config = node.tool_config or {}
        task_type = tool_config.get("type", "COMPUTE")
        query = tool_config.get("query", user_message)

        # Push task to queue
        task_id = await self.task_queue.push_task(
            task_type=task_type,
            query=query,
            priority="HIGH",  # User-facing tasks are high priority
            context={
                "node_id": node.id,
                "user_message": user_message,
                "collected_attributes": await self.context.get_collected_attributes()
            },
            filler_message=self._filler_messages.get(TaskType[task_type], "Processing..."),
            timeout_threshold=10000  # 10 seconds
        )

        self._current_task_id = task_id

        # Get filler message
        filler = self._filler_messages.get(TaskType[task_type], "Give me a moment...")

        await self.context.set_waiting_for_task(task_id, filler)
        await self.context.add_exchange(
            speaker="agent",
            content=filler,
            node_id=node.id
        )

        return {
            "type": "speak",
            "content": filler,
            "metadata": {
                "node_id": node.id,
                "node_type": "tool",
                "task_id": task_id,
                "waiting_for_result": True
            }
        }

    async def _handle_explanation(self, node: ConversationNode) -> Dict[str, Any]:
        """
        Handle EXPLANATION node - Explain results from previous tool execution.

        Args:
            node: Explanation conversation node

        Returns:
            Explanation response with tool results
        """
        # Get tool results from context
        tool_config = node.tool_config or {}
        tool_name = tool_config.get("tool_name")

        result = await self.context.get_cached_result(tool_name) if tool_name else None

        if result:
            # Format explanation with results
            explanation = node.prompt.format(result=result)
        else:
            explanation = node.prompt

        await self.context.add_exchange(
            speaker="agent",
            content=explanation,
            node_id=node.id
        )

        await self.context.mark_node_complete(node.id)
        if node.next_node:
            await self.context.advance_to_node(node.next_node)

        return {
            "type": "speak",
            "content": explanation,
            "metadata": {
                "node_id": node.id,
                "node_type": "explanation"
            }
        }

    async def _handle_react(self, node: ConversationNode, user_message: str) -> Dict[str, Any]:
        """
        Handle REACT node - Open-ended reasoning + action.

        For complex queries, delegate to Processing Agent.
        For simple queries, respond from cached context.

        Args:
            node: ReAct conversation node
            user_message: User's question

        Returns:
            Response or task delegation
        """
        # Check if query can be answered from cache
        cached_answer = await self._try_answer_from_cache(user_message)

        if cached_answer:
            # Quick response from cache (<200ms latency)
            await self.context.add_exchange(
                speaker="agent",
                content=cached_answer,
                node_id=node.id
            )

            return {
                "type": "speak",
                "content": cached_answer,
                "metadata": {
                    "node_id": node.id,
                    "node_type": "react",
                    "source": "cache"
                }
            }

        # Complex query - delegate to Processing Agent
        task_id = await self.task_queue.push_task(
            task_type="KB_SEARCH",
            query=user_message,
            priority="HIGH",
            context={
                "node_id": node.id,
                "conversation_history": [
                    turn.to_dict() for turn in await self.context.get_recent_context(3)
                ]
            },
            filler_message="Let me find that information for you...",
            timeout_threshold=10000
        )

        self._current_task_id = task_id

        filler = "Let me search that for you..."
        await self.context.set_waiting_for_task(task_id, filler)
        await self.context.add_exchange(
            speaker="agent",
            content=filler,
            node_id=node.id
        )

        return {
            "type": "speak",
            "content": filler,
            "metadata": {
                "node_id": node.id,
                "node_type": "react",
                "task_id": task_id,
                "waiting_for_result": True
            }
        }

    async def _check_task_status(self) -> Dict[str, Any]:
        """
        Check status of current task.

        If completed, return results. If still pending, return wait message.
        """
        if not self._current_task_id:
            return {"type": "error", "message": "No active task"}

        status = await self.task_queue.get_task_status(self._current_task_id)

        if status == "COMPLETED":
            # Get result
            result = await self.task_queue.get_task_result(self._current_task_id)

            # Cache result
            task = await self.task_queue.get_task(self._current_task_id)
            if task:
                await self.context.cache_tool_result(
                    tool_name=task.task_type.value,
                    result=result,
                    ttl_seconds=300
                )

            # Clear waiting state
            await self.context.clear_waiting_task()
            self._current_task_id = None

            # Format response
            response_text = self._format_result(result)

            current_node = await self.context.get_current_node()
            await self.context.add_exchange(
                speaker="agent",
                content=response_text,
                node_id=current_node.id if current_node else None,
                function_called=task.task_type.value
            )

            # Advance to next node if applicable
            if current_node and current_node.next_node:
                await self.context.mark_node_complete(current_node.id)
                await self.context.advance_to_node(current_node.next_node)

            return {
                "type": "speak",
                "content": response_text,
                "metadata": {
                    "task_completed": True,
                    "result": result
                }
            }

        elif status == "FAILED":
            # Handle failure
            task = await self.task_queue.get_task(self._current_task_id)
            error_msg = task.error if task else "Unknown error"

            await self.context.clear_waiting_task()
            self._current_task_id = None

            response = "I'm sorry, I encountered an issue. Could you try asking that again?"

            return {
                "type": "speak",
                "content": response,
                "metadata": {
                    "task_failed": True,
                    "error": error_msg
                }
            }

        else:
            # Still pending/in-progress
            # Check timeout
            task = await self.task_queue.get_task(self._current_task_id)
            if task and task.is_timed_out():
                # Timeout - provide fallback
                await self.context.clear_waiting_task()
                self._current_task_id = None

                response = "This is taking longer than expected. Let me help you with something else."

                return {
                    "type": "speak",
                    "content": response,
                    "metadata": {
                        "task_timeout": True
                    }
                }

            # Provide periodic filler if needed
            time_since_check = (datetime.now() - self._last_check_time).total_seconds()
            if time_since_check > 3:  # Every 3 seconds
                self._last_check_time = datetime.now()
                return {
                    "type": "speak",
                    "content": "Still working on that...",
                    "metadata": {
                        "task_status": status,
                        "filler": True
                    }
                }

            return {
                "type": "wait",
                "reason": "task_pending",
                "metadata": {
                    "task_id": self._current_task_id,
                    "status": status
                }
            }

    async def _handle_end(self) -> Dict[str, Any]:
        """Handle conversation end"""
        await self.context.update_phase(ConversationPhase.COMPLETED)

        return {
            "type": "end",
            "content": "Thank you for contacting us. Have a great day!",
            "metadata": {
                "conversation_ended": True
            }
        }

    async def _extract_user_data(
        self,
        user_message: str,
        required_fields: List[str]
    ) -> Dict[str, Any]:
        """
        Extract required data from user message.

        In production, use NER or LLM extraction.
        For now, simple placeholder.

        Args:
            user_message: User's message
            required_fields: Fields to extract

        Returns:
            Extracted data dict
        """
        # Placeholder - in real implementation:
        # - Use NER for entities
        # - Use LLM for complex extraction
        # - Validate extracted values

        return {field: user_message for field in required_fields}

    async def _try_answer_from_cache(self, query: str) -> Optional[str]:
        """
        Try to answer query from cached context.

        Returns:
            Cached answer or None if not found
        """
        # Check cached tool results
        # In production, use semantic similarity matching

        # Placeholder implementation
        return None

    def _format_result(self, result: Any) -> str:
        """
        Format tool result for user-friendly response.

        Args:
            result: Raw tool result

        Returns:
            Formatted response text
        """
        if isinstance(result, str):
            return result
        elif isinstance(result, dict):
            # Format dict results
            return str(result)
        else:
            return f"Here's what I found: {result}"

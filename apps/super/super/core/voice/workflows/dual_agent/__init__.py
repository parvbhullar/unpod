"""
Dual-Agent Architecture for Voice AI

Separates conversation flow (Communication Agent) from compute-intensive
operations (Processing Agent) for optimal latency and user experience.

Components:
- TaskQueue: Priority-based async task management
- ContextAggregator: Shared conversation state
- CommunicationAgent: Real-time conversation flow (<200ms latency)
- ProcessingAgent: Background task executor (500ms-5s operations)

Quick Start:
    from super.core.voice.workflows.dual_agent import (
        TaskQueue, ContextAggregator,
        CommunicationAgent, ProcessingAgent
    )

    # Initialize
    context = ContextAggregator(session_id)
    task_queue = TaskQueue()

    comm_agent = CommunicationAgent(session_id, context, task_queue, flow)
    proc_agent = ProcessingAgent(session_id, context, task_queue, tools)

    # Start
    await comm_agent.start()
    await proc_agent.start()

    # Process user input
    response = await comm_agent.process_user_input("Hello")
"""

from super.core.voice.workflows.dual_agent.task_queue import (
    TaskQueue,
    Task,
    TaskPriority,
    TaskStatus,
    TaskType
)

from super.core.voice.workflows.dual_agent.context_aggregator import (
    ContextAggregator,
    ConversationContext,
    ConversationNode,
    ConversationTurn,
    NodeType,
    ConversationPhase
)

from super.core.voice.workflows.dual_agent.communication_agent import CommunicationAgent
from super.core.voice.workflows.dual_agent.processing_agent import ProcessingAgent, LangGraphProcessingAgent


__all__ = [
    # Task Queue
    "TaskQueue",
    "Task",
    "TaskPriority",
    "TaskStatus",
    "TaskType",

    # Context Aggregator
    "ContextAggregator",
    "ConversationContext",
    "ConversationNode",
    "ConversationTurn",
    "NodeType",
    "ConversationPhase",

    # Agents
    "CommunicationAgent",
    "ProcessingAgent",
    "LangGraphProcessingAgent"
]

"""
Integration Example - Dual Agent Architecture

This example demonstrates how to wire together:
- Context Aggregator
- Task Queue
- Communication Agent
- Processing Agent

For a complete voice agent conversation flow.
"""

import asyncio
from typing import Any, Dict
import uuid

from super.core.voice.workflows.dual_agent.task_queue import TaskQueue
from super.core.voice.workflows.dual_agent.context_aggregator import (
    ContextAggregator,
    ConversationNode,
    NodeType,
    ConversationPhase
)
from super.core.voice.workflows.dual_agent.communication_agent import CommunicationAgent
from super.core.voice.workflows.dual_agent.processing_agent import ProcessingAgent


# ==================== Mock Tools ====================

async def search_docs(query: str) -> str:
    """Mock knowledge base search"""
    await asyncio.sleep(1)  # Simulate search latency
    return f"Found information about: {query}"


async def query_database(query: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Mock database query"""
    await asyncio.sleep(0.8)
    return {
        "status": "success",
        "data": {"result": f"Database result for: {query}"}
    }


async def check_eligibility(user_data: Dict[str, Any], criteria: str) -> Dict[str, bool]:
    """Mock eligibility check"""
    await asyncio.sleep(0.5)
    return {
        "eligible": True,
        "reason": "All criteria met"
    }


async def call_api(endpoint: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Mock external API call"""
    await asyncio.sleep(1.2)
    return {
        "status": 200,
        "response": f"API response from {endpoint}"
    }


async def compute(task: str, context: Dict[str, Any]) -> Any:
    """Mock heavy computation"""
    await asyncio.sleep(2)
    return f"Computed result for: {task}"


# ==================== Conversation Flow Definition ====================

def define_conversation_flow() -> list[ConversationNode]:
    """
    Define the conversation flow structure.

    This example shows a typical student support conversation:
    1. Greeting
    2. Collect name
    3. Search knowledge base
    4. Explain results
    5. Open-ended Q&A
    6. Closing
    """
    return [
        # Node 1: Greeting (Instruction)
        ConversationNode(
            id="greeting",
            type=NodeType.INSTRUCTION,
            prompt="Hello! I'm Saanvi from Vajirao & Ravi. How can I help you today?",
            next_node="ask_name"
        ),

        # Node 2: Collect Name (Question)
        ConversationNode(
            id="ask_name",
            type=NodeType.QUESTION,
            prompt="What's your name?",
            required_fields=["name"],
            next_node="ask_course_interest"
        ),

        # Node 3: Collect Course Interest (Question)
        ConversationNode(
            id="ask_course_interest",
            type=NodeType.QUESTION,
            prompt="Which course are you interested in?",
            required_fields=["course_interest"],
            next_node="search_course_info"
        ),

        # Node 4: Search Course Information (Tool)
        ConversationNode(
            id="search_course_info",
            type=NodeType.TOOL,
            prompt="",  # No prompt - agent will speak filler message
            tool_config={
                "type": "KB_SEARCH",
                "query": "course information"
            },
            next_node="explain_course_info"
        ),

        # Node 5: Explain Results (Explanation)
        ConversationNode(
            id="explain_course_info",
            type=NodeType.EXPLANATION,
            prompt="Based on what I found: {result}",
            tool_config={
                "tool_name": "kb_search"
            },
            next_node="open_qa"
        ),

        # Node 6: Open-ended Q&A (React)
        ConversationNode(
            id="open_qa",
            type=NodeType.REACT,
            prompt="Do you have any other questions?",
            next_node="closing"
        ),

        # Node 7: Closing (Instruction)
        ConversationNode(
            id="closing",
            type=NodeType.INSTRUCTION,
            prompt="Thank you for contacting us! Have a great day!",
            next_node=None  # End of conversation
        )
    ]


# ==================== System Initialization ====================

async def initialize_dual_agent_system(session_id: str) -> tuple:
    """
    Initialize the complete dual-agent system.

    Returns:
        Tuple of (context, task_queue, comm_agent, proc_agent)
    """
    # 1. Create shared infrastructure
    context = ContextAggregator(session_id)
    task_queue = TaskQueue()

    # 2. Define conversation flow
    conversation_flow = define_conversation_flow()
    await context.set_conversation_flow(conversation_flow)

    # 3. Register tools for Processing Agent
    tools = {
        "search_docs": search_docs,
        "query_database": query_database,
        "check_eligibility": check_eligibility,
        "call_api": call_api,
        "compute": compute
    }

    # 4. Create agents
    comm_agent = CommunicationAgent(
        session_id=session_id,
        context=context,
        task_queue=task_queue,
        conversation_flow=conversation_flow
    )

    proc_agent = ProcessingAgent(
        session_id=session_id,
        context=context,
        task_queue=task_queue,
        tools=tools
    )

    # 5. Start agents
    await comm_agent.start()
    await proc_agent.start()

    print(f"✅ Dual-agent system initialized for session: {session_id}")

    return context, task_queue, comm_agent, proc_agent


# ==================== Example Usage ====================

async def simulate_conversation():
    """
    Simulate a complete conversation flow.

    This demonstrates how the dual-agent architecture handles:
    - Real-time conversation (<200ms latency)
    - Background task execution (500ms-2s)
    - Async communication via Task Queue
    - Shared state via Context Aggregator
    """
    print("\n" + "="*80)
    print("DUAL-AGENT ARCHITECTURE - CONVERSATION SIMULATION")
    print("="*80 + "\n")

    # Initialize system
    session_id = str(uuid.uuid4())
    context, task_queue, comm_agent, proc_agent = await initialize_dual_agent_system(session_id)

    # Simulate conversation turns
    conversation_turns = [
        ("system", "START"),  # Triggers greeting
        ("user", "Hi"),
        ("user", "My name is Rahul"),
        ("user", "I'm interested in UPSC CSE preparation"),
        ("user", "What are the course timings?"),
        ("user", "What's the fee structure?"),
        ("user", "No more questions, thanks")
    ]

    for speaker, message in conversation_turns:
        print(f"\n{'='*80}")
        print(f"[{speaker.upper()}]: {message}")
        print(f"{'='*80}")

        if speaker == "system":
            # System message - just trigger initial state
            continue

        # Process user input
        response = await comm_agent.process_user_input(message)

        print(f"\n[Response Type]: {response.get('type')}")

        if response["type"] == "speak":
            print(f"[AGENT SPEAKS]: {response.get('content')}")
            print(f"[Metadata]: {response.get('metadata', {})}")

            # Check if waiting for task
            if response.get("metadata", {}).get("waiting_for_result"):
                task_id = response["metadata"]["task_id"]
                print(f"\n⏳ Waiting for task {task_id} to complete...")

                # Poll for task completion
                max_wait = 30  # 30 seconds max
                waited = 0
                while waited < max_wait:
                    await asyncio.sleep(0.5)
                    waited += 0.5

                    status = await task_queue.get_task_status(task_id)
                    if status in ["COMPLETED", "FAILED"]:
                        print(f"✅ Task completed with status: {status}")

                        # Get final response
                        final_response = await comm_agent.process_user_input("")
                        if final_response["type"] == "speak":
                            print(f"[AGENT SPEAKS]: {final_response.get('content')}")
                        break

        elif response["type"] == "wait":
            print(f"[WAITING]: {response.get('reason')}")

        elif response["type"] == "end":
            print(f"[CONVERSATION ENDED]: {response.get('content')}")
            break

        # Show context stats
        stats = await context.get_stats()
        print(f"\n📊 Context Stats:")
        print(f"   Phase: {stats['phase']}")
        print(f"   Completed nodes: {stats['completed_nodes']}/{stats['completed_nodes'] + stats['pending_nodes']}")
        print(f"   Collected attributes: {stats['collected_attributes']}")

        # Show queue stats
        queue_stats = await task_queue.get_queue_stats()
        print(f"\n📊 Queue Stats:")
        print(f"   Total tasks: {queue_stats['total']}")
        print(f"   Pending: {queue_stats['pending']}")
        print(f"   Completed: {queue_stats['completed']}")

        # Small delay between turns
        await asyncio.sleep(0.5)

    # Cleanup
    await comm_agent.stop()
    await proc_agent.stop()

    print("\n" + "="*80)
    print("CONVERSATION SIMULATION COMPLETE")
    print("="*80 + "\n")


# ==================== Main Entry Point ====================

async def main():
    """Main entry point"""
    try:
        await simulate_conversation()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

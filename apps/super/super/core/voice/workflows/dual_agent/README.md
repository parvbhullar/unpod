# Dual-Agent Architecture

Separates conversation flow from compute-intensive operations for optimal latency and user experience in voice AI agents.

## Architecture Overview

```
Communication Agent (Pipecat-flows) ←→ Task Queue ←→ Processing Agent (LangGraph)
                ↕                                              ↕
        Context Aggregator (Shared State)
```

## Key Components

### 1. Context Aggregator
Single source of truth for conversation state.

```python
from super.core.voice.workflows.dual_agent import ContextAggregator

context = ContextAggregator(session_id="abc-123")

# Update user data
await context.update_user_attribute("name", "Rahul")

# Track conversation flow
await context.advance_to_node("ask_course")

# Add conversation history
await context.add_exchange(speaker="user", content="I'm interested in UPSC")
```

### 2. Task Queue
Priority-based async task management between agents.

```python
from super.core.voice.workflows.dual_agent import TaskQueue

task_queue = TaskQueue()

# Communication Agent: Push task
task_id = await task_queue.push_task(
    task_type="KB_SEARCH",
    query="What courses do you offer?",
    priority="HIGH",
    filler_message="Let me search that for you..."
)

# Processing Agent: Get pending tasks
pending = await task_queue.get_pending_tasks(limit=5)

# Processing Agent: Mark complete
await task_queue.complete_task(task_id, result="We offer 3 courses...")
```

### 3. Communication Agent
Real-time conversation flow handler (target <200ms latency).

```python
from super.core.voice.workflows.dual_agent import CommunicationAgent, ConversationNode, NodeType

# Define conversation flow
flow = [
    ConversationNode(
        id="greeting",
        type=NodeType.INSTRUCTION,
        prompt="Hello! I'm Saanvi. How can I help?",
        next_node="ask_name"
    ),
    ConversationNode(
        id="ask_name",
        type=NodeType.QUESTION,
        prompt="What's your name?",
        required_fields=["name"],
        next_node="search_courses"
    ),
    ConversationNode(
        id="search_courses",
        type=NodeType.TOOL,
        tool_config={"type": "KB_SEARCH", "query": "course list"},
        next_node="explain_courses"
    )
]

# Create agent
comm_agent = CommunicationAgent(
    session_id=session_id,
    context=context,
    task_queue=task_queue,
    conversation_flow=flow
)

await comm_agent.start()

# Process user input
response = await comm_agent.process_user_input("My name is Rahul")
print(response["content"])  # "Got it! Rahul"
```

### 4. Processing Agent
Background task executor for compute-intensive operations.

```python
from super.core.voice.workflows.dual_agent import ProcessingAgent

# Define tools
async def search_docs(query: str) -> str:
    # Semantic search implementation
    return "Found: UPSC CSE course details..."

async def query_db(query: str, context: dict) -> dict:
    # Database query implementation
    return {"courses": [...]}

tools = {
    "search_docs": search_docs,
    "query_database": query_db
}

# Create agent
proc_agent = ProcessingAgent(
    session_id=session_id,
    context=context,
    task_queue=task_queue,
    tools=tools
)

await proc_agent.start()  # Starts polling loop
```

## Complete Example

```python
import asyncio
from super.core.voice.workflows.dual_agent import (
    TaskQueue, ContextAggregator,
    CommunicationAgent, ProcessingAgent,
    ConversationNode, NodeType
)

async def main():
    session_id = "session-123"

    # 1. Create shared infrastructure
    context = ContextAggregator(session_id)
    task_queue = TaskQueue()

    # 2. Define conversation flow
    flow = [
        ConversationNode(
            id="greeting",
            type=NodeType.INSTRUCTION,
            prompt="Hello! How can I help?",
            next_node="open_qa"
        ),
        ConversationNode(
            id="open_qa",
            type=NodeType.REACT,
            prompt="Ask me anything!",
            next_node=None
        )
    ]

    # 3. Define tools
    async def search_docs(query: str) -> str:
        await asyncio.sleep(1)  # Simulate search
        return f"Found info about: {query}"

    tools = {"search_docs": search_docs}

    # 4. Create agents
    comm_agent = CommunicationAgent(session_id, context, task_queue, flow)
    proc_agent = ProcessingAgent(session_id, context, task_queue, tools)

    # 5. Start agents
    await comm_agent.start()
    await proc_agent.start()

    # 6. Process user input
    response = await comm_agent.process_user_input("What courses do you offer?")
    print(response["content"])  # "Let me search that for you..."

    # Wait for task completion
    await asyncio.sleep(2)

    response = await comm_agent.process_user_input("")
    print(response["content"])  # "Found info about: What courses..."

    # 7. Cleanup
    await comm_agent.stop()
    await proc_agent.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

## Node Types

### INSTRUCTION
Agent speaks, no user input needed.
```python
ConversationNode(
    id="welcome",
    type=NodeType.INSTRUCTION,
    prompt="Welcome to Vajirao & Ravi!",
    next_node="ask_name"
)
```

### QUESTION
Agent asks, waits for user response.
```python
ConversationNode(
    id="ask_name",
    type=NodeType.QUESTION,
    prompt="What's your name?",
    required_fields=["name"],
    next_node="next_step"
)
```

### TOOL
Execute tool via Processing Agent.
```python
ConversationNode(
    id="search",
    type=NodeType.TOOL,
    tool_config={
        "type": "KB_SEARCH",
        "query": "course information"
    },
    next_node="explain_results"
)
```

### EXPLANATION
Explain tool results.
```python
ConversationNode(
    id="explain_results",
    type=NodeType.EXPLANATION,
    prompt="Based on what I found: {result}",
    tool_config={"tool_name": "kb_search"},
    next_node="next_step"
)
```

### REACT
Open-ended reasoning + action.
```python
ConversationNode(
    id="open_qa",
    type=NodeType.REACT,
    prompt="Do you have any questions?",
    next_node="closing"
)
```

## Features

✅ **Separation of Concerns**: Conversation flow separate from compute operations
✅ **Low Latency**: Communication Agent responds in <200ms
✅ **Async Task Execution**: Processing Agent handles 500ms-5s operations in background
✅ **Priority Queue**: High-priority user queries processed first
✅ **Shared State**: Both agents read/write to Context Aggregator
✅ **90% TTS Overlap**: Allows next response when TTS 90% complete
✅ **Filler Messages**: Agent provides context-aware filler during processing
✅ **Timeout Handling**: Graceful degradation for slow operations
✅ **Tool Registration**: Dynamic tool registration at runtime
✅ **Conversation History**: Sliding window of last N turns
✅ **Result Caching**: Cache tool results with TTL

## Architecture Benefits

### Communication Agent
- **Always responsive** (<200ms)
- Handles conversation flow
- Provides filler messages during processing
- Implements 90% TTS overlap rule
- Simple Q&A from cache

### Processing Agent
- **Non-blocking** background execution
- Polls Task Queue every 500ms
- Executes compute-intensive tasks
- Updates results in real-time
- Handles timeouts gracefully

### Task Queue
- **Priority-based** (HIGH, MEDIUM, LOW)
- Thread-safe via asyncio locks
- Task lifecycle: PENDING → IN_PROGRESS → COMPLETED/FAILED
- Timeout detection
- Auto-cleanup of old tasks

### Context Aggregator
- **Single source of truth**
- Conversation flow tracking
- User attribute collection
- Recent exchange history (sliding window)
- Tool result caching
- TTS state management

## Latency Optimization

The dual-agent architecture achieves target latencies:

- **Communication Agent**: <200ms (immediate responses)
- **Processing Agent**: 500ms-5s (background execution)
- **Task Queue**: <10ms overhead
- **Context Aggregator**: <5ms read/write

Total user-perceived latency: **<200ms** (Communication Agent response time)

## See Also

- [Architecture Document](../../../../../docs/dual_agent_architecture.md) - Complete design specs
- [Integration Example](integration_example.py) - Full working example
- [Task Queue](task_queue.py) - Task management implementation
- [Context Aggregator](context_aggregator.py) - Shared state implementation

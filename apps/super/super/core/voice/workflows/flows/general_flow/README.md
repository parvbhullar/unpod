# Active and Passive Agent Architecture

This directory contains the implementation of an **active and passive agent architecture** for Pipecat voice pipelines.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Pipecat Pipeline                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────┐        ┌──────────────────────┐         │
│  │ Active Agent  │───────▶│    Task Queue        │         │
│  │  (Flow Node)  │ pushes │  (handler.task_queue)│         │
│  └───────────────┘        └──────────────────────┘         │
│         │                           │                       │
│         │                           │                       │
│         │                           ▼                       │
│         │                  ┌──────────────────────┐         │
│         │                  │  Passive Agent       │         │
│         │                  │ (QueueProcessor)     │         │
│         │                  │                      │         │
│         │                  │ - Monitors queue     │         │
│         │                  │ - Processes tasks    │         │
│         │                  │ - Updates results    │         │
│         │                  └──────────────────────┘         │
│         │                                                   │
│    Conversations                Background Processing       │
│    with User                    (Non-blocking)              │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Active Agent (`active_node.py`)

**Purpose**: Handles direct user conversation and pushes tasks to the queue.

**Key Features**:
- Uses Pipecat Flows `NodeConfig` for conversational flow
- Exposes `push_to_queue` tool to LLM
- Creates `PipelineTasks` and adds them to `handler.task_queue`
- Never blocks on task execution

**Example Task Creation**:
```python
task = PipelineTasks(
    assignee="communication agent",
    task_name="search_docs",
    task_description="Search knowledge base for UPSC courses",
    task_status="pending"
)
handler.task_queue.append(task)
```

### 2. Passive Agent (`queue_processor.py`)

**Purpose**: Background frame processor that monitors and processes tasks from the queue.

**Key Features**:
- Extends `FrameProcessor` for Pipecat integration
- Runs background loop checking queue every N seconds (configurable)
- Processes tasks concurrently (up to `max_concurrent_tasks`)
- Updates task status (`pending` → `processing` → `completed`/`failed`)
- **Non-blocking**: Does not interfere with main conversation pipeline

**Configuration**:
```python
processor = TaskQueueProcessor(
    handler=handler,
    processing_interval=2.0,      # Check queue every 2 seconds
    max_concurrent_tasks=3         # Process up to 3 tasks at once
)
```

### 3. Task Data Model (`PipelineTasks`)

```python
@dataclass
class PipelineTasks:
    assignee: str                  # Who should process this task
    task_name: str                 # Task identifier
    task_description: str          # Detailed description
    task_status: str               # pending|processing|completed|failed
    task_result: Optional[str]     # Result after processing
```

## How It Works

### Flow Diagram

```
┌──────────┐
│   User   │ "Can you search for UPSC courses?"
└────┬─────┘
     │
     ▼
┌─────────────────────┐
│  Active Agent       │
│  (LLM + Flows)      │
│                     │
│  1. Understands     │
│     user request    │
│  2. Calls           │
│     push_to_queue() │
│  3. Responds:       │
│     "Sure, let me   │
│      check that"    │
└──────────┬──────────┘
           │
           ▼
    ┌──────────────┐
    │  task_queue  │ [PipelineTasks(pending)]
    └──────┬───────┘
           │
           │ (Background loop every 2s)
           │
           ▼
    ┌─────────────────────┐
    │  Passive Agent      │
    │  (QueueProcessor)   │
    │                     │
    │  1. Detects pending │
    │  2. Executes KB     │
    │     search          │
    │  3. Updates result  │
    └─────────────────────┘
           │
           ▼
    ┌──────────────┐
    │  task_queue  │ [PipelineTasks(completed, result="...")]
    └──────────────┘
```

### Execution Flow

1. **User makes a request** during conversation
2. **Active agent (LLM)** decides to delegate to background processing
3. **Active agent** calls `push_to_queue` tool with task details
4. **Task added** to `handler.task_queue` with status `pending`
5. **Active agent responds** to user immediately (non-blocking)
6. **Passive agent (QueueProcessor)** detects task in next loop iteration
7. **Passive agent** changes status to `processing`
8. **Passive agent** executes task (e.g., KB search, API call)
9. **Passive agent** updates task with result and status `completed`
10. **Active agent** can check queue in next conversation turn and use results

## Integration in Pipecat Pipeline

The passive agent is integrated as a **FrameProcessor** in the Pipecat pipeline:

### Location in `pipecat_handler.py`

```python
# Initialize QueueProcessor (line ~1743)
self.queue_processor = TaskQueueProcessor(
    handler=self,
    processing_interval=2.0,
    max_concurrent_tasks=3
)

# Add to pipeline (line ~1823)
pipeline_stages.append(ParallelPipeline(
    [
        context_aggregator.user(),
        llm_service
    ],
    [
        transcript.user()
    ],
    [
        self.queue_processor  # Passive agent in parallel
    ]
))
```

### Why ParallelPipeline?

- **Non-blocking**: Queue processing runs in parallel with LLM
- **No interference**: Doesn't affect conversation latency
- **Automatic lifecycle**: Starts/stops with pipeline

## Customizing Task Handlers

The `TaskQueueProcessor` includes built-in handlers for common tasks. You can extend it:

### Method 1: Override `_execute_task`

```python
from super.core.voice.workflows.flows.general_flow.queue_processor import TaskQueueProcessor

class CustomQueueProcessor(TaskQueueProcessor):
    async def _execute_task(self, task):
        if task.task_name == "send_email":
            return await self._handle_send_email(task)
        elif task.task_name == "call_api":
            return await self._handle_api_call(task)
        else:
            return await super()._execute_task(task)

    async def _handle_send_email(self, task):
        # Your custom email logic
        return "Email sent successfully"

    async def _handle_api_call(self, task):
        # Your custom API logic
        return "API call completed"
```

### Method 2: Register Custom Handlers

```python
# Add to handler
handler.custom_task_handlers = {
    "send_email": self.send_email_task,
    "call_api": self.call_api_task,
}
```

### Built-in Handlers

1. **KB Search**: Tasks containing "search", "find", "query", "kb", "knowledge"
2. **Fetch Docs**: Tasks with "fetch" or "get_docs"
3. **Custom**: Checks `handler.custom_task_handlers` dictionary

## Monitoring Queue Status

Get real-time queue statistics:

```python
status = handler.queue_processor.get_queue_status()
# Returns:
# {
#     "total": 10,
#     "pending": 3,
#     "processing": 2,
#     "completed": 4,
#     "failed": 1,
#     "active_background_tasks": 2
# }
```

## Best Practices

### 1. Task Naming Conventions

Use clear, descriptive task names:

```python
# Good ✅
task_name = "search_kb_upsc_courses"
task_name = "fetch_user_profile"
task_name = "send_confirmation_email"

# Bad ❌
task_name = "task1"
task_name = "do_stuff"
```

### 2. Task Descriptions

Provide detailed descriptions for complex tasks:

```python
task_description = "Search knowledge base for UPSC courses related to Vajiram & Ravi, filter by online mode, and return top 3 results"
```

### 3. Error Handling

The processor automatically handles errors and sets `task_status = "failed"` with error in `task_result`.

### 4. Concurrency Limits

Adjust based on your workload:

```python
# Light processing
max_concurrent_tasks=2

# Heavy processing
max_concurrent_tasks=5

# Very light (sequential)
max_concurrent_tasks=1
```

### 5. Processing Interval

Balance responsiveness vs resource usage:

```python
# Fast response (high CPU usage)
processing_interval=0.5

# Balanced
processing_interval=2.0

# Low resource usage
processing_interval=5.0
```

## Example Usage

### Complete Example: Search + Respond Flow

```python
# 1. User asks question
User: "Can you find information about UPSC courses?"

# 2. Active agent pushes task
Active Agent LLM calls push_to_queue({
    "task_name": "search_upsc_courses",
    "task_description": "Search knowledge base for UPSC course information"
})

# 3. Active agent responds immediately
Active Agent: "Sure! Let me search our knowledge base. Give me a few moments."

# 4. Passive agent processes (background)
QueueProcessor:
  - Detects task
  - Executes handler.get_docs("UPSC course information")
  - Updates task with results

# 5. Active agent checks queue in next turn
User: "Did you find anything?"
Active Agent checks task_queue, finds completed task, uses result:
"Yes! Here's what I found: [uses task_result]"
```

## Troubleshooting

### Tasks Not Processing

**Symptoms**: Tasks stay in `pending` state

**Solutions**:
1. Check if `queue_processor` is added to pipeline
2. Verify `processing_interval` isn't too long
3. Check logs for errors in `_process_queue_loop`

### Slow Processing

**Symptoms**: Tasks taking too long

**Solutions**:
1. Reduce `processing_interval`
2. Increase `max_concurrent_tasks`
3. Optimize task handlers

### Pipeline Not Starting

**Symptoms**: QueueProcessor never runs

**Solutions**:
1. Ensure processor is in `ParallelPipeline`
2. Check `start()` is called when pipeline starts
3. Verify no exceptions in `process_frame`

## Advanced Configuration

### Custom Processing Loop

Override `_process_queue_loop` for custom behavior:

```python
async def _process_queue_loop(self):
    while self._running:
        # Custom logic here
        pending_tasks = [t for t in self.handler.task_queue if t.task_status == "pending"]

        # Priority queue logic
        high_priority = [t for t in pending_tasks if t.assignee == "urgent"]

        for task in high_priority:
            await self._process_task(task)

        await asyncio.sleep(self.processing_interval)
```

### Task Lifecycle Hooks

Add hooks for monitoring:

```python
class MonitoredQueueProcessor(TaskQueueProcessor):
    async def _process_task(self, task):
        # Before processing
        await self.on_task_start(task)

        try:
            result = await super()._process_task(task)
            # On success
            await self.on_task_success(task, result)
            return result
        except Exception as e:
            # On failure
            await self.on_task_failure(task, e)
            raise

    async def on_task_start(self, task):
        print(f"⏳ Starting: {task.task_name}")

    async def on_task_success(self, task, result):
        print(f"✅ Completed: {task.task_name}")

    async def on_task_failure(self, task, error):
        print(f"❌ Failed: {task.task_name} - {error}")
```

## Files Reference

| File | Purpose |
|------|---------|
| `active_node.py` | Active agent flow node (conversation + push to queue) |
| `passive_node.py` | Legacy passive node (now deprecated, use QueueProcessor) |
| `queue_processor.py` | Passive agent frame processor (background task execution) |
| `README.md` | This documentation |

## Further Reading

- **Pipecat Docs**: https://docs.pipecat.ai/
- **Pipecat Flows**: https://docs.pipecat.ai/flows/
- **Frame Processors**: https://docs.pipecat.ai/processors/
# Voice Task Orchestration with Temporal

This directory contains the Temporal workflow implementation for voice task processing.

## Architecture

The implementation consists of:

1. **Workflows** (`workflows.py`): Defines the `VoiceTaskWorkflow` that orchestrates voice call execution
2. **Activities** (`activities.py`): Contains the `execute_call_activity` that performs the actual call execution
3. **Worker** (`worker.py`): Runs the Temporal worker that processes workflows and activities
4. **Consumer** (`../consumers/voice_task_consumer.py`): Kafka consumer that triggers workflows

## Setup

### Prerequisites

1. Install Temporal SDK:
```bash
pip install temporalio
```

2. Start Temporal server (local development):
```bash
# Using Docker
docker run -d -p 7233:7233 temporalio/auto-setup:latest
```

### Environment Variables

Configure these environment variables:

```bash
# Temporal Configuration
TEMPORAL_ADDRESS=localhost:7233          # Temporal server address
TEMPORAL_NAMESPACE=default               # Temporal namespace
VOICE_TASK_QUEUE=voice-task-queue       # Task queue name

# Kafka Configuration (existing)
AGENT_OUTBOUND_REQUEST_TOPIC=agent_outbound_requests
AGENT_OUTBOUND_REQUEST_GROUP=agent_outbound_requests_group
```

## Running the Services

### 1. Start Temporal Worker

The worker must be running to process workflows:

```bash
python -m super_services.voice.workflows.worker
```

### 2. Start Kafka Consumer

The consumer listens for voice tasks and triggers workflows:

```bash
python -m super_services.voice.consumers.voice_task_consumer
```

## How It Works

1. **Task Submission**: Tasks are published to Kafka topic (`agent_outbound_requests`)
2. **Consumer**: Kafka consumer receives the message and triggers a Temporal workflow
3. **Workflow**: `VoiceTaskWorkflow` orchestrates the execution with retry policies
4. **Activity**: `execute_call_activity` performs the actual call using the appropriate provider (VAPI/LiveKit)
5. **Result Handling**: Workflow waits for completion and updates task status in database

## Benefits of Temporal

- **Reliability**: Automatic retries with configurable policies
- **Durability**: Workflow state persisted across failures
- **Visibility**: Built-in UI for monitoring workflow execution
- **Scalability**: Horizontal scaling of workers
- **Timeout Management**: Configurable timeouts at workflow and activity levels

## Workflow Configuration

The workflow includes:
- **Activity Timeout**: 15 minutes (for long-running calls)
- **Retry Policy**:
  - Initial interval: 10 seconds
  - Maximum interval: 1 minute
  - Maximum attempts: 3
  - Non-retryable errors: `ValueError` (provider selection failures)

## Monitoring

Access Temporal Web UI:
```
http://localhost:8233
```

View:
- Workflow execution history
- Failed workflows
- Retry attempts
- Activity logs

## Fallback to Legacy Mode

The consumer includes a `_process_task_legacy()` method that bypasses Temporal for direct execution. This can be used as a fallback if Temporal is unavailable.

To use legacy mode, replace `process_task` call with `_process_task_legacy` in the consumer.

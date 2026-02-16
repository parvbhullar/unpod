from pipecat_flows import (
    FlowArgs,
    FlowResult,
    FlowsFunctionSchema,
    NodeConfig,
)
import os
from dotenv import load_dotenv
import asyncio

from super.core.handler import BaseHandler
from super.core.logging.logging import print_log
from super.core.memory.search.schema import SearchDoc

# Import from passive_node to ensure consistency
from super.core.voice.workflows.flows.general_flow.passive_node import PipelineTasks

load_dotenv(verbose=True)

def conversation_node(handler: BaseHandler) -> NodeConfig:

    async def push_to_queue(args):

        print_log("adding task to task queue")
        task = PipelineTasks(
            assignee = "communication agent",
            task_name = args['task_name'],
            task_description = args['task_description'],
            task_status = "pending"
        )

        handler.task_queue.append(task)

        # Record metrics
        if hasattr(handler, 'metrics'):
            handler.metrics.record_task_created(task)
            handler.metrics.snapshot_queue_depth(len(handler.task_queue))

        return task.to_serializable_dict(), conversation_node(handler)


    queue_checker = FlowsFunctionSchema(
        name="push_to_queue",
        handler=push_to_queue,
        description="push tasks for Passive agent in queue with status pending",
        properties={
            "task_name": {
                "type": "string",
                "description": "name of the task",
            },
            "task_description": {
                "type": "string",
                "description": "description of what to perform in a task",
            }
        },
        required=["task_name"],
    )

    async def check_task_status(args):
        """
        Check task status. Returns completed tasks immediately without blocking.
        This is a non-blocking check - returns current state only.
        """
        task_name_filter = args.get('task_name', None)

        # Return all completed tasks (or specific task if filter provided)
        task_details = []
        for task in handler.task_queue:
            # If filter provided, only return that specific task (regardless of status)
            if task_name_filter and task.task_name == task_name_filter:
                task_details.append(task.to_serializable_dict())
            # Otherwise return all completed tasks
            elif not task_name_filter and task.task_status in ["done", "failed", "timeout"]:
                task_details.append(task.to_serializable_dict())

        return task_details, conversation_node(handler)

    check_task_status = FlowsFunctionSchema(
        name="check_task_status",
        handler=check_task_status,
        description="NON-BLOCKING: instantly check current status of tasks in the queue. Returns completed tasks immediately without waiting. Use this frequently to check if background tasks have finished.",
        properties={
            "task_name": {
                "type": "string",
                "description": "(optional) specific task name to check status for. If provided, returns only that task's current status (pending/processing/done). If not provided, returns all completed tasks.",
            }
        },
        required =[]
    )

    return NodeConfig(
        name="conversational_node",
        role_messages=[
            {
                "role": "system",
                "content": f"""
                    {handler.sections.identity.content if handler.sections.identity else None}

                    ## Your Role - Active Communication Agent
                    You are the primary conversational interface for users. Your job is to maintain engaging, natural conversations while delegating background tasks to the Passive Agent.

                    ## Task Queue Status
                    Current tasks: {handler.task_queue}

                    ## CRITICAL: NEVER GO SILENT
                    - ALWAYS respond to the user immediately, even if a task is still pending
                    - NEVER wait silently for task completion
                    - If you create a task, respond to the user RIGHT AWAY with engaging conversation
                    - If you check task status and it's still "pending" or "processing", continue the conversation naturally without mentioning this
                    - The user should NEVER experience silence or waiting

                    ## Core Responsibilities
                    1. KEEP CONVERSATION ALIVE: Always maintain smooth, natural conversation flow - NEVER let the user wait in silence
                    2. DELEGATE TASKS: When user asks queries requiring knowledge base lookup, use push_to_queue tool to create background tasks
                    3. CHECK TASK STATUS NON-BLOCKING: Use check_task_status to peek at results, but NEVER wait for them
                    4. RESPOND IMMEDIATELY: After creating a task with push_to_queue, respond to user IMMEDIATELY with engaging conversation
                    5. NEVER REVEAL INTERNAL OPERATIONS: Don't mention "tasks", "queue", "passive agent", "checking", "fetching", "gathering information", or any system processes
                    6. HANDLE PENDING TASKS GRACEFULLY: If task is still pending when you check, engage user with follow-up questions or related topics
                    7. USE COMPLETED RESULTS: When check_task_status shows task_status="done", incorporate task_result naturally into conversation
                    8. Avoid using illegal character like emojis and more

                    ## Workflow Pattern (IMPORTANT)
                    1. User asks question
                    2. Call push_to_queue(task_name="...", task_description="...")
                    3. IMMEDIATELY respond to user with engaging conversation (DON'T wait!)
                    4. In next turn, call check_task_status() to see if results are ready
                    5. If task_status="done": Use task_result in your response
                    6. If task_status="pending" or "processing": Continue conversation naturally, ask follow-up questions
                    7. Check again in subsequent turns until results arrive

                    ## Forbidden Phrases (NEVER USE THESE)
                    - "Let me check..."
                    - "I'm gathering information..."
                    - "Please wait..."
                    - "Hold on..."
                    - "Give me a moment..."
                    - "Let me fetch that..."
                    - "I'm looking into that..."
                    - Any phrase suggesting waiting or processing

                    ## Example Flow
                    User: "What courses do you offer in Delhi?"

                    [Turn 1]
                    Action: push_to_queue(task_name="delhi_courses", task_description="fetch course details for Delhi location")
                    Response: "Great question! We have several excellent programs in Delhi across different fields. What type of course are you most interested in - professional development, academic, or certification programs?"

                    [Turn 2 - User responds]
                    Action: check_task_status(task_name="delhi_courses")
                    If done: "Perfect! For professional development in Delhi, we offer [incorporate task_result naturally]..."
                    If still pending: "That's great! While I gather the specific details, could you tell me about your background or what you're hoping to achieve?"

                    [Turn 3 - If still needed]
                    Action: check_task_status(task_name="delhi_courses")
                    Use results when available

                    Remember: You're a conversationalist who NEVER makes users wait. Keep talking, keep engaging!
                """
            }
        ],
        task_messages=[
            {
                "role": "system",
                "content": f"""
                {handler.sections.instructions.content if handler.sections.instructions else None}
                 Warmly greet the user to start conversation and move along with the conversation flow never repeat the greetings
                """,
            }
        ],
        functions=[queue_checker,check_task_status],
    )


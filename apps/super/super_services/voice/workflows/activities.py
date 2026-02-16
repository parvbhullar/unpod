"""
Temporal activities for voice task processing.
"""
import os
import sys
import asyncio
import traceback
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from temporalio import activity

from super.core.logging.logging import print_log
from super_services.voice.models.config import ModelConfig, MessageCallBack


def sanitize_data_for_mongodb(data):
    """Sanitize data to make it MongoDB-compatible by converting non-serializable objects"""
    if isinstance(data, dict):
        return {key: sanitize_data_for_mongodb(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_data_for_mongodb(item) for item in data]
    elif isinstance(data, timedelta):
        # Convert timedelta to total seconds (float)
        return data.total_seconds()
    elif isinstance(data, datetime):
        # Convert datetime to ISO string
        return data.isoformat()
    elif hasattr(data, '__dict__') and not isinstance(data, (str, int, float, bool, type(None))):
        # Convert complex objects to dictionaries, but be careful with circular references
        try:
            return {key: sanitize_data_for_mongodb(value) for key, value in data.__dict__.items()
                    if not key.startswith('_')}
        except:
            # If conversion fails, return string representation
            return str(data)
    else:
        return data


@activity.defn
async def execute_call_activity(agent_id: str, task_id: str, data: dict,
                                 instructions: str = None, model_config: dict = None) -> dict:
    """
    Temporal activity for executing voice calls.

    Args:
        agent_id: The agent identifier
        task_id: The task identifier
        data: Call data containing contact information or room details
        instructions: Optional instructions for the call
        model_config: Model configuration dictionary

    Returns:
        dict: Response containing status and call data
    """
    activity.logger.info(f"Executing call activity for task_id: {task_id}, agent_id: {agent_id}")

    try:
        from super.app.call_execution import execute_call

        # Execute the call asynchronously
        response = await execute_call(
            agent_id=agent_id,
            task_id=task_id,
            data=data,
            instructions=instructions,
            model_config=ModelConfig(),
            callback=MessageCallBack(),
        )

        activity.logger.info(f"Call activity completed for task_id: {task_id} with status: {response.get('status')}")

        # Sanitize data for MongoDB compatibility
        if response and response.get("data"):
            response["data"] = sanitize_data_for_mongodb(response["data"])

        return response

    except Exception as ex:
        activity.logger.error(f"Call activity failed for task_id: {task_id}: {str(ex)}")
        activity.logger.error(f"Traceback: {traceback.format_exc()}")

        return {
            "status": "failed",
            "data": {
                "error": f"Activity execution failed: {str(ex)}",
                "traceback": traceback.format_exc()
            }
        }

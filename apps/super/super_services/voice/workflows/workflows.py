"""
Temporal workflow definitions for voice task processing.
"""
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from super_services.voice.models.config import ModelConfig, MessageCallBack
    from super.core.logging.logging import print_log


@workflow.defn
class VoiceTaskWorkflow:
    """
    Temporal workflow for processing voice tasks (outbound calls).
    """

    @workflow.run
    async def run(self, task_id: str, agent_id: str, data: dict,
                  instructions: str = None, model_config: dict = None) -> dict:
        """
        Execute a voice task workflow.

        Args:
            task_id: The unique identifier for the task
            agent_id: The agent identifier
            data: Call data containing contact information or room details
            instructions: Optional instructions for the call
            model_config: Model configuration dictionary

        Returns:
            dict: Response containing status and call data
        """
        workflow.logger.info(f"Starting voice task workflow for task_id: {task_id}, agent_id: {agent_id}")

        try:
            # Execute the call activity with retry policy
            result = await workflow.execute_activity(
                "execute_call_activity",
                args=[agent_id, task_id, data, instructions, model_config],
                start_to_close_timeout=timedelta(minutes=15),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=10),
                    maximum_interval=timedelta(minutes=1),
                    maximum_attempts=3,
                    non_retryable_error_types=["ValueError"],
                ),
            )

            workflow.logger.info(f"Voice task workflow completed for task_id: {task_id}")
            return result

        except Exception as e:
            workflow.logger.error(f"Voice task workflow failed for task_id: {task_id}: {str(e)}")
            return {
                "status": "failed",
                "data": {
                    "error": f"Workflow execution failed: {str(e)}"
                }
            }

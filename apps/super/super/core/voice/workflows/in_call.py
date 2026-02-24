from super.core.voice.schema import UserState
from super_services.db.services.models.task import TaskModel
from .tools.classification import CallSummarizer
import logging


class InCallWorkflow:
    def __init__(self, user_state: UserState, logger):
        self.user_state = user_state
        self.summarizer = CallSummarizer()
        self.logger = logger if logger else logging.getLogger(__name__)

    async def _get_ref_id(self):
        try:
            task = TaskModel.get(
                task_id=self.user_state.task_id,
            )

            return task.ref_id

        except Exception as e:
            self.logger.error(f"Error getting ref id {str(e)}")
            return None

    async def _fetch_past_call_history(self):
        numbers = [self.user_state.contact_number]

        if self.user_state.contact_number.startswith("0"):
            numbers.append(self.user_state.contact_number[1:])

        search_fields = [
            {"input.contact_number": {"$in": numbers}},
            {"output.contact_number": {"$in": numbers}},
            {"input.number": {"$in": numbers}},
            {"output.customer": {"$in": numbers}},
        ]

        ref_id = await self._get_ref_id()

        if ref_id:
            search_fields.append({"ref_id": {"$in": [ref_id]}})

        try:
            call_data = list(
                TaskModel._get_collection()
                .find(
                    {
                        "$or": search_fields,
                        "assignee": self.user_state.model_config.get("agent_id"),
                    },
                    {"output": 1, "_id": 0},
                )
                .sort([("created", -1)])
                .limit(5)
            )

            return call_data
        except Exception as e:
            self.logger.error(f"Error getting call history {str(e)}")
            return {}

    async def generate_handover_summary(self):
        self.logger.info("[InCallWorkflow] Starting handover summary generation")

        try:
            current_transcript = self.user_state.transcript
            past_call_context = await self._fetch_past_call_history()
            handover_prompt = ""
            if (
                self.user_state
                and isinstance(self.user_state.model_config, dict)
            ):
                handover_prompt = self.user_state.model_config.get("handover_prompt", "")

            if not handover_prompt:
                from super.core.voice.prompts.guidelines import HANOVER_INSTRUCTIONS

                handover_prompt = HANOVER_INSTRUCTIONS

            summary_result = self.summarizer.forward(
                call_transcript=self.user_state.transcript,
                call_datetime=self.user_state.start_time,
                prompt=handover_prompt,
            )

            # Build handover summary structure
            handover_summary = {
                "handover_summary": {
                    "current_call": {
                        "summary": summary_result.summary
                        if summary_result
                        else "Summary generation failed",
                        "transcript": current_transcript,
                    },
                    "past_call_context": past_call_context,
                }
            }

            print(f"[InCallWorkflow] handover summary generation completed.")
            return handover_summary

        except Exception as e:
            self.logger.error(f"[InCallWorkflow] Summary generation failed: {e}")
            return {}

    async def execute(self):
        pass


if __name__ == "__main__":
    print("[InCallWorkflow] Starting InCall Workflow")
    import asyncio

    workflow = InCallWorkflow(
        user_state=UserState(
            contact_number="+918847348129",
            task_id="Tefe4015f78de11f082ac156368e7acc4",
            model_config={
                "agent_id": "testing-good-qua-xkc0gsvr7ns7",
            },
            transcript=[],
        ),
        logger=logging,
    )
    asyncio.run(workflow.generate_handover_summary())

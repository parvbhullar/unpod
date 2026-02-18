import datetime

from .tools.classification import (
    CallClassificationService,
    CallSummarizer,
    CallLabelClassifier,
    ProfileSummaryExtractor,
)
from super.core.voice.schema import UserState
import asyncio
from .base import BaseWorkflow
from .tools.helper_functions import get_next_date
from .tools.success_evaluator import SuccessEvaluator
from .tools.structured_data import StructuredDataExtractor
from .dspy_config import get_dspy_lm
import json
from typing import Dict, Any
from super_services.orchestration.task.task_service import TaskService
from super.core.logging import logging
from ...logging.logging import print_log
from super.core.voice.voice_agent_evals.voice_evaluation import evaluate_voice_call
from .tools.call_scheduler import FollowUpAnalyzer
from super.core.voice.schema import CallStatusEnum

# Setup logger
logger = logging.get_logger(__name__)


class PostCallWorkflow(BaseWorkflow):
    def __init__(
        self,
        agent: str = None,
        model_config: dict = None,
        user_state: UserState = None,
        transcript=None,
        token=None,
        document_id=None,
        data=None,
        lm=None,
    ):
        super().__init__(agent, model_config, user_state, transcript, token)
        self.data = data if data else {}
        self.call_time = self.data.get("call_end_time")
        self.callback_enabled = model_config.get("callback_enabled", False)
        self.followup_prompt = model_config.get("followup_prompt", "")
        self.follow_up_enabled = model_config.get("follow_up_enabled", True)
        self.document_id = document_id
        self.is_in_redial = False
        # Create process-local LM instance
        self.lm = lm or get_dspy_lm()

        # Pass LM to tool instances
        self.label_classifier = CallLabelClassifier(
            self.transcript,
            {
                "follow_up": "need to call again requested by user as user shows interest in services",
                "call_back": "user didn't pick up the call or call got cancelled midway couldn't complete call",
            },
            lm=self.lm,
        )
        self.scheduled_date = get_next_date(model_config)
        self.success_evaluator = SuccessEvaluator(lm=self.lm)
        self.data_extractor = StructuredDataExtractor(lm=self.lm)
        self.success_evaluation_plan = None
        self.structured_data_plan = None
        self.summary_plan = None
        self.follow_up_service = FollowUpAnalyzer()

    def process_input_date(self, data):
        result = data.get("input_data", {})
        result["scheduled_data"] = self.scheduled_date
        return result

    async def create_post_call_pipeline(self):
        tools = self.model_config.get("post_call_playbook", [])
        try:
            for i in tools:
                if i.get("success_evaluation"):
                    value = i.get("success_evaluation")
                    # Parse if string, use directly if dict
                    if isinstance(value, str):
                        self.success_evaluation_plan = json.loads(value)
                    else:
                        self.success_evaluation_plan = value
                    # Ensure it's a dict
                    if not isinstance(self.success_evaluation_plan, dict):
                        self.success_evaluation_plan = {}

                elif i.get("structured_data"):
                    value = i.get("structured_data")
                    # Parse if string, use directly if dict
                    if isinstance(value, str):
                        self.structured_data_plan = json.loads(value)
                    else:
                        self.structured_data_plan = value
                    # Ensure it's a dict
                    if not isinstance(self.structured_data_plan, dict):
                        self.structured_data_plan = {}

                elif i.get("summary"):
                    value = i.get("summary")
                    # Parse if string, use directly if dict
                    if isinstance(value, str):
                        self.summary_plan = json.loads(value)
                    else:
                        self.summary_plan = value
                    # Ensure it's a dict
                    if not isinstance(self.summary_plan, dict):
                        self.summary_plan = {}

        except Exception as e:
            print(f"[PostCallWorkflow] Error creating pipeline: {e}")

    async def create_follow_up_task(self, time):
        from super.core.voice.common.services import create_scheduled_task

        print(f"[PostCallWorkflow] Creating follow_up task")
        try:
            res = await create_scheduled_task(self.data.get("task_id"), time)

            if res:
                from super_services.prefect_setup.deployments.utils import (
                    trigger_deployment,
                )
                from prefect.states import Scheduled

                await trigger_deployment(
                    "Execute-Task",
                    {
                        "job": {
                            "task_id": res.get("task_id"),
                            "retry": 0,
                            "run_type": "call",
                        }
                    },
                    state=Scheduled(scheduled_time=res.get("time")),
                )

                print(f"[PostCallWorkflow] Created follow_up task")
                return "call_scheduled"

            print("[PostCallWorkflow] failed follow_up task")
            return "failed to schedule_call"

        except Exception as e:
            print(f"faield to schedule call {str(e)}")
            return "failed to schedule_call"

    async def follow_up(self):
        followup = None

        if self.follow_up_enabled:
            print("processing followup")

            results = self.label_classifier.classify()

            if self.model_config:
                available_slots = {
                    "time_range": json.loads(
                        self.model_config.get("calling_time_ranges", [])
                    ),
                    "days_range": json.loads(self.model_config.get("calling_days", [])),
                }
            else:
                available_slots = {}

            res = self.follow_up_service.forward(
                call_transcript=self.transcript,
                prompt=self.followup_prompt,
                token=self.token,
                document_id=self.document_id,
                available_slots=available_slots,
            )

            # from super.core.voice.common.common import send_web_notification
            # from super.core.voice.common.services import send_retry_sms

            if (
                self.user_state
                and self.user_state.call_status
                in [
                    CallStatusEnum.VOICEMAIL,
                    CallStatusEnum.BUSY,
                    CallStatusEnum.CANCELLED,
                    CallStatusEnum.NOT_CONNECTED,
                ]
                and res.followup_required == "true"
            ):
                followup_time = datetime.datetime.now() + datetime.timedelta(hours=1)

                followup = await self.create_follow_up_task(followup_time)
                await self._Send_sms(followup_time)

            elif res.followup_required == "true":
                followup = await self.create_follow_up_task(res.followup_time)

                await self._Send_sms(res.followup_time)

            return {
                "required": res.followup_required,
                "time": res.followup_time,
                "reason": res.reason,
                "status": followup,
            }

        return {"required": "follow_up disabled"}

    async def _Send_sms(self, followup_time):
        from super.core.voice.common.common import send_web_notification

        if self.model_config.get("sms_enabled", False):
            from super.core.voice.common.services import send_retry_sms

            await send_retry_sms(
                self.user_state,
                self.data.get("task_id"),
                self.model_config.get("agent_id"),
            )
            await send_web_notification(
                "completed",
                "sms_sent",
                self.user_state,
                self.user_state.call_status,
            )

    async def classification(self):
        print_log(
            "Classifying call for token and document id", self.token, self.document_id
        )
        classify_service = CallClassificationService(
            self.transcript, self.token, self.document_id
        )
        response = await classify_service.classify_call()
        return response

    async def instant_redial(self):
        scheduled_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=2)
        task_id = self.data.get("task_id")

        if not self.callback_enabled:
            return "instant redial not enabled"

        if not task_id:
            return {}

        from super.core.voice.common.services import schedule_redial_task

        is_scheduled = schedule_redial_task(task_id, scheduled_time, self.transcript)

        if is_scheduled:
            from super_services.prefect_setup.deployments.utils import (
                trigger_deployment,
            )
            from prefect.states import Scheduled

            await trigger_deployment(
                "Execute-Task",
                {
                    "job": {
                        "task_id": task_id,
                        "retry": 0,
                        "run_type": "call",
                    }
                },
                state=Scheduled(scheduled_time=scheduled_time),
            )
            self.is_in_redial = True
            return "call_scheduled_for_redial"
        return "unable to instant redial"

    async def summary_generation(self):
        print("generating summary ")
        summary_generator = CallSummarizer()
        summary = summary_generator.forward(
            call_transcript=self.transcript,
            call_datetime=self.call_time,
        )

        print(summary, "summary")

        if summary.status in ["Abandoned", "Dropped"]:
            await self.instant_redial()

        return summary.toDict()

    async def success_evaluation(self):
        if self.success_evaluation_plan:
            print("success evaluting")
            result = await self.success_evaluator.forward(
                self.transcript,
                self.success_evaluation_plan.get("prompt"),
                self.success_evaluation_plan.get("success_evaluation_rubric"),
            )
            return result.evaluate
        return None

    async def profile_summary_generation(self):
        print("generating profile summary")
        try:
            if not self.transcript or len(self.transcript) == 0:
                return None
            profile_extractor = ProfileSummaryExtractor(lm=self.lm)
            profile_summary = profile_extractor.forward(call_transcript=self.transcript)
            print_log(
                f"Profile summary generated: {profile_summary}",
                "profile_summary_generated",
            )
            return profile_summary
        except Exception as e:
            print_log(f"Error generating profile summary: {e}", "profile_summary_error")
            return None

    async def structured_data(self, success_result: str = ""):
        if self.structured_data_plan and isinstance(self.structured_data_plan, dict):
            print("Extracting structured data", self.structured_data_plan)

            # Safely get options (ensure it's a dict)
            options = self.structured_data_plan.get("options", {})
            if not isinstance(options, dict):
                options = {}

            # Get properties from options
            properties = options.get("properties", {})
            if not isinstance(properties, dict):
                properties = {}

            result = self.data_extractor.forward(
                self.transcript,
                properties,
                self.structured_data_plan.get("prompt"),
                success_result,
            )
            return result

        return None

    async def call_evaluation(self) -> Dict[str, Any]:
        """
        Evaluate the call using the standalone evaluator and persist results.

        Returns:
            Dict containing session_id, evaluation_results, quality_metrics, and optional audio_file_path
        """
        try:
            # Get thread_id from task using task_id (preferred method)
            thread_id = None
            task_id = self.data.get("task_id")

            if task_id:
                try:
                    task_service = TaskService()
                    task = task_service.get_task(task_id)
                    if task:
                        thread_id = (
                            getattr(task, "thread_id", None) or task.get("thread_id")
                            if isinstance(task, dict)
                            else None
                        )
                        logger.info(f"Got thread_id from task: {thread_id}")
                except Exception as e:
                    logger.warning(f"Failed to get thread_id from task: {e}")

            # Build session_id - prefer thread_id from task
            session_id = (
                thread_id
                or self.data.get("thread_id")
                or self.data.get("session_id")
                or self.data.get("call_id")
                or task_id
                or self.document_id
                or f"{int(__import__('time').time())}-session"
            )

            agent_id = self.agent or "unknown-agent"

            logger.info(
                f"Starting persisted call evaluation via VoiceCallEvaluator | session_id={session_id} agent_id={agent_id}"
            )

            # Get turn_metrics from call data if available (set by pipecat_handler)
            turn_metrics = self.data.get("turn_metrics", None)
            if turn_metrics:
                logger.info(
                    f"Found turn_metrics in call data: {len(turn_metrics)} turns"
                )
            else:
                logger.warning(
                    "No turn_metrics found in call data - per-turn cost/latency won't be saved"
                )

            # Get space_token - try model_config first, then fall back to data["token"]
            space_token = None
            if self.model_config:
                space_token = self.model_config.get("space_token")
            if not space_token and self.data:
                # Fall back to token from input data (this is the space token)
                space_token = self.data.get("input_data", {}).get(
                    "token"
                ) or self.data.get("token")

            logger.info(f"Space token for evaluation: {space_token}")

            # Evaluate using transcript only (no audio download needed)
            result = await evaluate_voice_call(
                session_id=session_id,
                agent_id=agent_id,
                transcript=self.transcript or [],
                audio_data=None,
                turn_metrics=turn_metrics,
                space_token=space_token,
            )

            evaluation_results = result.get("evaluation_results", [])

            logger.info(
                "Persisted evaluation complete | turns=%s quality=%.2f",
                len(evaluation_results),
                (result.get("quality_metrics", {}) or {}).get(
                    "overall_quality_score", 0.0
                ),
            )

            # Return the full result dict with session_id and evaluation_results
            return result

        except Exception as e:
            logger.error(f"Error in persisted call evaluation: {str(e)}", exc_info=True)
            return {
                "session_id": None,
                "evaluation_results": [],
                "quality_metrics": {},
                "audio_file_path": None,
            }

    def _extract_eval_records(self) -> Dict[str, Any]:
        """Fetch runtime eval traces from call_result.data or user_state.extra_data."""
        try:
            output = self.data.get("output")
            output_data = {}
            if isinstance(output, dict):
                output_data = output.get("data", {}) or {}
            elif hasattr(output, "data") and isinstance(output.data, dict):
                output_data = output.data

            eval_records = output_data.get("eval_records")
            if isinstance(eval_records, dict):
                return eval_records

            if self.user_state and isinstance(self.user_state.extra_data, dict):
                extra_records = self.user_state.extra_data.get("eval_records")
                if isinstance(extra_records, dict):
                    return extra_records
        except Exception as e:
            logger.warning(f"Could not extract eval_records: {e}")
        return {}

    def _extract_ground_truth_qa_pairs(self) -> list:
        """Collect QA pairs from post-call input/model config for realtime eval."""
        qa_pairs = []
        try:
            from super.core.voice.common.common import get_qa_pairs

            kn_list = self.model_config.get("knowledge_base", {})

            tokens = [item["token"] for item in kn_list if item.get("token")]
            print(f"{len(tokens)} tokens in knowledge_base")

            qa_pairs = get_qa_pairs(tokens)

        except Exception as e:
            logger.warning(f"Could not extract QA pairs for realtime eval: {e}")

        return qa_pairs

    async def realtime_agent_evaluation(self) -> Dict[str, Any]:
        """
        Evaluate runtime tool calls and responses against QA ground truth.
        """
        try:
            eval_records = self._extract_eval_records()
            qa_pairs = self._extract_ground_truth_qa_pairs()

            if not eval_records:
                return {
                    "status": "skipped",
                    "reason": "No eval_records found in call data",
                    "total_cases": 0,
                    "passed_cases": 0,
                    "failed_cases": 0,
                    "pass_rate": 0.0,
                    "test_results": [],
                }

            if not qa_pairs:
                return {
                    "status": "skipped",
                    "reason": "No QA pairs found for ground truth",
                    "total_cases": 0,
                    "passed_cases": 0,
                    "failed_cases": 0,
                    "pass_rate": 0.0,
                    "test_results": [],
                }

            from super.core.voice.eval_agent.eval_test_agent import EvalTestAgent

            evaluator = EvalTestAgent(model_config=self.model_config or {})
            result = await evaluator.evaluate_call_records(
                eval_records=eval_records,
                qa_pairs=qa_pairs,
            )
            result["status"] = "completed"
            return result
        except Exception as e:
            logger.error(f"Realtime agent evaluation failed: {e}", exc_info=True)
            return {
                "status": "failed",
                "reason": str(e),
                "total_cases": 0,
                "passed_cases": 0,
                "failed_cases": 0,
                "pass_rate": 0.0,
                "test_results": [],
            }

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate the similarity ratio between two strings.
        Returns a float between 0 and 1, where 1 means identical.
        """
        from difflib import SequenceMatcher

        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    def _calculate_relevancy(self, reply: str, expected: str) -> float:
        """
        Calculate how relevant the reply is to the expected answer.
        Returns a float between 0 and 1.
        """
        if not reply or not expected:
            return 0.0
        # Use both similarity and keyword matching for better relevancy score
        similarity = self._calculate_similarity(reply, expected)

        # Calculate keyword coverage
        expected_keywords = set(
            word.lower() for word in expected.split() if len(word) > 3
        )
        if not expected_keywords:
            return similarity

        reply_keywords = set(word.lower() for word in reply.split())
        keyword_coverage = len(expected_keywords.intersection(reply_keywords)) / len(
            expected_keywords
        )

        # Combine both metrics
        return (similarity + keyword_coverage) / 2

    def _calculate_completeness(self, reply: str, expected: str) -> float:
        """
        Calculate how complete the reply is compared to the expected answer.
        Returns a float between 0 and 1.
        """
        if not reply or not expected:
            return 0.0

        # Split into sentences for better comparison
        import re

        expected_sentences = [
            s.strip() for s in re.split(r"[.!?]", expected) if s.strip()
        ]
        if not expected_sentences:
            return 0.0

        # Check how many expected sentences are covered in the reply
        covered = 0
        for sentence in expected_sentences:
            if len(sentence.split()) < 3:  # Skip very short sentences
                continue
            if sentence.lower() in reply.lower():
                covered += 1

        return covered / len(expected_sentences)

    def _calculate_accuracy(self, reply: str, expected: str) -> float:
        """
        Calculate the overall accuracy of the reply compared to the expected answer.
        Returns a float between 0 and 1.
        """
        if not reply or not expected:
            return 0.0

        # Calculate different aspects of the answer
        similarity = self._calculate_similarity(reply, expected)
        relevancy = self._calculate_relevancy(reply, expected)
        completeness = self._calculate_completeness(reply, expected)

        # Weighted average of different metrics
        return (similarity * 0.3) + (relevancy * 0.4) + (completeness * 0.3)

    async def execute(self):
        print("executing post call _workflow")
        await self.create_post_call_pipeline()

        results = await asyncio.gather(
            self.classification(),
            self.summary_generation(),
            self.success_evaluation(),
            self.follow_up(),
            self.call_evaluation(),
            self.profile_summary_generation(),
            self.realtime_agent_evaluation(),
        )

        data = {
            "classification": results[0],
            "summary": results[1],
            "success_evaluator": results[2],
            "follow_up": results[3],
            "call_evaluation": results[4],
            "profile_summary": results[5],
            "realtime_agent_evaluation": results[6],
        }

        data["structured_data"] = await self.structured_data(
            data.get("success_evaluator")
        )

        if self.is_in_redial:
            data["is_redial"] = True

        return data

import datetime
import asyncio
import json
from typing import Dict, Any

from .tools.classification import (
    CallClassificationService,
    CallSummarizer,
    ProfileSummaryExtractor,
)
from super.core.voice.schema import UserState, CallStatusEnum
from .base import BaseWorkflow
from .tools.helper_functions import get_next_date
from .tools.success_evaluator import SuccessEvaluator
from .tools.structured_data import StructuredDataExtractor
from .tools.call_scheduler import FollowUpAnalyzer
from .tools.config import get_now
from .dspy_config import get_dspy_lm
from super_services.orchestration.task.task_service import TaskService
from super.core.logging import logging
from ...logging.logging import print_log
from super.core.voice.voice_agent_evals.voice_evaluation import evaluate_voice_call

# Setup logger
logger = logging.get_logger(__name__)

NOT_CONNECTED_STATUSES = {
    CallStatusEnum.VOICEMAIL,
    CallStatusEnum.BUSY,
    CallStatusEnum.CANCELLED,
    CallStatusEnum.NOT_CONNECTED,
    CallStatusEnum.DROPPED,
    CallStatusEnum.FAILED,
}


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
        self.scheduled_date = get_next_date(model_config)
        self.success_evaluator = SuccessEvaluator(lm=self.lm)
        self.data_extractor = StructuredDataExtractor(lm=self.lm)
        self.success_evaluation_plan = None
        self.structured_data_plan = None
        self.summary_plan = None
        self.follow_up_service = FollowUpAnalyzer(lm=self.lm)

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

    async def create_follow_up_task(self, time, max_calls: int = 3):
        from super.core.voice.common.services import create_scheduled_task

        print(f"[PostCallWorkflow] Creating follow_up task")
        try:
            res = await create_scheduled_task(
                self.data.get("task_id"), time, max_calls=max_calls
            )

            if res:
                if res.get("deduplicated"):
                    print("[PostCallWorkflow] follow_up task already scheduled")
                    return "call_already_scheduled"

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

    def _get_available_slots(self) -> dict:
        if not self.model_config:
            return {}
        try:
            return {
                "time_range": json.loads(
                    self.model_config.get("calling_time_ranges", "[]")
                ),
                "days_range": json.loads(
                    self.model_config.get("calling_days", "[]")
                ),
            }
        except (json.JSONDecodeError, TypeError):
            return {}

    def _is_not_connected(self) -> bool:
        if self.user_state is None:
            return False
        if self.user_state.call_status in NOT_CONNECTED_STATUSES:
            return True
        status = str(self.user_state.call_status or "").strip()
        normalized_not_connected = {
            str(getattr(item, "value", item)) for item in NOT_CONNECTED_STATUSES
        }
        return status in normalized_not_connected or status in {"dropped", "droped"}

    async def follow_up(self):
        if not self.follow_up_enabled:
            return {"required": "follow_up disabled"}

        print("processing followup")
        followup = None
        available_slots = self._get_available_slots()

        res = self.follow_up_service.forward(
            call_transcript=self.transcript,
            prompt=self.followup_prompt,
            token=self.token,
            document_id=self.document_id,
            available_slots=available_slots,
            task_id=self.data.get("task_id"),
            model_config=self.model_config,
            assignee=self.agent,
        )

        if res.followup_required:
            followup = await self.create_follow_up_task(
                res.followup_time,
                max_calls=getattr(res, "max_calls", 3),
            )
        elif (
            self._is_not_connected()
            and res.reason
            and "max_calls" in res.reason
        ):
            # All retries exhausted, never connected — send SMS
            await self._Send_sms()

        return {
            "required": res.followup_required,
            "time": res.followup_time,
            "reason": res.reason,
            "status": followup,
        }

    async def _Send_sms(self):
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
        scheduled_time = get_now(self.model_config) + datetime.timedelta(minutes=2)
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
        try:
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

            turn_metrics = self.data.get("turn_metrics", None)
            if turn_metrics:
                logger.info(
                    f"Found turn_metrics in call data: {len(turn_metrics)} turns"
                )
            else:
                logger.warning(
                    "No turn_metrics found in call data - per-turn cost/latency won't be saved"
                )

            space_token = None
            if self.model_config:
                space_token = self.model_config.get("space_token")
            if not space_token and self.data:
                space_token = self.data.get("input_data", {}).get(
                    "token"
                ) or self.data.get("token")

            logger.info(f"Space token for evaluation: {space_token}")

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
        try:
            eval_records = self._extract_eval_records()
            latency_metrics = self._extract_latency_metrics()
            llm_latency = self._build_llm_latency_summary(
                eval_records=eval_records,
                latency_metrics=latency_metrics,
            )
            qa_pairs = self._extract_ground_truth_qa_pairs()

            # Extract session metadata
            session_id = self._extract_session_id()
            agent_id = self.agent or "unknown-agent"
            call_start_time = self.data.get("call_start_time", 0)
            call_end_time = self.data.get("call_end_time", 0)

            print(
                f"{'='*100} \n\n\n {eval_records}\n\n llm_latency: {llm_latency} \n\n latency_metrics: {latency_metrics} \n\n {'='*100}"
            )

            # Build base result structure
            base_result = {
                "session_id": session_id,
                "agent_id": agent_id,
                "llm_latency": llm_latency,
            }

            if not eval_records:
                return {
                    **base_result,
                    "status": "skipped",
                    "reason": "No eval_records found in call data",
                }

            if not qa_pairs:
                return {
                    **base_result,
                    "status": "skipped",
                    "reason": "No QA pairs found for ground truth",
                }

            from super.core.voice.eval_agent.eval_test_agent import EvalTestAgent

            evaluator = EvalTestAgent(model_config=self.model_config or {})
            result = await evaluator.evaluate_call_records(
                eval_records=eval_records,
                qa_pairs=qa_pairs,
            )

            # Check if RAGAS/DeepEval evaluation is enabled
            enable_ragas = (
                self.model_config.get("enable_ragas_eval", True)
                if self.model_config
                else True
            )
            enable_deepeval = (
                self.model_config.get("enable_deepeval_eval", True)
                if self.model_config
                else True
            )

            # Build detailed_results from test_results with RAGAS/DeepEval metrics
            detailed_results = await self._build_detailed_results(
                test_results=result.get("test_results", []),
                eval_records=eval_records,
                latency_metrics=latency_metrics,
                qa_pairs=qa_pairs,
                session_id=session_id,
                agent_id=agent_id,
                call_start_time=call_start_time,
                call_end_time=call_end_time,
                enable_ragas=enable_ragas,
                enable_deepeval=enable_deepeval,
            )

            # Add conversation_details
            total_turns = len(result.get("test_results", []))
            questions_matched = sum(
                1
                for r in result.get("test_results", [])
                if r.get("question_match_score", 0) > 0
            )

            result["status"] = "completed"
            result["session_id"] = session_id
            result["agent_id"] = agent_id
            result["llm_latency"] = llm_latency
            result["conversation_details"] = {
                "total_turns": total_turns,
                "total_questions_matched": questions_matched,
            }
            result["detailed_results"] = detailed_results
            return result

        except Exception as e:
            logger.error(f"Realtime agent evaluation failed: {e}", exc_info=True)
            return {
                "session_id": self._extract_session_id(),
                "agent_id": self.agent or "unknown-agent",
                "status": "failed",
                "reason": str(e),
                "llm_latency": {
                    "count": 0,
                    "avg": None,
                    "min": None,
                    "max": None,
                    "p95": None,
                    "unit": "seconds",
                },
                "conversation_details": {
                    "total_turns": 0,
                    "total_questions_matched": 0,
                },
                "total_cases": 0,
                "passed_cases": 0,
                "failed_cases": 0,
                "pass_rate": 0.0,
                "test_results": [],
                "detailed_results": [],
            }

    def _extract_session_id(self) -> str:
        """Extract session_id from available data sources."""
        task_id = self.data.get("task_id")
        if task_id:
            try:
                task_service = TaskService()
                task = task_service.get_task(task_id)
                if task:
                    thread_id = getattr(task, "thread_id", None) or (
                        task.get("thread_id") if isinstance(task, dict) else None
                    )
                    if thread_id:
                        return thread_id
            except Exception:
                pass

        return (
            self.data.get("thread_id")
            or self.data.get("session_id")
            or self.data.get("call_id")
            or task_id
            or self.document_id
            or f"{int(__import__('time').time())}-session"
        )

    async def _build_detailed_results(
        self,
        test_results: list,
        eval_records: Dict[str, Any],
        latency_metrics: list,
        qa_pairs: list,
        session_id: str,
        agent_id: str,
        call_start_time: float,
        call_end_time: float,
        enable_ragas: bool = True,
        enable_deepeval: bool = True,
    ) -> list:
        detailed = []
        user_messages = eval_records.get("user_messages", []) or []
        agent_responses = eval_records.get("agent_responses", []) or []
        tool_calls = eval_records.get("tool_calls", []) or []

        # Build a mapping from turn_count to latency metrics
        # lite_handler.py uses turn_count (1-indexed), not sequence_id
        latency_by_turn = {}
        for metric in latency_metrics or []:
            if isinstance(metric, dict):
                turn_count = metric.get("turn_count")
                if turn_count is not None:
                    latency_by_turn[turn_count] = metric

        # Build a mapping from test_result index to test_result
        test_results_by_seq = {}
        for tr in test_results:
            seq_id = tr.get("eval_record_sequence_id")
            if seq_id is not None:
                test_results_by_seq[seq_id] = tr

        # Initialize RAGAS/DeepEval evaluator if enabled
        metrics_evaluator = None
        if enable_ragas or enable_deepeval:
            try:
                from super.core.voice.eval_agent.realtime_metrics_evaluator import (
                    get_realtime_metrics_evaluator,
                    is_ragas_available,
                    is_deepeval_available,
                )

                # Only create evaluator if at least one library is available
                if (enable_ragas and is_ragas_available()) or (
                    enable_deepeval and is_deepeval_available()
                ):
                    metrics_evaluator = get_realtime_metrics_evaluator(
                        model_config=self.model_config,
                        enable_ragas=enable_ragas,
                        enable_deepeval=enable_deepeval,
                    )
                    logger.info(
                        f"RAGAS/DeepEval evaluator initialized: "
                        f"RAGAS={enable_ragas and is_ragas_available()}, "
                        f"DeepEval={enable_deepeval and is_deepeval_available()}"
                    )
            except Exception as e:
                logger.warning(f"Failed to initialize RAGAS/DeepEval evaluator: {e}")
                metrics_evaluator = None

        # Prepare turns for batch evaluation
        turns_for_eval = []

        for turn_idx, user_msg in enumerate(user_messages):
            seq_id = user_msg.get("sequence_id", turn_idx)
            user_question = str(user_msg.get("content", "") or "")
            turn_number = turn_idx + 1

            # Find matching test_result
            test_result = test_results_by_seq.get(seq_id, {})

            # Find matching agent response
            matched_response = self._find_response_for_sequence(
                seq_id, agent_responses, user_messages
            )
            agent_reply = (matched_response or {}).get("content", "")
            llm_latency_val = (matched_response or {}).get("llm_latency", 0)

            # Find matching tool call
            matched_tool = self._find_tool_for_sequence(
                seq_id, tool_calls, user_messages
            )
            tool_name = (matched_tool or {}).get("tool_name", "")
            is_tool_call = bool(tool_name)
            tool_call_success = (
                test_result.get("tool_pass", False) if is_tool_call else False
            )

            # Get matched QA info
            question_found = test_result.get("question_match_score", 0) > 0
            eval_question = test_result.get("question", "No matching question found")
            expected_output = test_result.get(
                "expected_answer", "No expected output available"
            )
            intent = test_result.get("expected_intent", "")
            matched_keywords = ""  # Could be populated if available

            # Get latency data for this turn using turn_count (1-indexed)
            turn_latency = latency_by_turn.get(turn_number, {})

            # Use llm_latency from agent_response if available, else from latency_metrics
            if not llm_latency_val or llm_latency_val == 0:
                llm_latency_val = turn_latency.get("llm_latency", 0)

            # Calculate evaluation metrics
            similarity = (
                self._calculate_similarity(agent_reply, expected_output)
                if agent_reply and expected_output
                else 0
            )
            completeness = (
                self._calculate_completeness(agent_reply, expected_output)
                if agent_reply and expected_output
                else 0
            )
            accuracy = (
                self._calculate_accuracy(agent_reply, expected_output)
                if agent_reply and expected_output
                else 0
            )
            overall_quality = (
                (similarity + completeness + accuracy) / 3
                if (similarity or completeness or accuracy)
                else 0
            )

            # Prepare turn data for RAGAS/DeepEval evaluation
            turns_for_eval.append(
                {
                    "question": user_question,
                    "answer": agent_reply,
                    "expected_output": expected_output
                    if expected_output != "No expected output available"
                    else None,
                    "contexts": [expected_output]
                    if expected_output
                    and expected_output != "No expected output available"
                    else None,
                }
            )

            detailed_turn = {
                "session_id": session_id,
                "agent_id": agent_id,
                "conversation_details": {
                    "total_turns": len(user_messages),
                    "total_questions_matched": sum(
                        1
                        for tr in test_results
                        if tr.get("question_match_score", 0) > 0
                    ),
                },
                "turn_number": turn_number,
                "user_interaction": {
                    "user_question": user_question,
                    "eval_question": eval_question,
                    "question_found": question_found,
                    "matched_keywords": matched_keywords,
                    "intent": intent,
                    "tool_name": tool_name,
                    "is_tool_call": is_tool_call,
                    "tool_call_success": tool_call_success,
                    "agent_response": {
                        "agent_reply": agent_reply,
                        "expected_output": expected_output,
                    },
                },
                "ragas_metrics": {
                    "faithfulness_score": 0.0,
                    "answer_relevancy_score": 0.0,
                    "hallucination_score": 0.0,
                },
                "deepeval_metrics": {
                    "g_eval_score": 0.0,
                    "factual_consistency_score": 0.0,
                    "bias_score": 0.0,
                },
                "evaluation_metrics": {
                    "similarity": round(similarity, 4),
                    "completeness": round(completeness, 4),
                    "accuracy": round(accuracy, 4),
                    "overall_quality": round(overall_quality, 4),
                },
                "voice_call_data": {
                    "call_start_time": call_start_time,
                    "call_end_time": call_end_time,
                    "duration": (call_end_time - call_start_time)
                    if call_end_time and call_start_time
                    else 0,
                    "transcript_available": bool(self.transcript),
                    "stt_accuracy_score": turn_latency.get("stt_accuracy", 0),
                    "voice_interruption_detected": turn_latency.get(
                        "interrupted", False
                    ),
                },
                "latency_metrics": {
                    "avg_response_time": turn_latency.get("total_latency", 0),
                    "voice_to_voice_response_time": turn_latency.get(
                        "avg_total_latency", 0
                    ),
                    "llm_latency": llm_latency_val
                    if isinstance(llm_latency_val, (int, float))
                    else 0,
                    "stt_latency": turn_latency.get("stt_latency", 0),
                    "tts_latency": turn_latency.get("tts_latency", 0),
                    "llm_ttfb": turn_latency.get("llm_ttfb", 0),
                    "stt_ttfb": turn_latency.get("stt_ttfb", 0),
                    "tts_ttfb": turn_latency.get("tts_ttfb", 0),
                    "avg_llm_latency": turn_latency.get("avg_llm_latency", 0),
                    "avg_stt_latency": turn_latency.get("avg_stt_latency", 0),
                    "avg_tts_latency": turn_latency.get("avg_tts_latency", 0),
                },
                "token_metrics": {
                    "llm_prompt_tokens": turn_latency.get("prompt_tokens", 0),
                    "llm_completion_tokens": turn_latency.get("completion_tokens", 0),
                },
                "cost_metrics": {
                    "llm_cost": turn_latency.get("llm_cost", 0),
                    "stt_cost": turn_latency.get("stt_cost", 0),
                    "tts_cost": turn_latency.get("tts_cost", 0),
                },
                "provider_info": {
                    "llm_provider": turn_latency.get("llm_provider", ""),
                    "stt_provider": turn_latency.get("stt_provider", ""),
                    "tts_provider": turn_latency.get("tts_provider", ""),
                    "llm_type": turn_latency.get("llm_type", ""),
                    "stt_type": turn_latency.get("stt_type", ""),
                    "tts_type": turn_latency.get("tts_type", ""),
                },
            }
            detailed.append(detailed_turn)

        # Run RAGAS/DeepEval batch evaluation if evaluator is available
        if metrics_evaluator and turns_for_eval:
            try:
                logger.info(
                    f"Running RAGAS/DeepEval batch evaluation for {len(turns_for_eval)} turns"
                )
                eval_results = await metrics_evaluator.evaluate_batch(
                    turns=turns_for_eval,
                    max_concurrent=self.model_config.get("eval_max_concurrent", 3)
                    if self.model_config
                    else 3,
                )

                # Update detailed results with RAGAS/DeepEval metrics
                for idx, metrics in enumerate(eval_results):
                    if idx < len(detailed):
                        detailed[idx]["ragas_metrics"] = metrics.ragas.to_dict()
                        detailed[idx]["deepeval_metrics"] = metrics.deepeval.to_dict()

                logger.info("RAGAS/DeepEval batch evaluation completed successfully")
            except Exception as e:
                logger.error(f"RAGAS/DeepEval batch evaluation failed: {e}")
                # Keep the placeholder values on failure

        return detailed

    def _find_response_for_sequence(
        self,
        user_seq: int,
        responses: list,
        user_messages: list,
    ) -> Dict[str, Any]:
        """Find agent response for a given user message sequence."""
        if not responses:
            return {}

        # Find next user sequence
        next_user_seq = None
        for um in user_messages:
            um_seq = um.get("sequence_id", 0)
            if um_seq > user_seq:
                next_user_seq = um_seq
                break

        for resp in responses:
            seq = resp.get("sequence_id", 0)
            if seq > user_seq and (next_user_seq is None or seq < next_user_seq):
                return resp

        return responses[0] if responses else {}

    def _find_tool_for_sequence(
        self,
        user_seq: int,
        tools: list,
        user_messages: list,
    ) -> Dict[str, Any]:
        """Find tool call for a given user message sequence."""
        if not tools:
            return {}

        # Find next user sequence
        next_user_seq = None
        for um in user_messages:
            um_seq = um.get("sequence_id", 0)
            if um_seq > user_seq:
                next_user_seq = um_seq
                break

        for tool in tools:
            seq = tool.get("sequence_id", 0)
            if seq > user_seq and (next_user_seq is None or seq < next_user_seq):
                return tool

        return {}

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate the similarity ratio between two strings.
        Returns a float between 0 and 1, where 1 means identical.
        """
        from difflib import SequenceMatcher

        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    def _extract_latency_metrics(self) -> list:
        """Fetch runtime latency metrics from call_result.data or user_state.extra_data."""
        try:
            output = self.data.get("output")
            output_data = {}
            if isinstance(output, dict):
                output_data = output.get("data", {}) or {}
            elif hasattr(output, "data") and isinstance(output.data, dict):
                output_data = output.data

            latency_metrics = output_data.get("latency_metrics")
            if isinstance(latency_metrics, list):
                return latency_metrics

            if self.user_state and isinstance(self.user_state.extra_data, dict):
                extra_metrics = self.user_state.extra_data.get("latency_metrics")
                if isinstance(extra_metrics, list):
                    return extra_metrics
        except Exception as e:
            logger.warning(f"Could not extract latency_metrics: {e}")
        return []

    def _build_llm_latency_summary(
        self, eval_records: Dict[str, Any], latency_metrics: list
    ) -> Dict[str, Any]:
        """Build compact LLM latency summary for post-call results."""
        values = []

        try:
            if isinstance(eval_records, dict):
                for resp in eval_records.get("agent_responses", []) or []:
                    if not isinstance(resp, dict):
                        continue
                    latency = resp.get("llm_latency")
                    if isinstance(latency, (int, float)) and latency > 0:
                        values.append(float(latency))
        except Exception:
            pass

        try:
            if isinstance(eval_records, dict):
                for sample in eval_records.get("llm_latency_samples", []) or []:
                    if not isinstance(sample, dict):
                        continue
                    latency = sample.get("llm_latency")
                    if isinstance(latency, (int, float)) and latency > 0:
                        values.append(float(latency))
        except Exception:
            pass

        try:
            for metric in latency_metrics or []:
                if not isinstance(metric, dict):
                    continue
                for key in ("llm_latency", "realtime_latency"):
                    latency = metric.get(key)
                    if isinstance(latency, (int, float)) and latency > 0:
                        values.append(float(latency))
        except Exception:
            pass

        values = sorted(values)
        if not values:
            return {
                "count": 0,
                "avg": None,
                "min": None,
                "max": None,
                "p95": None,
                "unit": "seconds",
            }

        p95_idx = int(0.95 * (len(values) - 1))
        return {
            "count": len(values),
            "avg": round(sum(values) / len(values), 4),
            "min": round(values[0], 4),
            "max": round(values[-1], 4),
            "p95": round(values[p95_idx], 4),
            "unit": "seconds",
        }

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

        # Sequential: redial only if follow-up didn't schedule anything
        if not data["follow_up"].get("status"):
            summary_status = (data.get("summary") or {}).get("status")
            if summary_status in ["Abandoned", "Dropped"]:
                data["redial"] = await self.instant_redial()

        if self.is_in_redial:
            data["is_redial"] = True

        return data

"""
LiveKit Lite Agent - Minimal voice conversation agent.

Extends LiveKit's Agent with plugin integration and context management.
"""

import asyncio
import json
import os
import re
import unicodedata
from datetime import datetime
from typing import TYPE_CHECKING, Annotated, Any, AsyncIterable, List, Optional, Dict

from pydantic import Field

from super.core.voice.schema import CallStatusEnum
from super.core.voice.common.common import build_call_result
from super.core.voice.common.prefect import trigger_post_call
from super.core.voice.common.services import save_execution_log
from super.core.voice.workflows.in_call import InCallWorkflow
from super.core.voice.services.service_common import (
    estimate_tokens,
    get_model_context_limit,
)
from super_services.libs.core.timezone_utils import normalize_phone_number

# Conversation state import
try:
    from super.core.voice.livekit.conversation_state import (
        DynamicConversationState,
        TurnResponse,
        build_conversation_state,
    )

    CONVERSATION_INTELLIGENCE_AVAILABLE = True
except ImportError:
    CONVERSATION_INTELLIGENCE_AVAILABLE = False
    DynamicConversationState = None
    TurnResponse = None
    build_conversation_state = None

if TYPE_CHECKING:
    from livekit.agents import JobContext, llm, ToolError
    from super.core.voice.livekit.lite_handler import LiveKitLiteHandler
    from super.core.voice.schema import UserState

# Check LiveKit availability
try:
    from livekit.agents import JobContext
    from livekit.agents.voice import Agent, RunContext
    from livekit.agents import llm
    from livekit.agents.llm import function_tool, ToolError
    from livekit.agents import ChatContext, ChatMessage

    LIVEKIT_AVAILABLE = True
except ImportError:
    LIVEKIT_AVAILABLE = False
    JobContext = Any
    Agent = object
    ChatContext = Any
    ChatMessage = Any

    def function_tool(*args, **kwargs):
        """Stub decorator when LiveKit not available."""

        def decorator(func):
            return func

        if args and callable(args[0]):
            return args[0]
        return decorator


class LiveKitLiteAgent(Agent):
    """LiveKit Agent - minimal, non-blocking."""

    def __init__(
        self,
        handler: "LiveKitLiteHandler",
        user_state: "UserState",
        instructions: str,
        tools: Optional[List[Any]] = None,
        ctx: "JobContext" = None,
        config: Optional[Dict[str, Any]] = None,
        testing_mode: bool = False,
    ):
        super().__init__(instructions=instructions, tools=tools)
        self.testing_mode = testing_mode
        self.handler = handler
        self.user_state = user_state
        self.ctx = ctx
        self.config = config or {}
        self._logger = handler._logger.getChild("agent")
        self._max_turns = config.get("max_context_turns", 6) if config else 6
        self.memory_loaded = False

        # Token-aware context management
        llm_model = config.get("llm_model", "") if config else ""
        self._context_limit = get_model_context_limit(llm_model)
        # Reserve tokens for response (max_tokens) + safety margin
        max_tokens = config.get("llm_max_tokens", 350) if config else 350
        self._effective_context_limit = self._context_limit - max_tokens - 200
        self._logger.info(
            f"Context limit: {self._context_limit} tokens "
            f"(effective: {self._effective_context_limit} for model: {llm_model})"
        )

        # Build conversation state from config and instructions
        self._conv_state: Optional[DynamicConversationState] = None
        if CONVERSATION_INTELLIGENCE_AVAILABLE and build_conversation_state:
            self._conv_state = build_conversation_state(
                config=self.config,
                system_prompt=instructions,
            )

        # Realtime mode detection
        # In full realtime mode, TTS is not available - realtime LLM handles audio natively
        self._is_realtime_mode = config.get("llm_realtime", False) if config else False
        self._mixed_realtime_mode = (
            config.get("mixed_realtime_mode", False) if config else False
        )
        # Full realtime = realtime mode without mixed mode (no TTS available)
        self._is_full_realtime = (
            self._is_realtime_mode and not self._mixed_realtime_mode
        )

        # KB tool usage tracking for auto-inject fallback
        self._kb_tool_calls: int = 0

        if self._is_full_realtime:
            self._logger.info(
                "Full realtime mode: session.say() unavailable, using generate_reply()"
            )
        elif self._is_realtime_mode:
            self._logger.info("Mixed realtime mode: TTS available for session.say()")

    def _ensure_eval_records(self) -> Dict[str, Any]:
        """Ensure user_state.extra_data.eval_records exists and return it."""
        if not isinstance(self.user_state.extra_data, dict):
            self.user_state.extra_data = {}

        eval_records = self.user_state.extra_data.get("eval_records")
        if not isinstance(eval_records, dict):
            eval_records = {}
            self.user_state.extra_data["eval_records"] = eval_records

        if not isinstance(eval_records.get("tool_calls"), list):
            eval_records["tool_calls"] = []
        if not isinstance(eval_records.get("agent_responses"), list):
            eval_records["agent_responses"] = []
        if not isinstance(eval_records.get("user_messages"), list):
            eval_records["user_messages"] = []
        if not isinstance(eval_records.get("llm_latency_samples"), list):
            eval_records["llm_latency_samples"] = []
        if not isinstance(eval_records.get("sequence_counter"), int):
            eval_records["sequence_counter"] = 0

        return eval_records

    def _next_eval_sequence(self) -> int:
        eval_records = self._ensure_eval_records()
        eval_records["sequence_counter"] += 1
        return eval_records["sequence_counter"]

    def _to_eval_safe(self, value: Any, depth: int = 0) -> Any:
        """Convert nested values into JSON-safe shape for persistence."""
        if depth > 4:
            return str(value)
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        if isinstance(value, dict):
            return {str(k): self._to_eval_safe(v, depth + 1) for k, v in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [self._to_eval_safe(v, depth + 1) for v in value]
        return str(value)

    def _record_tool_call(
        self,
        tool_name: str,
        args: Optional[Dict[str, Any]] = None,
        result: Any = None,
        status: str = "success",
        error: Optional[str] = None,
    ) -> None:
        """Store tool call telemetry for post-call realtime eval."""
        try:
            eval_records = self._ensure_eval_records()
            eval_records["tool_calls"].append(
                {
                    "sequence_id": self._next_eval_sequence(),
                    "tool_name": tool_name,
                    "args": self._to_eval_safe(args or {}),
                    "result": self._to_eval_safe(result),
                    "status": status,
                    "error": error,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
        except Exception as e:
            self._logger.debug(f"Failed to record tool call for eval: {e}")

    def _tool_success(
        self, tool_name: str, args: Optional[Dict[str, Any]], result: Any
    ) -> Any:
        self._record_tool_call(
            tool_name=tool_name, args=args, result=result, status="success"
        )
        return result

    def _tool_failure(
        self,
        tool_name: str,
        args: Optional[Dict[str, Any]],
        error: str,
        result: Any = None,
    ) -> Any:
        self._record_tool_call(
            tool_name=tool_name,
            args=args,
            result=result,
            status="failure",
            error=error,
        )
        return result

    # === CORE TOOLS ===

    @function_tool(
        name="voicemail_detector",
        description="Call this tool if you have detected a voicemail system, AFTER hearing the voicemail greeting. Use when you detect an automated answering machine or voicemail greeting.",
    )
    async def detected_answering_machine(
        self,
        greeting_message: Annotated[
            str, Field(description="The voicemail greeting message detected")
        ] = "",
    ):
        """Call this tool if you have detected a voicemail system, AFTER hearing the voicemail greeting"""
        tool_args = {"greeting_message": greeting_message}
        await self.session.generate_reply(
            instructions="Leave a voicemail message letting the user know you'll call back later."
        )

        if not isinstance(self.user_state.extra_data, dict):
            self.user_state.extra_data = {}

        if self.user_state.extra_data.get("call_type") != "sdk":
            self.user_state.call_status = CallStatusEnum.VOICEMAIL
            self.user_state.end_time = datetime.utcnow()

            res = await build_call_result(self.user_state)
            await trigger_post_call(user_state=self.user_state, res=res)
            self.user_state.extra_data["post_call_triggered"] = True
            self._logger.info(
                f"{'='*100}\n\n[END_CALL_TOOL]  Triggering post call \n\n{'='*100}"
            )

        await asyncio.sleep(3)

        self._record_tool_call(
            tool_name="voicemail_detector",
            args=tool_args,
            result={"status": "voicemail_detected"},
        )
        await self.handler._handle_tool_end_call("voicemail_detected")

    @function_tool(
        name="handover_tool",
        description="Transfer an active call to another person such as a senior agent, supervisor, or specialized representative. Use when the user explicitly requests to speak with someone else, asks for escalation, or indicates a need for higher authority or specialized assistance.",
    )
    async def handover_call(
        self,
        reason: Annotated[
            str, Field(description="Brief reason for the transfer request")
        ] = "",
    ):
        tool_args = {"reason": reason}
        if self.config.get("handover_enabled"):
            await self.handler._stop_idle_monitor()

            number = self.config.get("handover_number")
            if isinstance(number, list):
                import random

                number = random.choice(number)

            from super.core.voice.livekit.telephony import SIPManager

            trunk_id = SIPManager.get_trunk_id(self.user_state.model_config or {})
            identity = f"idt_{number}"
            name = f"idt_{number}"

            if self.user_state.extra_data.get("handover_initiated"):
                return self._tool_success(
                    "handover_tool",
                    tool_args,
                    {"status": "handover call already initiated pls wait "},
                )

            if self.testing_mode:
                return self._tool_success(
                    "handover_tool",
                    tool_args,
                    {"status": "successfully transfered call  "},
                )

            self._logger.info(f"Transferring call to {number} with trunk: {trunk_id}")
            if number:
                number = normalize_phone_number(number)
                max_attempts = 2
                last_error = None

                for attempt in range(max_attempts):
                    try:
                        from livekit.agents.beta.workflows import WarmTransferTask
                        from super.core.voice.prompts.guidelines import (
                            HANOVER_INSTRUCTIONS,
                        )

                        transfer = WarmTransferTask(
                            target_phone_number=number,
                            sip_trunk_id=trunk_id,
                            chat_ctx=self.chat_ctx,
                            extra_instructions=HANOVER_INSTRUCTIONS,
                        )

                        result = await transfer

                        # WarmTransferTask may return ToolError as
                        # a value instead of raising it
                        if isinstance(result, ToolError):
                            raise result

                    except (ToolError, asyncio.TimeoutError, Exception) as e:
                        last_error = e
                        self._logger.warning(
                            f"Handover attempt {attempt + 1}/{max_attempts} "
                            f"failed: {e}"
                        )

                        if attempt < max_attempts - 1:
                            trunk_id = os.getenv("SIP_OUTBOUND_TRUNK_ID")
                            continue

                    else:
                        # Transfer succeeded — break out of retry loop
                        break
                else:
                    # Both attempts exhausted — re-enable audio and
                    # tell the caller the line is busy
                    self._logger.warning(
                        f"Handover failed after {max_attempts} attempts: "
                        f"{last_error}"
                    )
                    self.session.output.set_audio_enabled(True)
                    self.session.input.set_audio_enabled(True)

                    self.user_state.transcript.append(
                        {
                            "role": "system",
                            "type": "handover call",
                            "message": "human agent busy",
                        }
                    )
                    await self.session.generate_reply(
                        instructions=(
                            "The line is busy right now. "
                            "Continue the conversation and ask "
                            "if there is anything else you can "
                            "help with."
                        )
                    )
                    return self._tool_success(
                        "handover_tool",
                        tool_args,
                        {
                            "status": "user busy",
                            "instructions": (
                                "the handover person is busy, "
                                "continue the conversation"
                            ),
                        },
                    )

                # Success path — reached via break from retry loop
                self._logger.info(f"Call transfer complete: {result}")
                self.user_state.transcript.append(
                    {
                        "role": "system",
                        "type": "handover call",
                        "message": "call successfully handed over to human agent",
                    }
                )

                self.session.output.set_audio_enabled(False)
                self.session.input.set_audio_enabled(False)

                if not isinstance(self.user_state.extra_data, dict):
                    self.user_state.extra_data = {}

                self.user_state.extra_data["handover_initiated"] = True

                await save_execution_log(
                    self.user_state.task_id,
                    "handover_initiated",
                    "completed",
                    {"status": "handover_initiated"},
                )

                in_call_analyzer = InCallWorkflow(
                    user_state=self.user_state, logger=self._logger
                )
                handover_data = await in_call_analyzer.generate_handover_summary()

                from super.core.voice.common.common import (
                    send_web_notification,
                )

                await send_web_notification(
                    "completed",
                    "handover_initiated",
                    self.user_state,
                    "handover call picked up by executive",
                    payload_data=handover_data,
                )

                try:
                    room = self.ctx.room
                    self._logger.info(
                        f"Setting up multi-participant transcription. "
                        f"Remote participants: "
                        f"{list(room.remote_participants.keys())}"
                    )

                    for p in room.remote_participants.values():
                        self._logger.info(
                            f"Starting transcription for "
                            f"existing participant: {p.identity}"
                        )
                        await self.handler._start_participant_transcription(p, room)

                    self._logger.info(
                        "Started multi-participant transcription " "after handover"
                    )

                except Exception as e:
                    import traceback

                    self._logger.error(
                        f"Failed to setup multi-participant "
                        f"transcription: {e}\n"
                        f"{traceback.format_exc()}"
                    )

                return self._tool_success(
                    "handover_tool", tool_args, {"status": "handover call completed"}
                )

        await self.handler._start_idle_monitor()
        return self._tool_success(
            "handover_tool", tool_args, {"status": "cant transfer call"}
        )

    @function_tool(
        name="get_past_calls",
        description="Retrieve the user's recent past call records. Returns transcripts and metadata of the last few calls associated with the user's phone number. Use when you need to remember or reference previous conversations, understand past issues, or continue a previous topic.",
    )
    async def get_past_calls(
        self,
        query: Annotated[
            str, Field(description="Optional search query to filter past calls")
        ] = "",
    ):
        tool_args = {"query": query}
        if self.testing_mode:
            return self._tool_success(
                "get_past_calls",
                tool_args,
                {"status": "call has been fetched successfully"},
            )
        if self.config.get("enable_memory") and not self.memory_loaded:
            chat_context_data = None
            if self.user_state and self.user_state.extra_data:
                if isinstance(self.user_state.extra_data, dict):
                    chat_context_data = (
                        self.user_state.extra_data.get("data", {})
                        .get("pre_call_result", {})
                        .get("chat_context")
                    )

                elif isinstance(self.user_state.extra_data, str):
                    chat_context_data = self.user_state.extra_data

            else:
                numbers = [self.user_state.contact_number]

                if self.self.user_state.contact_number.startswith("0"):
                    numbers.append(self.self.user_state.contact_number[1:])
                    from super_services.db.services.models.task import TaskModel

                    list(
                        TaskModel._get_collection()
                        .find(
                            {
                                "$or": [
                                    {"input.contact_number": {"$in": numbers}},
                                    {"output.contact_number": {"$in": numbers}},
                                    {"input.number": {"$in": numbers}},
                                    {"output.customer": {"$in": numbers}},
                                ],
                                "assignee": self.config.get("agent_id"),
                            },
                            {"output.transcript": 1},
                        )
                        .sort([("created", -1)])
                        .limit(5)
                    )

            return self._tool_success(
                "get_past_calls", tool_args, {"call_details": chat_context_data}
            )

        return self._tool_success(
            "get_past_calls",
            tool_args,
            {"call_details": "unable top get recent calls data"},
        )

    @function_tool(
        name="create_followup_or_callback",
        description="Schedule a follow-up or callback request. Use when the user asks to be called later or requests a callback at a specific or unspecified time. The tool will collect the required time from the user and prepare the callback request.",
    )
    async def create_call_back(
        self,
        preferred_time: Annotated[
            str, Field(description="User's preferred callback time, if provided")
        ] = "",
    ):
        tool_args = {"preferred_time": preferred_time}
        if self.config.get("follow_up_enabled"):
            chat_ctx = self.chat_ctx.copy()
            chat_ctx.add_message(
                role="system",
                content=f"\n[callback and folloup guidelines]\n"
                + """
                1. ask user about the time when they will be avaible to initiate a call,
                2. if user has alredy provided with a time of call just say ok i will call you back at the given time
                """,
            )
            await self.update_chat_ctx(chat_ctx)

            return self._tool_success(
                "create_followup_or_callback",
                tool_args,
                {
                    "instructions": "ask user about the time when they will be avaible to initiate a call",
                    "response": "if user has alredy provided with a time of call just say ok i will call you back at the given time",
                },
            )
        else:
            return self._tool_success(
                "create_followup_or_callback",
                tool_args,
                {
                    "instructions": "ask user about the time when they will be avaible to initiate a call",
                    "response": "ok i will process your request",
                },
            )

    @function_tool(
        name="get_docs",
        description=(
            "Search the knowledge base for relevant information. "
            "ALWAYS call this tool if answer is not in context before answering domain-specific, factual, "
            "or product/service-related questions from the user."
        ),
    )
    async def get_docs(
        self,
        _context: RunContext,
        query: Annotated[str, Field(description="Query to get relevant documents")],
        kb_name: Annotated[str, Field(description="Knowledge Base Name")] = "",
    ):
        """Get documents from knowledge base."""
        tool_args = {"query": query, "kb_name": kb_name}
        try:
            self._kb_tool_calls += 1
            self._logger.info(f"Getting docs with query: {query}, kb_name: {kb_name}")

            kb_manager = getattr(self.handler, "_kb_manager", None)

            if kb_manager is None:
                # Wait for background KB warmup (started in preload_agent) instead of re-init
                kb_ready = getattr(self.handler, "_kb_ready", None)
                if kb_ready is not None:
                    try:
                        await asyncio.wait_for(kb_ready.wait(), timeout=5.0)
                        kb_manager = getattr(self.handler, "_kb_manager", None)
                    except asyncio.TimeoutError:
                        self._logger.warning("KB warmup timeout in get_docs")

            # Fallback: lazy init if background warmup didn't produce a manager
            if kb_manager is None:
                from super.core.voice.managers.knowledge_base import (
                    KnowledgeBaseManager,
                )

                kb_manager = KnowledgeBaseManager(
                    logger=self._logger,
                    session_id=self.handler._session_id,
                    user_state=self.user_state,
                    config=self.config,
                )
                await kb_manager._init_context_retrieval()
                self.handler._kb_manager = kb_manager

            docs = await kb_manager.get_docs(
                query=query,
                kn_name=kb_name if kb_name else None,
                user_state=self.user_state,
            )

            if isinstance(docs, dict) and "error" in docs:
                self._logger.warning(f"KB lookup returned error: {docs}")
                result = (None, json.dumps(docs))
                self._tool_failure("get_docs", tool_args, str(docs), result=result)
                return result

            if docs:
                doc_list = [
                    {
                        f"Context {i}": doc.content
                        if hasattr(doc, "content")
                        else str(doc)
                    }
                    for i, doc in enumerate(docs)
                ]
                result = {"Reference Docs": doc_list}
                self._logger.info(f"Retrieved {len(doc_list)} documents")
                output = (None, json.dumps(result))
                self._tool_success("get_docs", tool_args, output)
                return output

            self._logger.info("No documents found for query")
            output = (None, json.dumps({"Reference Docs": []}))
            self._tool_success("get_docs", tool_args, output)
            return output

        except Exception as e:
            self._logger.error(f"Error getting docs: {e}")
            output = (
                None,
                json.dumps(
                    {"error": str(e), "message": "Unable to retrieve information"}
                ),
            )
            self._tool_failure("get_docs", tool_args, str(e), result=output)
            return output

    @function_tool(
        name="end_call",
        description="""End the current call and disconnect gracefully.
        Use this tool ONLY when:
        - User explicitly says goodbye (bye, goodbye, see you, take care, etc.)
        - User confirms they want to end after you've said goodbye
        - User says they're done and confirms they don't have more questions
        - User thanks you and indicates the conversation is complete

        Do NOT use this tool when:
        - User says "okay" or "ok" as a simple acknowledgment mid-conversation
        - User says "done" but the conversation is still ongoing
        - User is asking a question or making a request
        - You're unsure if the user wants to end - ask for confirmation first""",
    )
    async def end_call_tool(
        self,
        _context: RunContext,
        reason: Annotated[
            str, Field(description="Brief reason why the call is ending")
        ] = "user_goodbye",
    ):
        """End the call gracefully when user indicates they want to finish."""
        tool_args = {"reason": reason}
        self._logger.info(f"[END_CALL_TOOL] Called with reason: {reason}")

        if self.testing_mode:
            return self._tool_success(
                "end_call", tool_args, {"status": "call ended successfully"}
            )
        # Capture conversation quality metrics before ending
        call_summary = None
        if self._conv_state:
            self._conv_state.task_id = self.user_state.task_id or ""
            self._conv_state.session_id = self.handler._session_id or ""
            self._conv_state.agent_handle = self.config.get("agent_handle", "")

            # Log quality summary
            self._logger.info(self._conv_state.get_quality_log_line())

            # Get full summary for storage
            call_summary = self._conv_state.get_call_summary_dict(end_reason=reason)

            # Persist metrics to file
            self._conv_state.persist_quality_metrics(reason=reason)

            # Log human-readable summary
            self._logger.info(
                f"\n{self._conv_state.build_call_summary(end_reason=reason)}"
            )

        if not isinstance(self.user_state.extra_data, dict):
            self.user_state.extra_data = {}

        # Store call summary in extra_data for post-call processing
        if call_summary:
            self.user_state.extra_data["conversation_summary"] = call_summary

        if self.user_state.extra_data.get("call_type") != "sdk":
            self.user_state.call_status = CallStatusEnum.COMPLETED
            self.user_state.end_time = datetime.utcnow()

            res = await build_call_result(self.user_state)
            await trigger_post_call(user_state=self.user_state, res=res)
            self.user_state.extra_data["post_call_triggered"] = True

            self._logger.info(
                f"{'='*100}\n\n[END_CALL_TOOL]  Triggering post call \n\n{'='*100}"
            )

        await self.handler._handle_tool_end_call(reason)

        return self._tool_success(
            "end_call",
            tool_args,
            {
                "status": "ending_call",
                "message": "Call ending gracefully. Say a brief goodbye to the user.",
            },
        )

    # === CONVERSATION TOOLS ===

    @function_tool(
        name="record_user_info",
        description="""Record information provided by the user.
        Use when user shares: name, preferred time, contact method, etc.""",
    )
    async def record_user_info(
        self,
        _context: RunContext,
        key: Annotated[
            str,
            Field(
                description="Info type (e.g., 'name', 'visit_date', 'contact_method')"
            ),
        ],
        value: Annotated[str, Field(description="The value to record")],
    ) -> Dict[str, Any]:
        """Record user information."""
        tool_args = {"key": key, "value": value}
        if self._conv_state:
            self._conv_state.record_user_info_item(key, value)
            self._logger.info(f"[USER_INFO] {key}={value}")
            return self._tool_success(
                "record_user_info",
                tool_args,
                {"status": "recorded", "key": key, "value": value},
            )
        return self._tool_success("record_user_info", tool_args, {"status": "no_state"})

    @function_tool(
        name="mark_topic_covered",
        description="""Mark a topic as covered after discussing it.
        Use when you've explained a topic from the checklist.""",
    )
    async def mark_topic_covered(
        self,
        _context: RunContext,
        topic_id: Annotated[
            str,
            Field(
                description="The topic ID from checklist (e.g., 'pricing', 'location')"
            ),
        ],
    ) -> Dict[str, Any]:
        """Mark a checklist topic as covered."""
        tool_args = {"topic_id": topic_id}
        if self._conv_state:
            self._conv_state.mark_block_delivered(topic_id)
            progress = self._conv_state.get_delivery_progress()
            self._logger.info(
                f"[TOPIC] Marked covered: {topic_id} "
                f"({progress['delivered']}/{progress['total']})"
            )
            return self._tool_success(
                "mark_topic_covered",
                tool_args,
                {
                    "status": "marked",
                    "topic": topic_id,
                    "progress": progress,
                },
            )
        return self._tool_success(
            "mark_topic_covered", tool_args, {"status": "no_state"}
        )

    @function_tool(
        name="report_breakdown",
        description="""Report a conversation breakdown when you detect confusion.
        Use when:
        - User asks to repeat (non_understanding)
        - User says you misunderstood them (misunderstanding)
        - User seems confused about what you said""",
    )
    async def report_breakdown(
        self,
        _context: RunContext,
        breakdown_type: Annotated[
            str, Field(description="Type: 'non_understanding' or 'misunderstanding'")
        ],
        reason: Annotated[str, Field(description="Brief reason for breakdown")] = "",
    ) -> Dict[str, Any]:
        """Report a conversation breakdown for repair handling."""
        tool_args = {"breakdown_type": breakdown_type, "reason": reason}
        if not self._conv_state:
            return self._tool_success(
                "report_breakdown", tool_args, {"status": "no_state"}
            )

        valid_types = ["non_understanding", "misunderstanding"]
        if breakdown_type not in valid_types:
            breakdown_type = "non_understanding"

        if self._conv_state.in_repair:
            self._conv_state.increment_repair_retry()
        else:
            self._conv_state.enter_repair(breakdown_type)

        # Get repair strategy
        repair_block = self._conv_state.get_repair_block()
        repair_strategy = repair_block.content if repair_block else None

        self._logger.info(
            f"[BREAKDOWN] {breakdown_type} reported, "
            f"retry={self._conv_state.repair_retry_count}, "
            f"reason={reason}"
        )

        return self._tool_success(
            "report_breakdown",
            tool_args,
            {
                "status": "repair_mode",
                "breakdown_type": breakdown_type,
                "retry_count": self._conv_state.repair_retry_count,
                "suggested_strategy": repair_strategy,
                "instruction": "Use the suggested strategy to repair the conversation",
            },
        )

    @function_tool(
        name="mark_objective_achieved",
        description="""Mark the conversation objective as achieved.
        Use when user accepts the CTA (e.g., agrees to book visit, confirms interest).""",
    )
    async def mark_objective_achieved(
        self,
        _context: RunContext,
        outcome: Annotated[
            str,
            Field(
                description="Outcome: 'primary_success', 'fallback_success', or 'declined'"
            ),
        ] = "primary_success",
    ) -> Dict[str, Any]:
        """Mark conversation objective as achieved."""
        tool_args = {"outcome": outcome}
        if not self._conv_state:
            return self._tool_success(
                "mark_objective_achieved", tool_args, {"status": "no_state"}
            )

        self._conv_state.objective_achieved = outcome in [
            "primary_success",
            "fallback_success",
        ]
        self._conv_state.objective_outcome = outcome

        self._logger.info(f"[OBJECTIVE] Marked: {outcome}")

        return self._tool_success(
            "mark_objective_achieved",
            tool_args,
            {
                "status": "recorded",
                "objective_achieved": self._conv_state.objective_achieved,
                "outcome": outcome,
            },
        )

    # === LLM NODE OVERRIDE (Structured Output) ===

    # async def llm_node(
    #     self,
    #     chat_ctx: "llm.ChatContext",
    #     tools: List[Any],
    #     model_settings: Any,
    # ) -> AsyncIterable[Any]:
    #     """
    #     Override llm_node for structured output processing.

    #     Flow:
    #     1. Inject conversation state context with JSON schema instruction
    #     2. Yield chunks from default LLM
    #     3. Collect full response and parse as TurnResponse
    #     4. Apply structured data to conversation state
    #     """
    #     # Inject structured output instruction
    #     if self._conv_state:
    #         state_context = self._build_structured_context()
    #         chat_ctx.add_message(role="system", content=state_context)

    #     # Collect response while yielding chunks
    #     full_response = ""

    #     async for chunk in Agent.default.llm_node(self, chat_ctx, tools, model_settings):
    #         # Extract text from chunk if available
    #         if hasattr(chunk, "choices") and chunk.choices:
    #             delta = chunk.choices[0].delta
    #             if hasattr(delta, "content") and delta.content:
    #                 full_response += delta.content
    #         yield chunk

    #     # Post-process: parse and apply structured response
    #     if full_response and self._conv_state:
    #         self._process_llm_response(full_response)

    # def _build_structured_context(self) -> str:
    #     """Build context with JSON schema instruction for structured output."""
    #     if not self._conv_state:
    #         return ""

    #     # Get base context (checklist, goal, repair)
    #     base_context = self._conv_state.build_llm_context()

    #     # Add structured output instruction
    #     topic_ids = [b.id for b in self._conv_state.get_topics()]

    #     structured_instruction = f"""
    #     {base_context}

    #     [RESPONSE TRACKING]
    #     After your spoken response, add a JSON block to track state:
    #     ```json
    #     {{"covered": ["topic_id"], "user_info": {{"key": "value"}}, "objective_outcome": null}}
    #     ```

    #     Available topic IDs: {topic_ids}
    #     - covered: List topic IDs you just explained (empty if none)
    #     - user_info: Any info user shared (name, preferred_time, etc.)
    #     - objective_outcome: "primary_success" if user accepted CTA, "declined" if rejected, null otherwise

    #     The JSON block will be parsed automatically - your spoken words come first.
    #     """
    #     return structured_instruction

    # Regex to match LLM-generated command tags like <Transfer the call here>, <Disconnect the call>
    _COMMAND_TAG_RE = re.compile(r"<[^>]{3,}>")
    _COMMAND_TAG_START_RE = re.compile(r"<\s*[A-Za-z/]")
    _WHITESPACE_RE = re.compile(r"\s+")
    _NO_AUDIO_FRAMES_ERR = "no audio frames were pushed for text"

    # Patterns for LLM-generated code/tool blocks that must not reach TTS.
    _TOOL_CODE_START_RE = re.compile(r"tool_code\b", re.IGNORECASE)
    _PRINT_CALL_RE = re.compile(r"print\s*\(", re.IGNORECASE)
    # Fenced code blocks: ```lang ... ```
    _CODE_FENCE_RE = re.compile(r"```[\s\S]*?```")
    # Bare function-call syntax: word.word(...) with nested parens
    _BARE_FUNC_CALL_RE = re.compile(r"\b\w+\.\w+\([^)]*(?:\([^)]*\)[^)]*)*\)")

    @classmethod
    def _find_matching_paren_end(cls, text: str, open_paren_idx: int) -> Optional[int]:
        """Return index after matching ')' for an opening '(' or None if incomplete."""
        depth = 0
        in_single = False
        in_double = False
        escaped = False

        for idx in range(open_paren_idx, len(text)):
            ch = text[idx]

            if escaped:
                escaped = False
                continue

            if ch == "\\" and (in_single or in_double):
                escaped = True
                continue

            if ch == "'" and not in_double:
                in_single = not in_single
                continue

            if ch == '"' and not in_single:
                in_double = not in_double
                continue

            if in_single or in_double:
                continue

            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    return idx + 1

        return None

    @classmethod
    def _find_incomplete_command_tag_start(cls, buffer: str) -> int:
        """Find start index of trailing incomplete <command> tag, else -1."""
        last_lt = buffer.rfind("<")
        if last_lt == -1:
            return -1

        last_gt = buffer.rfind(">")
        if last_lt < last_gt:
            return -1

        suffix = buffer[last_lt:]
        if cls._COMMAND_TAG_START_RE.match(suffix):
            return last_lt
        return -1

    @classmethod
    def _find_incomplete_tool_code_start(cls, buffer: str) -> int:
        """Find start index of trailing incomplete tool_code print(...) block."""
        last_match = None
        for match in cls._TOOL_CODE_START_RE.finditer(buffer):
            last_match = match

        if not last_match:
            return -1

        tool_start = last_match.start()
        print_match = cls._PRINT_CALL_RE.search(buffer, pos=tool_start)
        if not print_match:
            return tool_start

        open_paren_idx = buffer.find("(", print_match.start(), print_match.end())
        if open_paren_idx == -1:
            return tool_start

        close_idx = cls._find_matching_paren_end(buffer, open_paren_idx)
        if close_idx is None:
            return tool_start

        return -1

    @classmethod
    def _strip_tool_code_blocks(cls, text: str) -> str:
        """Remove complete tool_code print(...) blocks with nested-paren support."""
        cursor = 0
        parts: list[str] = []

        while cursor < len(text):
            match = cls._TOOL_CODE_START_RE.search(text, cursor)
            if not match:
                parts.append(text[cursor:])
                break

            parts.append(text[cursor : match.start()])
            parts.append(" ")

            print_match = cls._PRINT_CALL_RE.search(text, pos=match.end())
            if not print_match:
                cursor = match.end()
                continue

            open_paren_idx = text.find("(", print_match.start(), print_match.end())
            if open_paren_idx == -1:
                cursor = print_match.end()
                continue

            close_idx = cls._find_matching_paren_end(text, open_paren_idx)
            if close_idx is None:
                cursor = len(text)
                break

            cursor = close_idx

        return "".join(parts)

    @classmethod
    def _split_processable_tts_text(cls, buffer: str) -> tuple[str, str]:
        """
        Split text into processable prefix and carry-over suffix.

        If the buffer ends with an incomplete command tag start, keep it in the
        carry-over so split tags across streamed chunks are removed correctly.
        """
        if not buffer:
            return "", ""

        candidates: list[int] = []

        incomplete_tag_start = cls._find_incomplete_command_tag_start(buffer)
        if incomplete_tag_start >= 0:
            candidates.append(incomplete_tag_start)

        incomplete_tool_start = cls._find_incomplete_tool_code_start(buffer)
        if incomplete_tool_start >= 0:
            candidates.append(incomplete_tool_start)

        if not candidates:
            return buffer, ""

        cut_idx = min(candidates)
        return buffer[:cut_idx], buffer[cut_idx:]

    @classmethod
    def _strip_non_speakable(cls, text: str) -> str:
        """Remove tool_code blocks, code fences, bare function calls, and command tags."""
        result = cls._strip_tool_code_blocks(text)
        result = cls._CODE_FENCE_RE.sub(" ", result)
        result = cls._BARE_FUNC_CALL_RE.sub(" ", result)
        result = cls._COMMAND_TAG_RE.sub(" ", result)
        result = cls._WHITESPACE_RE.sub(" ", result)
        return result

    async def tts_node(
        self, text: AsyncIterable[str], model_settings: Any
    ) -> AsyncIterable[Any]:
        """Override tts_node to strip non-speakable content before TTS synthesis.

        Filters out:
        - LLM command tags (<Transfer the call>, etc.)
        - Gemini-style tool_code blocks (tool_code\\nprint(...))
        - Fenced code blocks (```...```)
        - Bare function-call snippets

        In realtime mode, text is streamed directly without filtering.
        """

        # Realtime mode: bypass all text filtering, stream raw text to TTS
        if self._is_realtime_mode:
            async for frame in Agent.default.tts_node(self, text, model_settings):
                yield frame
            return

        sanitized_chunks: list[str] = []

        async def _filtered_text() -> AsyncIterable[str]:
            pending = ""
            async for chunk in text:
                if not chunk:
                    continue

                pending += chunk
                processable, pending = self._split_processable_tts_text(pending)

                if not processable:
                    continue

                cleaned = self._strip_non_speakable(processable)
                if cleaned.strip():
                    sanitized_chunks.append(cleaned)
                    yield cleaned

            # Best-effort flush: drop dangling partial command tags.
            if pending:
                if not (pending.startswith("<") and ">" not in pending):
                    cleaned = self._strip_non_speakable(pending)
                    if cleaned.strip():
                        sanitized_chunks.append(cleaned)
                        yield cleaned

        emitted_frames = False
        try:
            async for frame in Agent.default.tts_node(
                self, _filtered_text(), model_settings
            ):
                emitted_frames = True
                yield frame
            return
        except Exception as exc:
            # Retry once with an ASCII-safe utterance when provider returns zero audio.
            if emitted_frames or self._NO_AUDIO_FRAMES_ERR not in str(exc).lower():
                raise

            fallback_text = self._build_ascii_safe_tts_text(" ".join(sanitized_chunks))
            if not fallback_text:
                raise

            self._logger.warning(
                "[TTS_SANITIZE] No audio frames from provider; retrying with ASCII-safe text."
            )

            async def _fallback_text_stream() -> AsyncIterable[str]:
                yield fallback_text

            async for frame in Agent.default.tts_node(
                self, _fallback_text_stream(), model_settings
            ):
                yield frame

    @classmethod
    def _build_ascii_safe_tts_text(cls, text: str) -> str:
        """Build a conservative ASCII fallback text for providers that fail on mixed scripts."""
        if not text:
            return ""

        normalized = text.replace("&", " and ")
        normalized = (
            unicodedata.normalize("NFKD", normalized)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
        normalized = cls._WHITESPACE_RE.sub(" ", normalized).strip()
        return normalized

    def _process_llm_response(self, response: str) -> None:
        """Parse LLM response for structured data and apply to state."""
        if not self._conv_state:
            return

        # Record response for quality tracking
        self._record_agent_response(response)

        # Try to extract JSON block from response
        # Pattern 1: Code block ```json {...} ```
        json_match = re.search(r"```json\s*(\{.*?\})\s*```", response, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                self._apply_turn_response(data)
                return
            except json.JSONDecodeError as e:
                self._logger.debug(f"[STRUCTURED] Code block JSON parse failed: {e}")

        # Pattern 2: Inline JSON - find {"covered" and parse until valid JSON
        json_start = response.find('{"covered"')
        if json_start != -1:
            # Try to parse JSON from this point
            for end_pos in range(json_start + 20, len(response) + 1):
                try:
                    candidate = response[json_start:end_pos]
                    if candidate.count("{") == candidate.count("}"):
                        data = json.loads(candidate)
                        self._apply_turn_response(data)
                        return
                except json.JSONDecodeError:
                    continue
        else:
            # Fallback: use heuristic detection
            self._detect_covered_topics_heuristic(response)

    def _apply_turn_response(self, data: Dict[str, Any]) -> None:
        """Apply parsed structured response to conversation state."""
        if not self._conv_state:
            return

        # Mark covered topics
        covered = data.get("covered", [])
        for topic_id in covered:
            if isinstance(topic_id, str):
                self._conv_state.mark_block_delivered(topic_id)
                self._logger.info(f"[STRUCTURED] Marked covered: {topic_id}")

        # Record user info
        user_info = data.get("user_info", {})
        for key, value in user_info.items():
            if key and value:
                self._conv_state.record_user_info_item(key, value)
                self._logger.info(f"[STRUCTURED] User info: {key}={value}")

        # Check objective outcome
        outcome = data.get("objective_outcome")
        if outcome in ["primary_success", "fallback_success", "declined"]:
            self._conv_state.objective_achieved = outcome in [
                "primary_success",
                "fallback_success",
            ]
            self._conv_state.objective_outcome = outcome
            self._logger.info(f"[STRUCTURED] Objective: {outcome}")

        # Log progress
        progress = self._conv_state.get_delivery_progress()
        self._logger.info(
            f"[STRUCTURED] Progress: {progress['delivered']}/{progress['total']} topics"
        )

    def _detect_covered_topics_heuristic(self, response: str) -> None:
        """Fallback: detect covered topics from response text using heuristics."""
        if not self._conv_state:
            return

        response_lower = response.lower()
        topics = self._conv_state.get_topics()

        for topic in topics:
            if topic.delivered:
                continue

            # Check if topic content keywords appear in response
            topic_keywords = topic.id.replace("_", " ").split()
            content_keywords = topic.content.lower().split()[:5]

            # Match if multiple keywords found
            matches = sum(
                1 for kw in topic_keywords + content_keywords if kw in response_lower
            )
            if matches >= 2:
                self._conv_state.mark_block_delivered(topic.id)
                self._logger.info(f"[HEURISTIC] Likely covered: {topic.id}")

    # === LIFECYCLE ===

    async def update_chat_ctx(
        self,
        chat_ctx: "llm.ChatContext",
        *,
        exclude_invalid_function_calls: bool = True,
    ) -> None:
        try:
            if hasattr(super(), "update_chat_ctx"):
                await super().update_chat_ctx(
                    chat_ctx,
                    exclude_invalid_function_calls=exclude_invalid_function_calls,
                )
                self._logger.info("Chat context updated successfully")
            else:
                self._logger.warning("Parent Agent does not support update_chat_ctx")
        except Exception as e:
            self._logger.error(f"Failed to update chat context: {e}")

    async def load_previous_conversations(self, chat_context_data: str) -> None:
        if not chat_context_data:
            self._logger.debug("No previous conversations to load")
            return

        try:
            # Token-aware truncation of previous conversations
            # Reserve ~50% of effective context for conversation history
            max_history_tokens = self._effective_context_limit // 2
            history_tokens = estimate_tokens(chat_context_data)

            if history_tokens > max_history_tokens:
                # Truncate from the beginning, keeping recent history
                target_chars = max_history_tokens * 4  # Approx 4 chars per token
                chat_context_data = chat_context_data[-target_chars:]
                # Find first complete line to avoid mid-sentence truncation
                newline_idx = chat_context_data.find("\n")
                if newline_idx > 0 and newline_idx < 500:
                    chat_context_data = chat_context_data[newline_idx + 1 :]
                self._logger.info(
                    f"Truncated previous conversations: {history_tokens} -> "
                    f"{estimate_tokens(chat_context_data)} tokens"
                )

            chat_ctx = self.chat_ctx.copy()
            chat_ctx.add_message(
                role="system",
                content=f"\n[previous conversations with user ]\n" + chat_context_data,
            )
            await self.update_chat_ctx(chat_ctx)
            self._logger.info("Previous conversations loaded into chat context")
            self.memory_loaded = True
        except Exception as e:
            self._logger.warning(f"Failed to load previous conversations: {e}")

    async def on_user_turn_completed(
        self,
        turn_ctx: "ChatContext",
        new_message: "ChatMessage",
    ) -> None:
        """Turn handler with quality tracking and conditional context pruning.

        IMPORTANT: Only modifies turn_ctx.items when truncation is actually needed.
        Unnecessary reassignment triggers preemptive_generation to cancel and re-issue
        the LLM request (see agents#4219), doubling latency and token costs.
        """
        if self._conv_state:
            self._conv_state.increment_turn()

            # Detect potential breakdown from user message
            if new_message and hasattr(new_message, "content"):
                user_text = str(new_message.content).lower()
                self._detect_breakdown(user_text)

        # Token-aware context pruning — only modify turn_ctx when needed
        if hasattr(turn_ctx, "messages"):
            current_messages = turn_ctx.messages()
            truncated_messages = self._truncate_context_to_limit(current_messages)

            # Only reassign items if truncation actually changed the message list
            if len(truncated_messages) < len(current_messages):
                current_items = turn_ctx.items
                non_message_items = [
                    item
                    for item in current_items
                    if not hasattr(item, "role")
                    or getattr(item, "role", "") not in ("user", "assistant", "system")
                ]
                turn_ctx.items = non_message_items + truncated_messages

    def _truncate_context_to_limit(self, messages: List[Any]) -> List[Any]:
        """Truncate messages to fit within context limit, preserving system + recent turns."""
        if not messages:
            return messages

        # Separate system messages from conversation
        sys_msgs = [m for m in messages if getattr(m, "role", "") == "system"]
        conv_msgs = [
            m for m in messages if getattr(m, "role", "") in ("user", "assistant")
        ]

        # Calculate current token usage
        def msg_tokens(m: Any) -> int:
            content = getattr(m, "content", "")
            if isinstance(content, list):
                content = " ".join(str(c) for c in content)
            return estimate_tokens(str(content))

        sys_tokens = sum(msg_tokens(m) for m in sys_msgs)
        conv_tokens = sum(msg_tokens(m) for m in conv_msgs)
        total_tokens = sys_tokens + conv_tokens

        # If within limit, also apply turn-based pruning as secondary limit
        if total_tokens <= self._effective_context_limit:
            if len(conv_msgs) > self._max_turns * 2:
                conv_msgs = conv_msgs[-(self._max_turns * 2) :]
            return sys_msgs[-1:] + conv_msgs if sys_msgs else conv_msgs

        # Need to truncate - first try removing old conversation turns
        self._logger.warning(
            f"Context overflow: {total_tokens} tokens > {self._effective_context_limit} limit"
        )

        # Keep only the most recent system message
        sys_msgs = sys_msgs[-1:] if sys_msgs else []
        sys_tokens = sum(msg_tokens(m) for m in sys_msgs)

        # If system message alone exceeds limit, truncate it
        if sys_tokens > self._effective_context_limit * 0.6:
            self._logger.warning(
                f"System message too large ({sys_tokens} tokens), truncating"
            )
            if sys_msgs:
                sys_content = str(getattr(sys_msgs[0], "content", ""))
                target_chars = int(self._effective_context_limit * 0.5 * 4)
                truncated_content = sys_content[:target_chars]
                # Preserve the message structure by creating a new-like object
                # We'll just modify in place if possible or rebuild
                try:
                    sys_msgs[0].content = truncated_content + "\n[...truncated...]"
                except (AttributeError, TypeError):
                    pass  # If immutable, skip - will still truncate conv
                sys_tokens = estimate_tokens(truncated_content)

        # Calculate remaining budget for conversation
        conv_budget = self._effective_context_limit - sys_tokens - 100  # Safety margin

        # Remove oldest conversation messages until within budget
        while conv_msgs and sum(msg_tokens(m) for m in conv_msgs) > conv_budget:
            removed = conv_msgs.pop(0)
            self._logger.debug(
                f"Removed old message ({msg_tokens(removed)} tokens) to fit context"
            )

        # Also apply max_turns limit
        if len(conv_msgs) > self._max_turns * 2:
            conv_msgs = conv_msgs[-(self._max_turns * 2) :]

        final_tokens = sys_tokens + sum(msg_tokens(m) for m in conv_msgs)
        self._logger.info(
            f"Context truncated: {total_tokens} -> {final_tokens} tokens "
            f"({len(conv_msgs)} conversation messages)"
        )

        return sys_msgs + conv_msgs

    def _detect_breakdown(self, user_text: str) -> None:
        """Detect conversation breakdown from user message."""
        if not self._conv_state:
            return

        # Non-understanding indicators
        non_understanding_patterns = [
            "what",
            "huh",
            "sorry",
            "repeat",
            "again",
            "samajh nahi",
            "kya bola",
            "pardon",
            "didn't catch",
            "can't hear",
        ]

        # Misunderstanding indicators
        misunderstanding_patterns = [
            "no i meant",
            "that's not what",
            "i said",
            "maine kaha",
            "galat",
            "wrong",
            "not that",
            "actually i want",
        ]

        # Check for non-understanding
        if any(p in user_text for p in non_understanding_patterns):
            if self._conv_state.in_repair:
                self._conv_state.increment_repair_retry()
            else:
                self._conv_state.enter_repair("non_understanding")
            self._logger.info(
                f"[BREAKDOWN] non_understanding detected, retry={self._conv_state.repair_retry_count}"
            )
            return

        # Check for misunderstanding
        if any(p in user_text for p in misunderstanding_patterns):
            if self._conv_state.in_repair:
                self._conv_state.increment_repair_retry()
            else:
                self._conv_state.enter_repair("misunderstanding")
            self._logger.info(
                f"[BREAKDOWN] misunderstanding detected, retry={self._conv_state.repair_retry_count}"
            )
            return

        # If in repair mode and user gives substantive response, exit repair
        if self._conv_state.in_repair and len(user_text.split()) > 3:
            self._conv_state.exit_repair()
            self._logger.info("[BREAKDOWN] repair successful, resuming normal flow")

    def _record_agent_response(self, response_text: str) -> None:
        """Record agent response for quality tracking."""
        if not self._conv_state:
            return

        result = self._conv_state.record_agent_response(
            response_text=response_text,
            phase="active",
            turn=self._conv_state.turn_count,
        )

        if result.get("issues"):
            self._logger.warning(f"[QUALITY] Issues detected: {result['issues']}")

    async def on_enter(self) -> None:
        """Called when agent becomes active."""
        await super().on_enter()
        # Say first message if configured
        first_msg = self.config.get(
            "first_message", "Hello! How can I assist you today?"
        )
        if self.config.get("strict_script_mode", False):
            generic_openers = {"hello", "hello!", "hi", "hi!", "hey", "hey!"}
            if str(first_msg).strip().lower() in generic_openers:
                user_name = getattr(self.user_state, "user_name", "") or ""
                first_msg = (
                    f"हॅलो, {user_name} बोलताय का?" if user_name else "हॅलो, बोलताय का?"
                )

        # In full realtime mode, TTS is not available - use generate_reply instead
        if self._is_full_realtime:
            self._logger.info(
                f"Full realtime mode: Using generate_reply for first message"
            )
            await self.session.generate_reply(
                instructions=f"Start the conversation by saying: {first_msg}"
            )
        else:
            await self.session.say(first_msg)

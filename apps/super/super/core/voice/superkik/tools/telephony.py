"""
Telephony Tool Plugin - Call management for SuperKik.

Provides tools for initiating calls to providers and managing
call status using the SIPManager infrastructure.
"""

import json
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Annotated, Any, Callable, Dict, List, Optional

from pydantic import Field

from super.core.logging import logging as app_logging
from super.core.voice.superkik.schema import CallContext, CallStatus, CallStatusType
from super.core.voice.superkik.tools.base import ToolPlugin

if TYPE_CHECKING:
    from super.core.voice.superkik.handler import SuperKikHandler

logger = app_logging.get_logger("superkik.tools.telephony")


def _is_call_in_progress(call_status: Optional[CallStatus]) -> bool:
    """Check if a call is currently in progress (not ended/failed/idle)."""
    if not call_status:
        return False
    # Terminal states where we can start a new call
    terminal_states = {CallStatusType.ENDED, CallStatusType.FAILED, CallStatusType.IDLE}
    return call_status.status not in terminal_states


async def initiate_call_impl(
    handler: "SuperKikHandler",
    provider_id: str,
    provider_name: Optional[str] = None,
    phone_number: Optional[str] = None,
    main_objective: str = "",
    preferred_time: Optional[str] = None,
    specific_questions: Optional[str] = None,
    task_details: Optional[Dict[str, Any]] = None,
) -> CallStatus:
    """
    Initiate a call to a provider.

    If a call is already in progress, returns the current call status instead
    of initiating a new call. This prevents duplicate SIP participant creation.

    Args:
        handler: SuperKikHandler instance
        provider_id: Provider ID from search results
        provider_name: Optional provider name for display
        phone_number: Optional direct phone number (overrides lookup)

    Returns:
        CallStatus with current call state
    """
    # Guard: Check if a call is already in progress
    current_call: Optional[CallStatus] = getattr(handler, "_current_call", None)
    if _is_call_in_progress(current_call):
        logger.info(
            f"[TELEPHONY] Call already in progress (status={current_call.status.value}), "
            f"returning current call instead of initiating new one"
        )
        return current_call

    call_id = str(uuid.uuid4())[:8]

    if not phone_number or not provider_name:
        last_result = getattr(handler, "_last_search_result", None)
        if last_result:
            for provider in last_result.providers:
                if provider.id == provider_id:
                    phone_number = phone_number or provider.phone
                    provider_name = provider_name or provider.name
                    break

    if not phone_number:
        logger.error(f"No phone number found for provider {provider_id}")
        return CallStatus(
            call_id=call_id,
            status=CallStatusType.FAILED,
            provider_id=provider_id,
            provider_name=provider_name,
            error_message="No phone number available for this provider",
        )

    call_status = CallStatus(
        call_id=call_id,
        status=CallStatusType.INITIATING,
        provider_id=provider_id,
        provider_name=provider_name,
        provider_phone=phone_number,
        started_at=datetime.utcnow().isoformat(),
    )

    # Store call context if provided
    context = CallContext(
        provider_id=provider_id,
        provider_name=provider_name or "Unknown",
        provider_phone=phone_number or "Unknown",
        main_objective=main_objective,
        details=task_details or {},
        preferred_time=preferred_time,
        specific_questions=specific_questions.split(",") if specific_questions else [],
    )
    handler._current_call_context = context

    handler._current_call = call_status
    # Reset call message sequence for new call
    handler._call_message_seq = 0

    if handler._event_bridge:
        await handler._publish_call_status(call_status)

    sip_manager = getattr(handler, "_sip_manager", None)
    if not sip_manager:
        logger.warning("SIP manager not available, simulating call")
        call_status.status = CallStatusType.CONNECTING
        if handler._event_bridge:
            await handler._publish_call_status(call_status)
        return call_status

    try:
        if handler.user_state:
            original_contact = getattr(handler.user_state, "contact_number", None)
            handler.user_state.contact_number = phone_number

        call_status.status = CallStatusType.CONNECTING
        if handler._event_bridge:
            await handler._publish_call_status(call_status)

        participant, room_name = await sip_manager.create_sip_participant({})

        if participant or room_name:
            call_status.status = CallStatusType.RINGING
            logger.info(f"Call initiated to {provider_name} ({phone_number})")
        else:
            call_status.status = CallStatusType.FAILED
            call_status.error_message = getattr(
                handler.user_state, "call_error", "Failed to connect call"
            )
            logger.error(f"Failed to initiate call to {phone_number}")

        if handler.user_state and original_contact:
            handler.user_state.contact_number = original_contact

    except Exception as e:
        logger.error(f"Error initiating call: {e}")
        call_status.status = CallStatusType.FAILED
        call_status.error_message = str(e)

    if handler._event_bridge:
        await handler._publish_call_status(call_status)

    return call_status


async def end_call_impl(
    handler: "SuperKikHandler",
    call_id: Optional[str] = None,
) -> CallStatus:
    """
    End an active call.

    Args:
        handler: SuperKikHandler instance
        call_id: Optional call ID (uses current call if not provided)

    Returns:
        CallStatus with ended state
    """
    current_call: Optional[CallStatus] = getattr(handler, "_current_call", None)

    if not current_call:
        return CallStatus(
            call_id=call_id or "unknown",
            status=CallStatusType.FAILED,
            error_message="No active call to end",
        )

    if call_id and current_call.call_id != call_id:
        return CallStatus(
            call_id=call_id,
            status=CallStatusType.FAILED,
            error_message=f"Call {call_id} not found",
        )

    if current_call.started_at:
        try:
            start_time = datetime.fromisoformat(current_call.started_at)
            duration = (datetime.utcnow() - start_time).total_seconds()
            current_call.duration_seconds = int(duration)
        except (ValueError, TypeError):
            pass

    current_call.status = CallStatusType.ENDED
    current_call.ended_at = datetime.utcnow().isoformat()

    if handler._event_bridge:
        await handler._publish_call_status(current_call)

    handler._current_call = None

    logger.info(
        f"Call ended: {current_call.provider_name} "
        f"(duration: {current_call.duration_seconds}s)"
    )

    return current_call


async def get_call_status_impl(
    handler: "SuperKikHandler",
    call_id: Optional[str] = None,
) -> Optional[CallStatus]:
    """Get status of current or specified call."""
    current_call: Optional[CallStatus] = getattr(handler, "_current_call", None)

    if not current_call:
        return None

    if call_id and current_call.call_id != call_id:
        return None

    return current_call


class TelephonyToolPlugin(ToolPlugin):
    """
    Tool plugin for call management.

    Provides tools:
    - initiate_call: Start a call to a provider
    - end_call: End the current call
    - get_call_status: Check call status
    """

    name = "telephony"

    def _create_tools(self) -> List[Callable]:
        """Create telephony-related tool functions."""
        return [
            self._create_initiate_call_tool(),
            self._create_end_call_tool(),
            self._create_get_call_status_tool(),
        ]

    def _create_initiate_call_tool(self) -> Callable:
        """Create the initiate_call function tool."""
        try:
            from livekit.agents.llm import function_tool
        except ImportError:
            self._logger.warning("livekit.agents not available")
            return lambda: None

        handler = self._handler

        @function_tool
        async def initiate_call(
            provider_id: Annotated[
                str,
                Field(description="Provider ID from search results"),
            ],
            main_objective: Annotated[
                str,
                Field(description="Main goal of the call (e.g. 'book a table', 'check availability')"),
            ],
            preferred_time: Annotated[
                Optional[str],
                Field(description="Specifically requested time if any"),
            ] = None,
            specific_questions: Annotated[
                Optional[str],
                Field(description="Comma-separated list of questions to ask"),
            ] = None,
            task_details: Annotated[
                Optional[str],
                Field(description="JSON string of any extra details like party size, symptoms, etc. Example: '{\"party_size\": 4}'"),
            ] = None,
        ) -> str:
            """
            Initiate a phone call to a provider.

            Use this tool when the user confirms they want to call a provider from
            the search results. Always confirm the provider selection before calling.

            IMPORTANT: Do NOT call this tool multiple times for the same provider.
            If a call is already in progress, wait for it to connect or end.

            Example triggers:
            - "Yes, call them"
            - "Connect me to the first one"
            - "Call Dr. Sharma's clinic"
            """
            try:
                # Parse task_details from JSON string if provided
                parsed_task_details: Optional[Dict[str, Any]] = None
                if task_details:
                    try:
                        parsed_task_details = json.loads(task_details)
                    except json.JSONDecodeError:
                        # If not valid JSON, wrap the string as a note
                        parsed_task_details = {"note": task_details}

                # Check if call already in progress before calling impl
                existing_call = getattr(handler, "_current_call", None)
                existing_call_in_progress = _is_call_in_progress(existing_call)

                call_status = await initiate_call_impl(
                    handler,
                    provider_id,
                    main_objective=main_objective,
                    preferred_time=preferred_time,
                    specific_questions=specific_questions,
                    task_details=parsed_task_details,
                )

                if call_status.status == CallStatusType.FAILED:
                    return json.dumps(
                        {
                            "status": "failed",
                            "error": call_status.error_message,
                            "message": f"Could not connect call: {call_status.error_message}",
                        }
                    )

                # If call was already in progress, return status indicating to wait
                if existing_call_in_progress:
                    status_messages = {
                        CallStatusType.INITIATING: "Call is being initiated",
                        CallStatusType.CONNECTING: "Call is connecting",
                        CallStatusType.RINGING: "Call is ringing, waiting for answer",
                        CallStatusType.ACTIVE: "Call is already connected",
                    }
                    message = status_messages.get(
                        call_status.status, f"Call is {call_status.status.value}"
                    )
                    return json.dumps(
                        {
                            "status": "in_progress",
                            "call_id": call_status.call_id,
                            "call_status": call_status.status.value,
                            "provider_name": call_status.provider_name,
                            "provider_phone": call_status.provider_phone,
                            "message": (
                                f"{message} to {call_status.provider_name}. "
                                "Please wait, do not initiate another call."
                            ),
                        }
                    )

                return json.dumps(
                    {
                        "status": "success",
                        "call_id": call_status.call_id,
                        "call_status": call_status.status.value,
                        "provider_name": call_status.provider_name,
                        "provider_phone": call_status.provider_phone,
                        "message": (
                            f"Connecting you to {call_status.provider_name}. "
                            "Please wait while the call connects."
                        ),
                    }
                )

            except Exception as e:
                self._logger.error(f"initiate_call error: {e}")
                return json.dumps(
                    {
                        "status": "error",
                        "message": f"Error initiating call: {str(e)}",
                    }
                )

        return initiate_call

    def _create_end_call_tool(self) -> Callable:
        """Create the end_call function tool."""
        try:
            from livekit.agents.llm import function_tool
        except ImportError:
            self._logger.warning("livekit.agents not available")
            return lambda: None

        handler = self._handler

        @function_tool
        async def end_call() -> str:
            """
            End the current active call.

            Use this tool when the user wants to disconnect from the provider.

            Example triggers:
            - "Hang up"
            - "End the call"
            - "Disconnect"
            """
            try:
                call_status = await end_call_impl(handler)

                if call_status.status == CallStatusType.FAILED:
                    return json.dumps(
                        {
                            "status": "failed",
                            "error": call_status.error_message,
                            "message": call_status.error_message,
                        }
                    )

                return json.dumps(
                    {
                        "status": "success",
                        "call_id": call_status.call_id,
                        "duration_seconds": call_status.duration_seconds,
                        "provider_name": call_status.provider_name,
                        "message": (
                            f"Call with {call_status.provider_name} ended. "
                            f"Duration: {call_status.duration_seconds} seconds."
                        ),
                    }
                )

            except Exception as e:
                self._logger.error(f"end_call error: {e}")
                return json.dumps(
                    {
                        "status": "error",
                        "message": f"Error ending call: {str(e)}",
                    }
                )

        return end_call

    def _create_get_call_status_tool(self) -> Callable:
        """Create the get_call_status function tool."""
        try:
            from livekit.agents.llm import function_tool
        except ImportError:
            self._logger.warning("livekit.agents not available")
            return lambda: None

        handler = self._handler

        @function_tool
        async def get_call_status() -> str:
            """
            Get the status of the current call.

            Use this to check if a call is still active, connecting, or ended.
            """
            try:
                call_status = await get_call_status_impl(handler)

                if not call_status:
                    return json.dumps(
                        {
                            "status": "no_call",
                            "message": "No active call.",
                        }
                    )

                return json.dumps(
                    {
                        "status": "success",
                        "call_id": call_status.call_id,
                        "call_status": call_status.status.value,
                        "provider_name": call_status.provider_name,
                        "duration_seconds": call_status.duration_seconds,
                        "message": (
                            f"Call with {call_status.provider_name} is "
                            f"{call_status.status.value}."
                        ),
                    }
                )

            except Exception as e:
                self._logger.error(f"get_call_status error: {e}")
                return json.dumps(
                    {
                        "status": "error",
                        "message": f"Error getting call status: {str(e)}",
                    }
                )

        return get_call_status

    def get_metrics(self) -> Optional[Dict[str, Any]]:
        """Return call metrics."""
        if not self._handler:
            return None

        current_call = getattr(self._handler, "_current_call", None)
        return {
            "active_call": current_call is not None,
            "call_status": current_call.status.value if current_call else None,
        }

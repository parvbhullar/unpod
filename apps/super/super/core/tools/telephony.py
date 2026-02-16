"""
Telephony Tool - Call management.

Provides call initiation and management that works with any orchestrator.
Uses in-memory storage for call state.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from super.core.logging import logging as app_logging
from super.core.tools.base import BaseTool, ToolCategory, ToolResult

logger = app_logging.get_logger("tools.telephony")


class CallStatusType(str, Enum):
    IDLE = "idle"
    INITIATING = "initiating"
    CONNECTING = "connecting"
    RINGING = "ringing"
    ACTIVE = "active"
    ENDED = "ended"
    FAILED = "failed"


@dataclass
class CallData:
    """Call information."""

    call_id: str
    status: CallStatusType
    provider_id: Optional[str] = None
    provider_name: Optional[str] = None
    phone_number: Optional[str] = None
    objective: Optional[str] = None
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    ended_at: Optional[str] = None
    duration_seconds: int = 0
    error_message: Optional[str] = None


class CallManager:
    """Simple in-memory call manager."""

    def __init__(self) -> None:
        self._current_call: Optional[CallData] = None

    @property
    def current_call(self) -> Optional[CallData]:
        return self._current_call

    def is_call_active(self) -> bool:
        if not self._current_call:
            return False
        terminal = {CallStatusType.ENDED, CallStatusType.FAILED, CallStatusType.IDLE}
        return self._current_call.status not in terminal

    def initiate(
        self,
        provider_id: str,
        provider_name: str,
        phone_number: str,
        objective: Optional[str] = None,
    ) -> CallData:
        if self.is_call_active():
            return self._current_call

        call_id = str(uuid.uuid4())[:8]
        self._current_call = CallData(
            call_id=call_id,
            status=CallStatusType.INITIATING,
            provider_id=provider_id,
            provider_name=provider_name,
            phone_number=phone_number,
            objective=objective,
        )
        return self._current_call

    def update_status(self, status: CallStatusType) -> Optional[CallData]:
        if not self._current_call:
            return None
        self._current_call.status = status
        return self._current_call

    def end(self) -> Optional[CallData]:
        if not self._current_call:
            return None
        if self._current_call.started_at:
            try:
                start = datetime.fromisoformat(self._current_call.started_at)
                duration = (datetime.utcnow() - start).total_seconds()
                self._current_call.duration_seconds = int(duration)
            except (ValueError, TypeError):
                pass
        self._current_call.status = CallStatusType.ENDED
        self._current_call.ended_at = datetime.utcnow().isoformat()
        ended = self._current_call
        self._current_call = None
        return ended


_default_manager = CallManager()


class InitiateCallTool(BaseTool):
    """Tool for initiating phone calls."""

    name = "initiate_call"
    description = "Start a phone call to a provider"
    category = ToolCategory.COMMUNICATION

    def __init__(self, manager: Optional[CallManager] = None) -> None:
        self._manager = manager or _default_manager

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "provider_id": {
                        "type": "string",
                        "description": "Provider ID from search results",
                    },
                    "provider_name": {
                        "type": "string",
                        "description": "Provider name for display",
                    },
                    "phone_number": {
                        "type": "string",
                        "description": "Phone number to call",
                    },
                    "objective": {
                        "type": "string",
                        "description": "Main goal of the call",
                    },
                },
                "required": ["provider_id", "provider_name", "phone_number"],
            },
        }

    async def execute(
        self,
        provider_id: str,
        provider_name: str,
        phone_number: str,
        objective: Optional[str] = None,
        **kwargs: Any,
    ) -> ToolResult:
        if self._manager.is_call_active():
            call = self._manager.current_call
            return ToolResult(
                success=True,
                data={
                    "call_id": call.call_id,
                    "status": call.status.value,
                    "provider_name": call.provider_name,
                    "message": "Call already in progress",
                },
                metadata={"already_active": True},
            )

        call = self._manager.initiate(
            provider_id=provider_id,
            provider_name=provider_name,
            phone_number=phone_number,
            objective=objective,
        )

        self._manager.update_status(CallStatusType.CONNECTING)

        return ToolResult(
            success=True,
            data={
                "call_id": call.call_id,
                "status": call.status.value,
                "provider_name": call.provider_name,
                "phone_number": call.phone_number,
            },
        )


class EndCallTool(BaseTool):
    """Tool for ending phone calls."""

    name = "end_call"
    description = "End the current active call"
    category = ToolCategory.COMMUNICATION

    def __init__(self, manager: Optional[CallManager] = None) -> None:
        self._manager = manager or _default_manager

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        }

    async def execute(self, **kwargs: Any) -> ToolResult:
        if not self._manager.current_call:
            return ToolResult(success=False, error="No active call to end")

        call = self._manager.end()

        return ToolResult(
            success=True,
            data={
                "call_id": call.call_id,
                "status": call.status.value,
                "provider_name": call.provider_name,
                "duration_seconds": call.duration_seconds,
            },
        )


class GetCallStatusTool(BaseTool):
    """Tool for checking call status."""

    name = "get_call_status"
    description = "Get the status of the current call"
    category = ToolCategory.COMMUNICATION

    def __init__(self, manager: Optional[CallManager] = None) -> None:
        self._manager = manager or _default_manager

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        }

    async def execute(self, **kwargs: Any) -> ToolResult:
        call = self._manager.current_call

        if not call:
            return ToolResult(
                success=True,
                data={"status": "no_call", "message": "No active call"},
            )

        return ToolResult(
            success=True,
            data={
                "call_id": call.call_id,
                "status": call.status.value,
                "provider_name": call.provider_name,
                "phone_number": call.phone_number,
                "duration_seconds": call.duration_seconds,
            },
        )

"""
Booking Tool - Appointment management.

Provides booking functionality that works with any orchestrator.
Uses in-memory storage for booking state.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from super.core.logging import logging as app_logging
from super.core.tools.base import BaseTool, ToolCategory, ToolResult

logger = app_logging.get_logger("tools.booking")


class BookingStatusType(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class BookingData:
    """Booking information."""

    booking_id: str
    provider_id: str
    provider_name: str
    status: BookingStatusType
    time_slot: Optional[str] = None
    service_type: Optional[str] = None
    notes: Optional[str] = None
    confirmation_code: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: Optional[str] = None


class BookingStore:
    """Simple in-memory booking store."""

    def __init__(self) -> None:
        self._bookings: Dict[str, BookingData] = {}

    def create(
        self,
        provider_id: str,
        provider_name: str,
        time_slot: Optional[str] = None,
        service_type: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> BookingData:
        booking_id = str(uuid.uuid4())[:8]
        booking = BookingData(
            booking_id=booking_id,
            provider_id=provider_id,
            provider_name=provider_name,
            status=BookingStatusType.PENDING,
            time_slot=time_slot,
            service_type=service_type,
            notes=notes,
        )
        self._bookings[booking_id] = booking
        return booking

    def get(self, booking_id: str) -> Optional[BookingData]:
        return self._bookings.get(booking_id)

    def confirm(
        self, booking_id: str, confirmation_code: Optional[str] = None
    ) -> Optional[BookingData]:
        booking = self._bookings.get(booking_id)
        if not booking or booking.status != BookingStatusType.PENDING:
            return None
        booking.status = BookingStatusType.CONFIRMED
        booking.confirmation_code = confirmation_code or f"BK{booking_id.upper()}"
        booking.updated_at = datetime.utcnow().isoformat()
        return booking

    def cancel(
        self, booking_id: str, reason: Optional[str] = None
    ) -> Optional[BookingData]:
        booking = self._bookings.get(booking_id)
        if not booking or booking.status in (
            BookingStatusType.CANCELLED,
            BookingStatusType.COMPLETED,
        ):
            return None
        booking.status = BookingStatusType.CANCELLED
        booking.notes = reason or booking.notes
        booking.updated_at = datetime.utcnow().isoformat()
        return booking


_default_store = BookingStore()


class CreateBookingTool(BaseTool):
    """Tool for creating booking requests."""

    name = "create_booking"
    description = "Create a booking request with a provider"
    category = ToolCategory.BOOKING

    def __init__(self, store: Optional[BookingStore] = None) -> None:
        self._store = store or _default_store

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
                    "time_slot": {
                        "type": "string",
                        "description": "Requested time (e.g., 'tomorrow 10am')",
                    },
                    "service_type": {
                        "type": "string",
                        "description": "Type of service (e.g., 'checkup')",
                    },
                    "notes": {
                        "type": "string",
                        "description": "Additional notes",
                    },
                },
                "required": ["provider_id", "provider_name"],
            },
        }

    async def execute(
        self,
        provider_id: str,
        provider_name: str,
        time_slot: Optional[str] = None,
        service_type: Optional[str] = None,
        notes: Optional[str] = None,
        **kwargs: Any,
    ) -> ToolResult:
        booking = self._store.create(
            provider_id=provider_id,
            provider_name=provider_name,
            time_slot=time_slot,
            service_type=service_type,
            notes=notes,
        )

        return ToolResult(
            success=True,
            data={
                "booking_id": booking.booking_id,
                "provider_name": booking.provider_name,
                "status": booking.status.value,
                "time_slot": booking.time_slot,
                "service_type": booking.service_type,
            },
        )


class ConfirmBookingTool(BaseTool):
    """Tool for confirming pending bookings."""

    name = "confirm_booking"
    description = "Confirm a pending booking request"
    category = ToolCategory.BOOKING

    def __init__(self, store: Optional[BookingStore] = None) -> None:
        self._store = store or _default_store

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "booking_id": {
                        "type": "string",
                        "description": "Booking ID to confirm",
                    },
                    "confirmation_code": {
                        "type": "string",
                        "description": "Optional confirmation code",
                    },
                },
                "required": ["booking_id"],
            },
        }

    async def execute(
        self,
        booking_id: str,
        confirmation_code: Optional[str] = None,
        **kwargs: Any,
    ) -> ToolResult:
        booking = self._store.confirm(booking_id, confirmation_code)

        if not booking:
            existing = self._store.get(booking_id)
            if not existing:
                return ToolResult(
                    success=False, error=f"Booking {booking_id} not found"
                )
            return ToolResult(
                success=False,
                error=f"Cannot confirm booking with status: {existing.status.value}",
            )

        return ToolResult(
            success=True,
            data={
                "booking_id": booking.booking_id,
                "confirmation_code": booking.confirmation_code,
                "provider_name": booking.provider_name,
                "status": booking.status.value,
            },
        )


class CancelBookingTool(BaseTool):
    """Tool for cancelling bookings."""

    name = "cancel_booking"
    description = "Cancel an existing booking"
    category = ToolCategory.BOOKING

    def __init__(self, store: Optional[BookingStore] = None) -> None:
        self._store = store or _default_store

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "booking_id": {
                        "type": "string",
                        "description": "Booking ID to cancel",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Cancellation reason",
                    },
                },
                "required": ["booking_id"],
            },
        }

    async def execute(
        self,
        booking_id: str,
        reason: Optional[str] = None,
        **kwargs: Any,
    ) -> ToolResult:
        booking = self._store.cancel(booking_id, reason)

        if not booking:
            existing = self._store.get(booking_id)
            if not existing:
                return ToolResult(
                    success=False, error=f"Booking {booking_id} not found"
                )
            return ToolResult(
                success=False,
                error=f"Cannot cancel booking with status: {existing.status.value}",
            )

        return ToolResult(
            success=True,
            data={
                "booking_id": booking.booking_id,
                "status": booking.status.value,
            },
        )

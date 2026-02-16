"""
Booking Tool Plugin - Appointment management for SuperKik.

Provides tools for creating, confirming, and managing bookings
with service providers.
"""

import json
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Annotated, Any, Callable, Dict, List, Optional

from pydantic import Field

from super.core.logging import logging as app_logging
from super.core.voice.superkik.schema import (
    BookingRequest,
    BookingStatus,
    BookingStatusType,
)
from super.core.voice.superkik.tools.base import ToolPlugin

if TYPE_CHECKING:
    from super.core.voice.superkik.handler import SuperKikHandler

logger = app_logging.get_logger("superkik.tools.booking")


async def create_booking_impl(
    handler: "SuperKikHandler",
    provider_id: str,
    time_slot: Optional[str] = None,
    service_type: Optional[str] = None,
    notes: Optional[str] = None,
) -> BookingStatus:
    """
    Create a booking request for a provider.

    Args:
        handler: SuperKikHandler instance
        provider_id: Provider ID from search results
        time_slot: Requested time slot (e.g., "tomorrow 10am")
        service_type: Type of service requested
        notes: Additional notes for the booking

    Returns:
        BookingStatus with pending state
    """
    booking_id = str(uuid.uuid4())[:8]

    provider_name = None
    provider_phone = None
    last_result = getattr(handler, "_last_search_result", None)
    if last_result:
        for provider in last_result.providers:
            if provider.id == provider_id:
                provider_name = provider.name
                provider_phone = provider.phone
                break

    if not provider_name:
        logger.warning(f"Provider {provider_id} not found in search results")
        return BookingStatus(
            booking_id=booking_id,
            status=BookingStatusType.FAILED,
            error_message=f"Provider {provider_id} not found",
        )

    user_name = None
    user_contact = None
    if handler.user_state:
        user_name = getattr(handler.user_state, "user_name", None)
        user_contact = getattr(handler.user_state, "contact_number", None)

    request = BookingRequest(
        provider_id=provider_id,
        provider_name=provider_name,
        provider_phone=provider_phone,
        requested_time_str=time_slot,
        service_type=service_type,
        notes=notes,
        user_name=user_name,
        user_contact=user_contact,
    )

    booking_status = BookingStatus(
        booking_id=booking_id,
        status=BookingStatusType.PENDING,
        request=request,
    )

    if not hasattr(handler, "_pending_bookings"):
        handler._pending_bookings = {}
    handler._pending_bookings[booking_id] = booking_status

    preferences = getattr(handler, "_user_preferences", None)
    if preferences:
        preferences.set_last_provider(provider_id, provider_name)
        preferences.add_to_history(
            "booking_created",
            {
                "booking_id": booking_id,
                "provider_id": provider_id,
                "provider_name": provider_name,
            },
        )

    if handler._event_bridge:
        await handler._publish_booking_update(booking_status)

    logger.info(f"Booking created: {booking_id} for {provider_name}")

    return booking_status


async def confirm_booking_impl(
    handler: "SuperKikHandler",
    booking_id: str,
    confirmation_code: Optional[str] = None,
) -> BookingStatus:
    """
    Confirm a pending booking.

    Args:
        handler: SuperKikHandler instance
        booking_id: Booking ID to confirm
        confirmation_code: Optional confirmation code from provider

    Returns:
        BookingStatus with confirmed state
    """
    pending_bookings = getattr(handler, "_pending_bookings", {})
    booking_status = pending_bookings.get(booking_id)

    if not booking_status:
        return BookingStatus(
            booking_id=booking_id,
            status=BookingStatusType.FAILED,
            error_message=f"Booking {booking_id} not found",
        )

    if booking_status.status != BookingStatusType.PENDING:
        return BookingStatus(
            booking_id=booking_id,
            status=BookingStatusType.FAILED,
            error_message=(
                f"Booking {booking_id} is not pending "
                f"(status: {booking_status.status.value})"
            ),
        )

    booking_status.status = BookingStatusType.CONFIRMED
    booking_status.confirmation_code = confirmation_code or f"SK{booking_id.upper()}"
    booking_status.confirmed_time = datetime.utcnow()
    booking_status.updated_at = datetime.utcnow().isoformat()

    preferences = getattr(handler, "_user_preferences", None)
    if preferences:
        preferences.add_to_history(
            "booking_confirmed",
            {
                "booking_id": booking_id,
                "confirmation_code": booking_status.confirmation_code,
            },
        )

    if handler._event_bridge:
        await handler._publish_booking_update(booking_status)

    logger.info(
        f"Booking confirmed: {booking_id} (code: {booking_status.confirmation_code})"
    )

    return booking_status


async def cancel_booking_impl(
    handler: "SuperKikHandler",
    booking_id: str,
    reason: Optional[str] = None,
) -> BookingStatus:
    """
    Cancel a booking.

    Args:
        handler: SuperKikHandler instance
        booking_id: Booking ID to cancel
        reason: Optional cancellation reason

    Returns:
        BookingStatus with cancelled state
    """
    pending_bookings = getattr(handler, "_pending_bookings", {})
    booking_status = pending_bookings.get(booking_id)

    if not booking_status:
        return BookingStatus(
            booking_id=booking_id,
            status=BookingStatusType.FAILED,
            error_message=f"Booking {booking_id} not found",
        )

    if booking_status.status in (
        BookingStatusType.CANCELLED,
        BookingStatusType.COMPLETED,
    ):
        return BookingStatus(
            booking_id=booking_id,
            status=BookingStatusType.FAILED,
            error_message=f"Cannot cancel booking (status: {booking_status.status.value})",
        )

    booking_status.status = BookingStatusType.CANCELLED
    booking_status.error_message = reason
    booking_status.updated_at = datetime.utcnow().isoformat()

    preferences = getattr(handler, "_user_preferences", None)
    if preferences:
        preferences.add_to_history(
            "booking_cancelled",
            {
                "booking_id": booking_id,
                "reason": reason,
            },
        )

    if handler._event_bridge:
        await handler._publish_booking_update(booking_status)

    logger.info(f"Booking cancelled: {booking_id}")

    return booking_status


async def get_booking_status_impl(
    handler: "SuperKikHandler",
    booking_id: str,
) -> Optional[BookingStatus]:
    """Get status of a booking."""
    pending_bookings = getattr(handler, "_pending_bookings", {})
    return pending_bookings.get(booking_id)


class BookingToolPlugin(ToolPlugin):
    """
    Tool plugin for booking management.

    Provides tools:
    - create_booking: Create a booking request
    - confirm_booking: Confirm a pending booking
    - cancel_booking: Cancel a booking
    """

    name = "booking"

    def _create_tools(self) -> List[Callable]:
        """Create booking-related tool functions."""
        return [
            self._create_booking_tool(),
            self._create_confirm_booking_tool(),
            self._create_cancel_booking_tool(),
        ]

    def _create_booking_tool(self) -> Callable:
        """Create the create_booking function tool."""
        try:
            from livekit.agents.llm import function_tool
        except ImportError:
            self._logger.warning("livekit.agents not available")
            return lambda: None

        handler = self._handler

        @function_tool
        async def create_booking(
            provider_id: Annotated[
                str,
                Field(description="Provider ID from search results"),
            ],
            time_slot: Annotated[
                Optional[str],
                Field(
                    description="Requested time (e.g., 'tomorrow 10am', 'next Monday 3pm')"
                ),
            ] = None,
            service_type: Annotated[
                Optional[str],
                Field(description="Type of service (e.g., 'checkup', 'consultation')"),
            ] = None,
        ) -> str:
            """
            Create a booking request with a provider.

            Use this tool when the user wants to book an appointment. Collect the
            time slot and service type through conversation before calling.

            Example triggers:
            - "Book an appointment for tomorrow"
            - "Schedule a checkup with them"
            - "I want to book at 3pm"
            """
            try:
                booking_status = await create_booking_impl(
                    handler,
                    provider_id=provider_id,
                    time_slot=time_slot,
                    service_type=service_type,
                )

                if booking_status.status == BookingStatusType.FAILED:
                    return json.dumps(
                        {
                            "status": "failed",
                            "error": booking_status.error_message,
                            "message": f"Could not create booking: {booking_status.error_message}",
                        }
                    )

                request = booking_status.request
                return json.dumps(
                    {
                        "status": "success",
                        "booking_id": booking_status.booking_id,
                        "provider_name": request.provider_name if request else None,
                        "time_slot": request.requested_time_str if request else None,
                        "service_type": request.service_type if request else None,
                        "message": (
                            f"Booking request created for {request.provider_name if request else 'provider'}. "
                            f"Booking ID: {booking_status.booking_id}. "
                            "Please confirm to finalize the booking."
                        ),
                    }
                )

            except Exception as e:
                self._logger.error(f"create_booking error: {e}")
                return json.dumps(
                    {
                        "status": "error",
                        "message": f"Error creating booking: {str(e)}",
                    }
                )

        return create_booking

    def _create_confirm_booking_tool(self) -> Callable:
        """Create the confirm_booking function tool."""
        try:
            from livekit.agents.llm import function_tool
        except ImportError:
            self._logger.warning("livekit.agents not available")
            return lambda: None

        handler = self._handler

        @function_tool
        async def confirm_booking(
            booking_id: Annotated[
                str,
                Field(description="Booking ID to confirm"),
            ],
        ) -> str:
            """
            Confirm a pending booking request.

            Use this after the user confirms they want to proceed with the booking.

            Example triggers:
            - "Yes, confirm it"
            - "Book it"
            - "That looks good, proceed"
            """
            try:
                booking_status = await confirm_booking_impl(handler, booking_id)

                if booking_status.status == BookingStatusType.FAILED:
                    return json.dumps(
                        {
                            "status": "failed",
                            "error": booking_status.error_message,
                            "message": booking_status.error_message,
                        }
                    )

                request = booking_status.request
                return json.dumps(
                    {
                        "status": "success",
                        "booking_id": booking_status.booking_id,
                        "confirmation_code": booking_status.confirmation_code,
                        "provider_name": request.provider_name if request else None,
                        "message": (
                            f"Booking confirmed! Your confirmation code is "
                            f"{booking_status.confirmation_code}. "
                            f"Appointment with {request.provider_name if request else 'provider'} "
                            f"for {request.requested_time_str if request else 'the requested time'}."
                        ),
                    }
                )

            except Exception as e:
                self._logger.error(f"confirm_booking error: {e}")
                return json.dumps(
                    {
                        "status": "error",
                        "message": f"Error confirming booking: {str(e)}",
                    }
                )

        return confirm_booking

    def _create_cancel_booking_tool(self) -> Callable:
        """Create the cancel_booking function tool."""
        try:
            from livekit.agents.llm import function_tool
        except ImportError:
            self._logger.warning("livekit.agents not available")
            return lambda: None

        handler = self._handler

        @function_tool
        async def cancel_booking(
            booking_id: Annotated[
                str,
                Field(description="Booking ID to cancel"),
            ],
            reason: Annotated[
                Optional[str],
                Field(description="Reason for cancellation"),
            ] = None,
        ) -> str:
            """
            Cancel a booking request.

            Use this when the user wants to cancel a pending or confirmed booking.

            Example triggers:
            - "Cancel my booking"
            - "I don't want to book anymore"
            - "Never mind, cancel it"
            """
            try:
                booking_status = await cancel_booking_impl(handler, booking_id, reason)

                if booking_status.status == BookingStatusType.FAILED:
                    return json.dumps(
                        {
                            "status": "failed",
                            "error": booking_status.error_message,
                            "message": booking_status.error_message,
                        }
                    )

                return json.dumps(
                    {
                        "status": "success",
                        "booking_id": booking_status.booking_id,
                        "message": f"Booking {booking_id} has been cancelled.",
                    }
                )

            except Exception as e:
                self._logger.error(f"cancel_booking error: {e}")
                return json.dumps(
                    {
                        "status": "error",
                        "message": f"Error cancelling booking: {str(e)}",
                    }
                )

        return cancel_booking

    def get_metrics(self) -> Optional[Dict[str, Any]]:
        """Return booking metrics."""
        if not self._handler:
            return None

        pending_bookings = getattr(self._handler, "_pending_bookings", {})
        pending_count = sum(
            1
            for b in pending_bookings.values()
            if b.status == BookingStatusType.PENDING
        )
        confirmed_count = sum(
            1
            for b in pending_bookings.values()
            if b.status == BookingStatusType.CONFIRMED
        )

        return {
            "total_bookings": len(pending_bookings),
            "pending_bookings": pending_count,
            "confirmed_bookings": confirmed_count,
        }

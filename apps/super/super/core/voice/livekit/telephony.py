"""
SIPManager - A standalone module for SIP/telephony operations.

This module contains all SIP-related functionality extracted from the PipecatVoiceHandler,
including creating SIP participants, phone number formatting, trunk management, and call handover.
"""
import random

import asyncio
import logging
import os
from typing import Any, Dict, Optional
from datetime import datetime

from super.core.logging.logging import print_log
from super_services.libs.core.timezone_utils import normalize_phone_number


class SIPManager:
    """
    Manages SIP/telephony operations including:
    - Creating SIP participants for outbound calls
    - Phone number formatting and validation
    - Trunk selection for outbound calls
    - Call handover functionality
    - Room name generation
    """

    def __init__(
        self,
        logger: logging.Logger,
        config: Dict[str, Any],
        session_id: str,
        room_name: Optional[str] = None,
        user_state: Optional[Any] = None,
        transport: Optional[Any] = None,
    ):
        """
        Initialize the SIP Manager.

        Args:
            logger: Logger instance for logging operations
            config: Configuration dictionary containing SIP settings
            session_id: Unique session identifier
            room_name: Optional LiveKit room name (will be generated if not provided)
            user_state: Optional user state object containing call information
        """
        self._logger = logger
        self.config = config
        self._session_id = session_id
        self._room_name = room_name or self._generate_room_name()
        self.user_state = user_state
        self.transport = transport

    def _generate_room_name(self) -> str:
        """
        Generate a unique room name based on session ID.

        Returns:
            str: Generated room name in format 'room_{session_id}'
        """
        self._room_name = f"room_{self._session_id}"
        return self._room_name

    def _format_phone_number(self, phone_number: str) -> Optional[str]:
       return normalize_phone_number(phone_number)

    def _format_sip_uri(self, phone_number: str, use_alternate: bool = False) -> Optional[str]:
        """
        Format phone number as SIP URI for Daily dialout.

        Daily requires SIP URI format for dialout: phone_number@sip_domain
        Example: +919876543210@sip-up-tt.unpod.tv

        Args:
            phone_number: Formatted E.164 phone number (with country code)
            use_alternate: If True, use alternate SIP domain (fallback)

        Returns:
            Optional[str]: SIP URI string, or None if invalid
        """
        if not phone_number:
            return None

        # Get SIP domain from environment variable
        # Primary: UNPOD_SIP_DOMAIN (sip-up-tt.unpod.tv)
        # Fallback: UNPOD_SIP_DOMAIN_ALT (sip.unpod.tel)
        if use_alternate:
            sip_domain = os.getenv("UNPOD_SIP_DOMAIN_ALT")
            domain_type = "alternate"
        else:
            sip_domain = os.getenv("UNPOD_SIP_DOMAIN")
            domain_type = "primary"

        if not sip_domain:
            self._logger.error(f"{domain_type.upper()} SIP domain not set (UNPOD_SIP_DOMAIN{'_ALT' if use_alternate else ''})")
            return None

        # Remove @ prefix if already in domain
        if sip_domain.startswith("@"):
            sip_domain = sip_domain[1:]

        # Construct SIP URI: phone_number@sip_domain
        sip_uri = f"{phone_number}@{sip_domain}"
        self._logger.info(f"Formatted SIP URI ({domain_type}): {sip_uri}")

        return sip_uri

    def _find_trunk_for_outbound(self, number: str) -> Optional[str]:
        """
        Find appropriate SIP trunk for outbound call.

        This is a simple implementation that uses the first available trunk.
        In production, this should look up the from_number and find the mapped
        trunk from the provider or database.

        Args:
            number: Phone number to find trunk for

        Returns:
            Optional[str]: SIP trunk ID, or None if not found
        """
        # Simple implementation - use first available trunk
        # It should look for from_number and mapped trunk to the same number from provider or db
        return os.getenv("SIP_OUTBOUND_TRUNK_ID")

    @staticmethod
    def get_trunk_id(model_config: Dict[str, Any]) -> Optional[str]:
        """
        Select a SIP trunk ID from the telephony config.

        Picks a random trunk from configured telephony numbers,
        falling back to SIP_OUTBOUND_TRUNK_ID env var.
        """
        telephony = (
            model_config.get("telephony")
            if isinstance(model_config, dict)
            else []
        )

        if not telephony:
            return os.getenv("SIP_OUTBOUND_TRUNK_ID")

        num = random.choice(telephony)

        if not isinstance(num, dict):
            return os.getenv("SIP_OUTBOUND_TRUNK_ID")

        trunk_id = num.get("association", {}).get("trunk_id")
        return trunk_id or os.getenv("SIP_OUTBOUND_TRUNK_ID")


    async def create_sip_participant(self, data: Dict[str, Any]) -> tuple[Optional[Any], Optional[str]]:
        """
        Create a SIP participant for outbound calling.

        This method:
        - Validates and formats the phone number
        - Selects appropriate SIP trunk
        - Creates SIP participant with retry logic
        - Handles errors with exponential backoff

        """
        # Validate user state and phone number first (common for both Daily and LiveKit)
        if not self.user_state or not hasattr(self.user_state, 'contact_number'):
            self._logger.error("User state or contact number not available")
            return None, None

        phone_number = self._format_phone_number(self.user_state.contact_number)
        if not phone_number:
            self._logger.error(f"Invalid phone number format: {self.user_state.contact_number}")
            return None, None

        # Initialize variables for different transport types
        livekit_api = None
        request = None
        room_name = None
        trunk_id = None

        if self.user_state.transport_type == "daily":
            self._logger.info("creating SIP participant for daily transport")
            room_name = self.user_state.room_name

            # Format phone number as SIP URI for Daily dialout
            # Daily requires SIP URI instead of phone number: phone@domain.sip.provider.com
            # Primary domain: UNPOD_SIP_DOMAIN (sip-up-tt.unpod.tv)
            # Fallback domain: UNPOD_SIP_DOMAIN_ALT (sip.unpod.tel)
            sip_uri = self._format_sip_uri(phone_number, use_alternate=False)
            if not sip_uri:
                self._logger.error("Failed to format SIP URI for Daily dialout")
                if self.user_state:
                    self.user_state.call_error = "Invalid SIP URI configuration - missing UNPOD_SIP_DOMAIN"
                    self.user_state.call_status = "failed"
                return None, None

            # Log Daily call setup details
            self._logger.info(f"📞 Daily Call Setup Details:")
            self._logger.info(f"  • Original Number: {self.user_state.contact_number}")
            self._logger.info(f"  • Formatted Number: {phone_number}")
            self._logger.info(f"  • SIP URI (primary): {sip_uri}")
            self._logger.info(f"  • Room Name: {room_name}")
            self._logger.info(f"  • Participant Name: {getattr(self.user_state, 'user_name', 'Unknown')}")

            # ⚠️ CRITICAL: Daily transport requires the pipeline to be running before calling start_dialout()
            # The transport's task manager is not initialized until the pipeline starts.
            # Therefore, we CANNOT call start_dialout() here - it will fail with:
            #   "DailyTransportClient: missing task manager (pipeline not started?)"
            #
            # Solution: Store the dialout info in user_state and return None as the participant.
            # The actual dialout will be triggered via an event handler AFTER the pipeline starts.
            # See: on_call_state_updated handler in pipecat_handler.py
            self.user_state.dialout_sip_uri = sip_uri
            # self.user_state.dialout_from_number = from_number  # Store for alternate domain retry
            self.user_state.dialout_phone_number = phone_number  # Store for alternate domain retry
            self._logger.info("⏳ Daily dialout deferred - will be triggered after pipeline starts")
            return None, room_name

        else:
            self._logger.info("creating SIP participant for livekit transport")
            from livekit import api
            from livekit.protocol.sip import CreateSIPParticipantRequest, SIPParticipantInfo

            self._logger.info("Creating SIP participant")
            livekit_api = api.LiveKitAPI()

            # TODO: Get trunk id from agent number required for allocation.
            # Find appropriate trunk if not specified
            trunk_id = data.get("trunk_id", os.getenv("SIP_OUTBOUND_TRUNK_ID"))
            if not trunk_id:
                from_number = data.get("from_number", os.getenv("SIP_OUTBOUND_CALLER_ID"))
                trunk_id = self._find_trunk_for_outbound(from_number)

            # Log trunk configuration for debugging
            if not trunk_id:
                self._logger.error("❌ No SIP trunk ID available!")
                self._logger.error("Please set SIP_OUTBOUND_TRUNK_ID environment variable or provide trunk_id in data")
                if self.user_state:
                    self.user_state.call_error = "No SIP trunk configured - missing SIP_OUTBOUND_TRUNK_ID"
                    self.user_state.call_status = "failed"
                return None, None
            else:
                self._logger.info(f"✓ Using SIP trunk: {trunk_id}")

            room_name = self._room_name

            # Comprehensive logging for SIP call setup
            self._logger.info(f"📞 SIP Call Setup Details:")
            self._logger.info(f"  • Trunk ID: {trunk_id}")
            self._logger.info(f"  • Original Number: {self.user_state.contact_number}")
            self._logger.info(f"  • Formatted Number: {phone_number}")
            self._logger.info(f"  • Number Length: {len(phone_number)} chars")
            self._logger.info(f"  • Room Name: {room_name}")
            self._logger.info(f"  • Participant Name: {getattr(self.user_state, 'user_name', 'Unknown')}")
            self._logger.info(f"  • Krisp Enabled: True")
            self._logger.info(f"  • Wait Until Answered: True")
            print(f"Creating SIP participant with trunk_id: {trunk_id}, phone: {phone_number}")
            # Get user name if available
            participant_name = getattr(self.user_state, 'user_name', 'Unknown')
            request = CreateSIPParticipantRequest(
                sip_trunk_id=trunk_id,
                sip_call_to=phone_number,
                room_name=room_name,
                participant_identity=phone_number,
                participant_name=participant_name,
                krisp_enabled=True,
                wait_until_answered=True
            )

        # Retry logic for LiveKit SIP participant creation
        max_retries = 3
        sip_error_details = {}

        for attempt in range(max_retries):
            try:
                # self._logger.info(f"Attempt {attempt + 1} to create SIP participant", request)
                participant = await livekit_api.sip.create_sip_participant(request)
                self._logger.info(f"Successfully created LiveKit SIP participant {participant} on attempt {attempt + 1}")
                return participant, room_name

            except Exception as e:
                import traceback
                attempt_num = attempt + 1
                self._logger.error(f"Attempt {attempt_num}/{max_retries} - Error creating LiveKit SIP participant: {e}")

                # Extract error details
                error_message = str(e)
                if hasattr(e, 'code'):
                    error_message = f"TelephonyError({e.code}): {error_message}"

                # Extract additional SIP metadata if available
                if hasattr(e, 'metadata') and e.metadata:
                    sip_error_details.update({
                        "sip_status": e.metadata.get('sip_status'),
                        "sip_status_code": e.metadata.get('sip_status_code'),
                        "error_details": e.metadata.get('error_details')
                    })

                # Store error information for this attempt
                sip_error_details.update({
                    "last_error": error_message,
                    "attempt": attempt_num,
                    "max_retries": max_retries
                })

                # If this was the last attempt, log final failure
                if attempt_num == max_retries:
                    self._logger.error(f"Failed to create LiveKit SIP participant after {max_retries} attempts")
                    self._logger.error(f"Full traceback:\n{traceback.format_exc()}")
                    # Create comprehensive error message with SIP details for task_end
                    comprehensive_error = error_message
                    if sip_error_details.get('sip_status') and sip_error_details.get('sip_status_code'):
                        comprehensive_error = f"{error_message} (SIP Status: {sip_error_details.get('sip_status_code')} - {sip_error_details.get('sip_status')}, Attempts: {attempt_num}/{max_retries})"

                    # Store comprehensive error information in user_state for task_end message
                    if self.user_state:
                        self.user_state.call_error = comprehensive_error
                        self.user_state.call_status = "failed"

                    # Close LiveKit API
                    await livekit_api.aclose()

                    return None, None
                else:
                    # Wait before retry (exponential backoff: 1, 2, 4 seconds)
                    wait_time = 2 ** attempt
                    self._logger.info(f"Waiting {wait_time} seconds before retry...")
                    await asyncio.sleep(wait_time)

        # Close API connection after all attempts (should not reach here, but safety check)
        await livekit_api.aclose()

        return None, None

    async def handover_call(self, handover_number: Optional[str] = None) -> Optional[Any]:
        """
        Transfer an active call to another number (handover).

        This method creates a new SIP participant in the same room to facilitate
        call transfer to a human agent or sales team.

        Args:
            handover_number: Optional phone number to transfer to.
                           If not provided, uses config value.

        Returns:
            Optional[Any]: Created SIP participant if successful, None otherwise
        """
        from livekit import api
        from livekit.protocol.sip import CreateSIPParticipantRequest, SIPParticipantInfo

        self._logger.info("Creating SIP participant for call handover")
        livekit_api = api.LiveKitAPI()

        trunk_id = self.config.get("trunk_id", os.getenv("SIP_OUTBOUND_TRUNK_ID"))
        handover_number = handover_number or self.config.get("handover_number")

        if not handover_number:
            self._logger.error("No handover number provided")
            return None

        print(f"Creating handover call to {handover_number}")
        self._logger.info(f"Creating handover call to {handover_number}")

        request = CreateSIPParticipantRequest(
            sip_trunk_id=trunk_id,
            sip_call_to=handover_number,
            room_name=self._room_name,
            participant_identity=handover_number,
            participant_name="test-handover",
            krisp_enabled=True,
            wait_until_answered=True
        )

        # Retry logic for SIP participant creation
        max_retries = 3

        for attempt in range(max_retries):
            try:
                participant = await livekit_api.sip.create_sip_participant(request)
                self._logger.info(f"Successfully created handover participant {participant} on attempt {attempt + 1}")
                return participant

            except Exception as e:
                import traceback
                attempt_num = attempt + 1
                self._logger.error(f"Attempt {attempt_num}/{max_retries} - Error creating SIP participant for handover: {e}")

                if attempt_num == max_retries:
                    self._logger.error(f"Failed to handover call after {max_retries} attempts")
                    self._logger.error(f"Full traceback:\n{traceback.format_exc()}")
                    return None
                else:
                    # Wait before retry (exponential backoff)
                    wait_time = 2 ** attempt
                    self._logger.info(f"Waiting {wait_time} seconds before retry...")
                    await asyncio.sleep(wait_time)

        # Close API connection after all attempts
        await livekit_api.aclose()

        return None

    def get_room_name(self) -> str:
        """
        Get the current room name.

        Returns:
            str: Current room name
        """
        return self._room_name

    def set_room_name(self, room_name: str) -> None:
        """
        Set a custom room name.

        Args:
            room_name: New room name to set
        """
        self._room_name = room_name

    def update_config(self, config: Dict[str, Any]) -> None:
        """
        Update the configuration dictionary.

        Args:
            config: New configuration dictionary
        """
        self.config.update(config)

    def __repr__(self) -> str:
        """String representation of SIPManager."""
        return f"SIPManager(session_id={self._session_id}, room_name={self._room_name})"

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"SIPManager for session {self._session_id} in room {self._room_name}"
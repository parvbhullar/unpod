"""
Transport Manager for Pipecat Voice Handler
Handles all transport-related operations including LiveKit room management,
transport configuration, and idle user handling.
"""
import random

import asyncio
import json
import logging
import os
import time
import uuid
from typing import Any, Dict, Optional

import aiohttp
import jwt

# Pipecat imports
from pipecat.audio.mixers.soundfile_mixer import SoundfileMixer
from pipecat.audio.turn.smart_turn.base_smart_turn import SmartTurnParams
from pipecat.audio.turn.smart_turn.local_smart_turn_v3 import LocalSmartTurnAnalyzerV3
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import EndFrame, TTSSpeakFrame
from pipecat.transports.base_transport import BaseTransport
from pipecat.transports.livekit.transport import LiveKitParams, LiveKitTransport
from livekit import api as lk_api

from super.core.logging.logging import print_log


async def configure_livekit(participant_name: str = "Pipecat Agent") -> tuple[str, str, str]:
    """
    Configure LiveKit room URL and token with custom participant identity.

    Unlike Pipecat's default configure(), this function allows specifying
    the participant name to ensure the Pipecat agent joins with the same
    identity as expected by the LiveKit room for agent state tracking.

    Args:
        participant_name: The identity/name for the agent participant.
            Defaults to "Pipecat Agent" for backwards compatibility.

    Returns:
        Tuple containing (url, token, room_name).

    Raises:
        Exception: If required LiveKit environment variables are not set.
    """
    room_name = os.getenv("LIVEKIT_ROOM_NAME")
    url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")

    if not room_name:
        raise Exception("LIVEKIT_ROOM_NAME must be set in environment variables.")
    if not url:
        raise Exception("LIVEKIT_URL must be set in environment variables.")
    if not api_key or not api_secret:
        raise Exception("LIVEKIT_API_KEY and LIVEKIT_API_SECRET must be set.")

    # Generate token with agent grants using custom participant identity
    token = lk_api.AccessToken(api_key, api_secret)
    token.with_identity(participant_name).with_name(participant_name).with_grants(
        lk_api.VideoGrants(
            room_join=True,
            room=room_name,
            agent=True,  # Mark as agent for proper state handling
        )
    )

    return (url, token.to_jwt(), room_name)
# LiveKit imports
# from livekit import api
# from livekit.agents import get_job_context

# Type imports
from super.core.voice.schema import TransportType, UserState
from pipecat.transcriptions.language import Language
# from pipecat.audio.filters.koala_filter import KoalaFilter


class TransportManager:
    """
    Manages transport operations for Pipecat voice handling.

    This class encapsulates all transport-related functionality including:
    - Creating and configuring LiveKit transports
    - Managing LiveKit rooms (creation/deletion)
    - Handling idle user detection and warnings
    - Safe call termination with cleanup
    """

    def __init__(
        self,
        logger: logging.Logger,
        config: Optional[Dict[str, Any]] = None,
        user_state: Optional[UserState] = None,
        room_name: Optional[str] = None,
        transport_type: TransportType = TransportType.LIVEKIT,
        task: Optional[Any] = None,
        active_sessions: Optional[Dict[str, Any]] = None,
        end_call_callback: Optional[callable] = None,
    ):
        """
        Initialize the TransportManager.

        Args:
            logger: Logger instance for logging operations
            config: Configuration dictionary containing agent settings
            user_state: Current user state information
            room_name: Name of the LiveKit room
            transport_type: Type of transport to use (default: LIVEKIT)
            task: Pipeline task instance
            active_sessions: Dictionary of active call sessions
            end_call_callback: Callback function to end the call
        """
        self._logger = logger
        self.config = config or {}
        self.user_state = user_state
        self._room_name = room_name
        self._transport_type = transport_type
        self.task = task
        self.active_sessions = active_sessions or {}
        self._end_call_callback = end_call_callback
        self._is_shutting_down = False

    async def get_transport(self) -> BaseTransport:
        """
        Get the appropriate transport based on configured transport type.

        Returns:
            BaseTransport: Configured transport instance
        """
        if self._transport_type == TransportType.LIVEKIT:
            return await self._get_livekit_transport(self.user_state)
        elif self._transport_type == TransportType.DAILY:
            return await self._get_daily_transport(self.user_state)

        return await self._get_livekit_transport(self.user_state)

    def get_outbound_number(self, config) -> Optional[str]:
        """
        Get the outbound caller ID number from config or environment variable.

        Returns:
            Optional[str]: Outbound caller ID number, or None if not set
        """
        telephony_list = [n.get("number", None) for n in config.get("telephony", []) if n.get("number")]
        print_log("telephony_numbers - ", [n for n in telephony_list])
        if not telephony_list:
            return os.getenv("SIP_OUTBOUND_CALLER_ID")
        tel_number = random.choice(telephony_list)
        return tel_number or os.getenv("SIP_OUTBOUND_CALLER_ID")

    async def _get_daily_transport(self, user_state: UserState) -> Any:
        from pipecat.transports.daily.transport import DailyParams, DailyTransport
        from pipecat.runner.daily import configure

        self._logger.info("Getting daily transport ready ")

        # IMPORTANT: Pass sip_caller_phone to enable dialout functionality for the room
        # When provided, pipecat will automatically set enable_dialout=True for the room
        # Use the actual contact number from user_state as the caller ID
        sip_caller_phone = self.get_outbound_number(self.config)

        self._logger.info(f"Creating Daily room with dialout enabled for: {sip_caller_phone}")

        async with aiohttp.ClientSession() as session:
            room_url, token = await configure(
                session,
                sip_caller_phone=sip_caller_phone,  # Enables dialout for the room
                sip_enable_video=False,  # Audio-only calls
            )

        user_state.room_name=room_url
        user_state.room_token=token
        user_state.dialout_from_number = sip_caller_phone
        if not self.config:
            self.config = user_state.model_config

        speaking_plan = self.config.get("speaking_plan", {})
        vad_params = VADParams(
            start_secs=speaking_plan.get("min_interruption_duration", 0.3),
            stop_secs=speaking_plan.get("min_silence_duration", 0.2),
        )
        vad_analyzer = SileroVADAnalyzer(params=vad_params)

        return DailyTransport(
            room_url,
            token,
            user_state.config.get("agent_id", "default-up-agent"),
            DailyParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                transcription_enabled=True,
                vad_analyzer=vad_analyzer,
                turn_analyzer=LocalSmartTurnAnalyzerV3(params=SmartTurnParams()),
            ),
        )


    async def _get_livekit_transport(self, user_state: UserState) -> Any:
        """
        Create and configure a LiveKit transport with audio mixer and VAD settings.
        Args:
            user_state: User state containing room and session information
        Returns:
            LiveKitTransport: Configured LiveKit transport instance
        """
        # Configure LiveKit session
        # Set environment variable for room name
        room_name = user_state.room_name or f"room-{user_state.thread_id}" if not self._room_name else self._room_name
        os.environ['LIVEKIT_ROOM_NAME'] = room_name

        # Use agent_name from config to ensure Pipecat joins with correct identity
        # This allows LiveKit client to properly track agent state
        agent_name = self.config.get("agent_name") if self.config else None
        if not agent_name:
            agent_name = f"agent-{uuid.uuid4().hex[:8]}"

        # Configure LiveKit session with custom participant identity
        (url, token, room_name) = await configure_livekit(participant_name=agent_name)
        self._logger.info(f"Connecting to LiveKit: {url}")
        self._logger.info(f"Room: {room_name}, Agent Identity: {agent_name}")

        if not self.config:
            self.config = user_state.model_config

        # Setup background sound mixer with office ambience
        audio_mixer = None
        try:
            # Get the directory of the current file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # Construct the path to the audio file relative to the current file
            ambience_path = os.path.join(
                current_dir,
                "assets",
                "examples_foundational_assets_office-ambience-24000-mono.mp3"
            )

            if os.path.exists(ambience_path):
                self._logger.info(f"Initializing background audio mixer with file: {ambience_path}")
                audio_mixer = SoundfileMixer(
                    sound_files={"office_ambience": ambience_path},
                    default_sound="office_ambience",
                    loop=True,
                    volume=0.3  # 30% volume (0.0 to 1.0 scale)
                )
                self._logger.info("Successfully initialized background audio mixer with 30% volume")
            else:
                self._logger.warning(f"Background audio file not found at: {ambience_path}")
        except Exception as e:
            self._logger.error(f"Error initializing audio mixer: {str(e)}", exc_info=True)
            audio_mixer = None

        # Create VAD analyzer with config from speaking plan or use defaults
        # Production-grade VAD settings for telephony/LiveKit:
        # - confidence: 0.65 (industry standard, prevents false positives from noise/breathing)
        # - start_secs: 0.2s (responsive interruption detection without sluggishness)
        # - stop_secs: 0.5s (allows natural pauses 200-500ms + network jitter 150-300ms)
        # - min_volume: 0.4 (works with AGC normalization, quieter speakers supported)
        speaking_plan = self.config.get("speaking_plan", {})

        try:
            vad_params = VADParams(
                confidence=0.6,  # Raised from 0.3 to prevent false positives on background noise
                start_secs=speaking_plan.get("min_interruption_duration", 0.2),
                stop_secs=speaking_plan.get("min_silence_duration", 0.3),
                min_volume=speaking_plan.get("min_volume", 0.4)
            )

            # Log VAD configuration for debugging and performance monitoring
            self._logger.info(
                f"VAD Configuration - confidence: {vad_params.confidence}, "
                f"start: {vad_params.start_secs}s, stop: {vad_params.stop_secs}s, "
                f"min_volume: {vad_params.min_volume}"
            )

            # Warn if speaking_plan overrides are potentially problematic
            if vad_params.stop_secs < 0.3:
                self._logger.warning(
                    f"VAD stop_secs={vad_params.stop_secs}s is aggressive (<0.3s). "
                    "May cause interruptions during natural pauses. "
                    "Consider increasing to 0.5s for better user experience."
                )

            if vad_params.confidence < 0.5:
                self._logger.warning(
                    f"VAD confidence={vad_params.confidence} is low (<0.5). "
                    "May trigger on background noise. Consider using 0.6-0.7 for telephony."
                )

            vad_analyzer = SileroVADAnalyzer(params=vad_params)
            self._logger.info("VAD analyzer initialized successfully with Silero model")

        except Exception as e:
            self._logger.error(f"Failed to initialize VAD analyzer: {e}", exc_info=True)
            # Fallback: Create VAD with safe production defaults
            self._logger.warning("Using fallback VAD configuration with safe defaults")
            try:
                vad_analyzer = SileroVADAnalyzer(params=vad_params)
                self._logger.info("Fallback VAD analyzer initialized successfully")
            except Exception as fallback_error:
                self._logger.critical(f"Fallback VAD initialization also failed: {fallback_error}")
                raise RuntimeError("Cannot initialize VAD analyzer - voice detection unavailable") from fallback_error

        # Create turn analyzer with config from speaking plan or use production defaults
        # Turn analyzer should coordinate with VAD timing to avoid race conditions:
        # - VAD stop_secs detects user pause (0.5s default)
        # - Turn stop_secs confirms end-of-turn (0.6s default, must be > VAD)
        # - This ensures proper handoff: VAD marks pause → Turn confirms completion
        try:
            turn_params = SmartTurnParams(
                # BUG FIX: Was using 'max_silence_duration' (doesn't exist), now using correct 'stop_secs'
                # Must be > VAD stop_secs to avoid race condition (VAD=0.5s, Turn=0.6s)
                stop_secs=speaking_plan.get("turn_stop_secs", 0.6),
                # Include 100ms of audio before speech starts for better ML model context
                pre_speech_ms=speaking_plan.get("pre_speech_ms", 100),
                # Allow up to 15 seconds for complex multi-sentence queries (was 8s default)
                max_duration_secs=speaking_plan.get("max_turn_duration", 8)
            )

            # Log turn analyzer configuration for debugging and performance monitoring
            self._logger.info(
                f"Turn Analyzer Configuration - stop: {turn_params.stop_secs}s, "
                f"pre_speech: {turn_params.pre_speech_ms}ms, "
                f"max_duration: {turn_params.max_duration_secs}s"
            )

            # Critical: Validate coordination with VAD to prevent race conditions
            # Turn analyzer should wait slightly longer than VAD for proper handoff
            if hasattr(vad_params, 'stop_secs') and turn_params.stop_secs <= vad_params.stop_secs:
                self._logger.warning(
                    f"Turn stop_secs ({turn_params.stop_secs}s) should be > VAD stop_secs ({vad_params.stop_secs}s) "
                    f"to avoid race conditions. Auto-adjusting to {vad_params.stop_secs + 0.1}s"
                )
                # Auto-fix: Add 100ms buffer to ensure turn waits for VAD
                turn_params.stop_secs = vad_params.stop_secs + 0.1

            turn_analyzer = LocalSmartTurnAnalyzerV3(params=turn_params)
            self._logger.info("Turn analyzer initialized successfully")

        except Exception as e:
            self._logger.error(f"Failed to initialize turn analyzer: {e}", exc_info=True)
            # Fallback: Create turn analyzer with safe production defaults
            self._logger.warning("Using fallback turn analyzer configuration")
            turn_params = SmartTurnParams(
                stop_secs=0.6,  # Safe default > VAD
                pre_speech_ms=100,
                max_duration_secs=8
            )
            try:
                turn_analyzer = LocalSmartTurnAnalyzerV3(params=turn_params)
                self._logger.info("Fallback turn analyzer initialized successfully")
            except Exception as fallback_error:
                self._logger.critical(f"Fallback turn analyzer initialization failed: {fallback_error}")
                raise RuntimeError("Cannot initialize turn analyzer - turn detection unavailable") from fallback_error

        # Create transport with audio mixer, VAD, and turn analyzer settings
        transport = LiveKitTransport(
            url=url,
            token=token,
            room_name=room_name,
            params=LiveKitParams(
                # audio_in_filter=KoalaFilter(access_key=os.getenv("KOALA_ACCESS_KEY")), # Enable Koala noise reduction
                audio_in_enabled=True,
                audio_out_enabled=True,
                video_out_enabled=False,  # Disable video to skip GPU encoder/decoder initialization
                audio_out_mixer=audio_mixer,
                vad_analyzer=vad_analyzer,
                turn_analyzer=turn_analyzer
            ),
        )
        return transport

    async def handle_idle_user(self, processor, retry_count: int) -> bool:
        """
        Handle idle user detection with progressive warnings and call termination.
        Args:
            processor: The processor handling the user's audio
            retry_count: Number of times the user has been idle (1-based)
        Returns:
            bool: True to continue the call, False to end it
        """
        if hasattr(self, '_is_shutting_down') and self._is_shutting_down:
            self._logger.info("Already shutting down, ignoring idle event")
            return False

        try:
            user_language = self.get_language(self.config.get("language", 'en'))

            if retry_count == 1:
                msg = self.get_message(user_language, "idle_warning_1")
                self._logger.info(f"First idle warning: {msg}")
                try:
                    await processor.push_frame(TTSSpeakFrame(msg))
                except Exception as e:
                    self._logger.error(f"Error sending first idle warning: {e}")
                return True

            elif retry_count == 2:
                msg = self.get_message(user_language, "idle_warning_2")
                self._logger.info(f"Second idle warning: {msg}")
                try:
                    await processor.push_frame(TTSSpeakFrame(msg))
                except Exception as e:
                    self._logger.error(f"Error sending second idle warning: {e}")
                return True

            else:
                msg = self.get_message(user_language, "idle_disconnect")
                self._logger.info(f"Ending call due to idle timeout: {msg}")

                # Send the goodbye message
                try:
                    await processor.push_frame(TTSSpeakFrame(msg))
                    # Give some time for the message to be spoken
                    await asyncio.sleep(2)
                except Exception as e:
                    self._logger.error(f"Error sending goodbye message: {e}")

                # End the call in a separate task to avoid blocking
                asyncio.create_task(self._safe_end_call("user_idle"))
                return False

        except Exception as e:
            self._logger.error(f"Error in handle_idle_user: {e}")
            # End the call in a separate task to avoid blocking
            asyncio.create_task(self._safe_end_call("idle_handler_error"))
            return False

    async def _safe_end_call(self, reason: str):
        """
        Safely end the call with proper error handling.

        Args:
            reason: Reason for ending the call
        """
        room_name = None
        try:
            # Get the room name before ending the call
            if hasattr(self, 'user_state') and hasattr(self.user_state, 'room_name'):
                room_name = self.user_state.room_name
                self._logger.info(f"Preparing to end call for room: {room_name}")
            else:
                self._logger.warning("No room name found in user_state")

            # Call the end_call callback if provided
            if self._end_call_callback:
                await self._end_call_callback(reason=reason)

        except Exception as e:
            self._logger.error(f"Error in _safe_end_call: {e}")
            # If end_call fails, try to force stop the task
            if hasattr(self, 'task') and hasattr(self.task, 'stop'):
                try:
                    await self.task.stop()
                except Exception as stop_err:
                    self._logger.error(f"Error stopping task: {stop_err}")
        finally:
            # Always attempt to delete the room, even if end_call fails
            if room_name:
                self._logger.info(f"Attempting to delete room: {room_name}")
                await self._delete_livekit_room(room_name)
            else:
                self._logger.warning("No room name available for deletion")

    async def _delete_livekit_room(self, room_name: str) -> bool:
        """
        Delete the LiveKit room.
        Args:
            room_name: Name of the room to delete
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            if not room_name:
                self._logger.warning("No room name provided for deletion")
                return False

            # Get LiveKit API key and secret from environment
            api_key = os.getenv("LIVEKIT_API_KEY")
            api_secret = os.getenv("LIVEKIT_API_SECRET")
            livekit_url = os.getenv("LIVEKIT_URL")

            if not all([api_key, api_secret, livekit_url]):
                self._logger.error("Missing required LiveKit API credentials in environment")
                return False

            try:
                # Create JWT token for authentication
                now = int(time.time())
                token = jwt.encode({
                    "iss": api_key,
                    "nbf": now - 5,
                    "exp": now + 30,
                    "name": "Room Deletion Service",
                    "roomAdmin": True,  # Add admin permissions
                    "room": room_name,  # Specify the room to delete
                    "video": {
                        "room": room_name,
                        "roomAdmin": True,  # Add room admin permissions
                        "roomCreate": True,  # Required for deletion
                        "roomList": True,  # Required for deletion
                        "roomJoin": True,
                        "canPublish": True,
                        "canSubscribe": True,
                        "canPublishData": True
                    }
                }, api_secret, algorithm="HS256")

                # Set up headers with Bearer token
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }

                # Log the room deletion attempt
                self._logger.info(f"Attempting to delete LiveKit room: {room_name}")

                # Make DELETE request to LiveKit API
                url = f"{livekit_url}/twirp/livekit.RoomService/DeleteRoom"
                data = json.dumps({"room": room_name})

                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, data=data) as response:
                        if response.status == 200:
                            self._logger.info(f"Successfully deleted LiveKit room: {room_name}")
                            return True
                        else:
                            error_text = await response.text()
                            self._logger.error(
                                f"Failed to delete room {room_name}. Status: {response.status}, Error: {error_text}")
                            return False

            except Exception as e:
                error_msg = str(e)
                self._logger.error(f"Error deleting LiveKit room {room_name}: {error_msg}")

                # If the room is already deleted or doesn't exist, that's fine
                if "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
                    self._logger.info(f"Room {room_name} was already deleted or never existed")
                    return True

                # For other errors, log and return False to indicate failure
                return False

        except Exception as e:
            self._logger.error(f"Error in room deletion process: {str(e)}")
            return False

    def get_language(self, language: str) -> Language:
        """
        Get the Language enum value for the given language code.

        Args:
            language: Language code (e.g., 'en', 'hi', 'pa', 'ta', 'ur')

        Returns:
            Language: Corresponding Language enum value
        """
        if language == "hi":
            return Language.HI
        elif language == "pa":
            return Language.PA
        elif language == "ta":
            return Language.TA
        elif language == "ur":
            return Language.UR
        else:
            return Language.EN

    def get_message(self, user_language: Language, param: str) -> str:
        """
        Get message based on language and parameter.

        Args:
            user_language: Language enum value
            param: Message parameter key

        Returns:
            str: Localized message string
        """
        messages = {
            "en": {
                "call_start": "Connecting your call, please wait...",
                "call_end": "Thank you for calling. Goodbye!",
                "call_error": "We're sorry, but there was an error connecting your call.",
                "idle_warning_1": "Are you still there? ",
                "idle_warning_2": "Would you like to continue our conversation?",
                "idle_disconnect": "No response detected. Ending the call now.",
            },
            "hi": {
                "call_start": "आपके कॉल को कनेक्ट किया जा रहा है, कृपया प्रतीक्षा करें...",
                "call_end": "कॉल के लिए धन्यवाद। अलविदा!",
                "call_error": "क्षमा करें, लेकिन आपके कॉल को कनेक्ट करने में त्रुटि हुई है।",
                "idle_warning_1": "क्या आप अभी भी यहाँ हैं?",
                "idle_warning_2": "क्या आप हमारी बातचीत जारी रखना चाहेंगे?",
                "idle_disconnect": "कोई response नहीं मिला। अब कॉल समाप्त कर रही हूँ।",
            },
            # Add more languages as needed
        }

        # Convert Language enum to string for lookup
        lang_str = str(user_language).split('.')[-1].lower()
        lang = lang_str if lang_str in messages else "en"
        return messages[lang].get(param, "")

    def set_task(self, task: Any):
        """
        Set the pipeline task instance.

        Args:
            task: Pipeline task instance
        """
        self.task = task

    def set_user_state(self, user_state: UserState):
        """
        Set the user state.

        Args:
            user_state: User state instance
        """
        self.user_state = user_state

    def set_end_call_callback(self, callback: callable):
        """
        Set the callback function for ending calls.

        Args:
            callback: Callback function to be called when ending a call
        """
        self._end_call_callback = callback

    def update_config(self, config: Dict[str, Any]):
        """
        Update the configuration.

        Args:
            config: Configuration dictionary to update with
        """
        if config:
            self.config.update(config)
"""
Transport Factory for SuperVoiceAgent - Dynamic transport creation and management
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type


class TransportAdapter(ABC):
    """Base class for transport adapters."""

    def __init__(self, options: Dict[str, Any], logger: logging.Logger):
        self.options = options
        self.logger = logger
        self._running = False
        self._sessions: Dict[str, Any] = {}

    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the transport."""
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from the transport."""
        pass

    @abstractmethod
    async def start_session(self, session_id: str, call_meta: Any) -> bool:
        """Start a session."""
        pass

    @abstractmethod
    async def receive_media_frame(self, session_id: str, frame: Any) -> bool:
        """Receive a media frame."""
        pass

    @abstractmethod
    async def send_media_frame(self, session_id: str, frame: Any) -> bool:
        """Send a media frame."""
        pass

    @abstractmethod
    async def close_session(
        self, session_id: str, reason: Optional[str] = None
    ) -> bool:
        """Close a session."""
        pass

    @abstractmethod
    async def get_session_state(self, session_id: str) -> Dict[str, Any]:
        """Get session state."""
        pass


class TransportAdapterFactory:
    """Factory for creating transport adapters."""

    _adapters: Dict[str, Type[TransportAdapter]] = {}

    @classmethod
    def register(
        cls, transport_type: str, adapter_class: Type[TransportAdapter]
    ) -> None:
        """Register a transport adapter."""
        cls._adapters[transport_type] = adapter_class

    @classmethod
    def load(
        cls, transport_type: str, options: Dict[str, Any]
    ) -> Optional[TransportAdapter]:
        """Load a transport adapter."""
        adapter_class = cls._adapters.get(transport_type)
        if adapter_class:
            return adapter_class(options, logging.getLogger(__name__))
        return None

    @classmethod
    def list_available(cls) -> list:
        """List available transport types."""
        return list(cls._adapters.keys())


# Import all available pipecat transports (using updated import paths)
# Each transport imported separately - Daily not available on Windows
PipecatLiveKit = None
PipecatDaily = None
PipecatWebRTC = None
PipecatWebSocket = None
PipecatWSServer = None
PIPECAT_AVAILABLE = False

try:
    from pipecat.transports.livekit.transport import LiveKitTransport as PipecatLiveKit

    PIPECAT_AVAILABLE = True
except ImportError:
    pass

try:
    from pipecat.transports.daily.transport import DailyTransport as PipecatDaily
except (ImportError, Exception):
    pass  # Daily not available on Windows

try:
    from pipecat.transports.services.small_webrtc import (
        SmallWebRTCTransport as PipecatWebRTC,
    )
except ImportError:
    pass

try:
    from pipecat.transports.services.fastapi_websocket import (
        FastAPIWebSocketTransport as PipecatWebSocket,
    )
except ImportError:
    pass

try:
    from pipecat.transports.network.websocket_server import (
        WebsocketServerTransport as PipecatWSServer,
    )
except ImportError:
    pass


class SuperTransportFactory:
    """Enhanced transport factory with automatic pipecat transport detection"""

    _transport_mapping = {
        "livekit": "LiveKitTransport",
        "daily": "DailyTransport",
        "webrtc": "SmallWebRTCTransport",
        "websocket": "FastAPIWebSocketTransport",
        "ws-server": "WebsocketServerTransport",
    }

    @classmethod
    def create_transport(
        cls,
        transport_type: str,
        options: Dict[str, Any],
        logger: Optional[logging.Logger] = None,
    ) -> Optional[TransportAdapter]:
        """
        Create transport adapter with fallback to pipecat transports

        Args:
            transport_type: Type of transport (livekit, daily, webrtc, websocket, ws-server)
            options: Transport configuration options
            logger: Optional logger instance

        Returns:
            Configured transport adapter or None if creation fails
        """
        logger = logger or logging.getLogger(__name__)

        try:
            # First try our custom transport adapters
            if transport_type in TransportAdapterFactory._adapters:
                return TransportAdapterFactory.load(transport_type, options)

            # Fallback to direct pipecat transport creation
            if PIPECAT_AVAILABLE:
                return cls._create_pipecat_transport(transport_type, options, logger)

            logger.error(
                f"Transport type '{transport_type}' not available and pipecat not installed"
            )
            return None

        except Exception as e:
            logger.error(f"Failed to create transport '{transport_type}': {e}")
            return None

    @classmethod
    def _create_pipecat_transport(
        cls, transport_type: str, options: Dict[str, Any], logger: logging.Logger
    ) -> Optional[TransportAdapter]:
        """Create direct pipecat transport wrapper"""

        if transport_type == "livekit":
            return cls._create_livekit_wrapper(options, logger)
        elif transport_type == "daily":
            return cls._create_daily_wrapper(options, logger)
        elif transport_type == "webrtc":
            return cls._create_webrtc_wrapper(options, logger)
        elif transport_type == "websocket":
            return cls._create_websocket_wrapper(options, logger)
        elif transport_type == "ws-server":
            return cls._create_ws_server_wrapper(options, logger)
        else:
            logger.error(f"Unknown pipecat transport type: {transport_type}")
            return None

    @classmethod
    def _create_livekit_wrapper(
        cls, options: Dict[str, Any], logger: logging.Logger
    ) -> Optional[TransportAdapter]:
        """Create LiveKit transport wrapper"""
        try:
            from .transport.livekit import LiveKitTransport

            return LiveKitTransport(options, logger)
        except Exception as e:
            logger.error(f"Failed to create LiveKit transport: {e}")
            return None

    @classmethod
    def _create_daily_wrapper(
        cls, options: Dict[str, Any], logger: logging.Logger
    ) -> Optional[TransportAdapter]:
        """Create Daily transport wrapper"""
        try:
            from .transport.daily import DailyTransport

            return DailyTransport(options, logger)
        except ImportError:
            # Create basic Daily transport wrapper if custom one doesn't exist
            return cls._create_generic_wrapper(PipecatDaily, options, logger)
        except Exception as e:
            logger.error(f"Failed to create Daily transport: {e}")
            return None

    @classmethod
    def _create_webrtc_wrapper(
        cls, options: Dict[str, Any], logger: logging.Logger
    ) -> Optional[TransportAdapter]:
        """Create WebRTC transport wrapper"""
        try:
            from .transport.webrtc import SmallWebRTCTransport

            return SmallWebRTCTransport(options, logger)
        except Exception as e:
            logger.error(f"Failed to create WebRTC transport: {e}")
            return None

    @classmethod
    def _create_websocket_wrapper(
        cls, options: Dict[str, Any], logger: logging.Logger
    ) -> Optional[TransportAdapter]:
        """Create WebSocket transport wrapper"""
        try:
            from .transport.websocket import FastAPIWebSocketTransport

            return FastAPIWebSocketTransport(options, logger)
        except Exception as e:
            logger.error(f"Failed to create WebSocket transport: {e}")
            return None

    @classmethod
    def _create_ws_server_wrapper(
        cls, options: Dict[str, Any], logger: logging.Logger
    ) -> Optional[TransportAdapter]:
        """Create WebSocket Server transport wrapper"""
        try:
            return cls._create_generic_wrapper(PipecatWSServer, options, logger)
        except Exception as e:
            logger.error(f"Failed to create WebSocket Server transport: {e}")
            return None

    @classmethod
    def _create_generic_wrapper(
        cls,
        pipecat_transport_class: Type,
        options: Dict[str, Any],
        logger: logging.Logger,
    ) -> Optional[TransportAdapter]:
        """Create generic wrapper for pipecat transports"""

        class GenericTransportWrapper(TransportAdapter):
            """Generic wrapper for pipecat transports"""

            def __init__(self, pipecat_class, options, logger):
                super().__init__(options, logger)
                self.pipecat_transport = None
                self.pipecat_class = pipecat_class

            async def connect(self) -> bool:
                try:
                    self.pipecat_transport = self.pipecat_class(**self.options)
                    await self.pipecat_transport.start()
                    self._running = True
                    return True
                except Exception as e:
                    self.logger.error(f"Failed to connect generic transport: {e}")
                    return False

            async def disconnect(self) -> bool:
                try:
                    if self.pipecat_transport:
                        await self.pipecat_transport.stop()
                    self._running = False
                    return True
                except Exception as e:
                    self.logger.error(f"Failed to disconnect generic transport: {e}")
                    return False

            async def start_session(self, session_id: str, call_meta) -> bool:
                self._sessions[session_id] = {"call_meta": call_meta, "state": "active"}
                return True

            async def receive_media_frame(self, session_id: str, frame) -> bool:
                if self.pipecat_transport and hasattr(
                    self.pipecat_transport, "push_frame"
                ):
                    await self.pipecat_transport.push_frame(frame)
                return True

            async def send_media_frame(self, session_id: str, frame) -> bool:
                return True

            async def close_session(
                self, session_id: str, reason: Optional[str] = None
            ) -> bool:
                if session_id in self._sessions:
                    del self._sessions[session_id]
                return True

            async def get_session_state(self, session_id: str) -> Dict[str, Any]:
                return self._sessions.get(session_id, {"error": "Session not found"})

        return GenericTransportWrapper(pipecat_transport_class, options, logger)

    @classmethod
    def list_available_transports(cls) -> Dict[str, str]:
        """List all available transport types"""
        available = {}

        # Add registered custom transports
        for transport_type in TransportAdapterFactory.list_available():
            available[transport_type] = "Custom Transport Adapter"

        # Add pipecat transports if available
        if PIPECAT_AVAILABLE:
            for transport_type, class_name in cls._transport_mapping.items():
                if transport_type not in available:  # Don't override custom adapters
                    available[transport_type] = f"Pipecat {class_name}"

        return available

    @classmethod
    def get_transport_config_schema(cls, transport_type: str) -> Dict[str, Any]:
        """Get configuration schema for a transport type"""
        schemas = {
            "livekit": {
                "url": {
                    "type": "string",
                    "required": True,
                    "description": "LiveKit server URL",
                },
                "api_key": {
                    "type": "string",
                    "required": True,
                    "description": "LiveKit API key",
                },
                "api_secret": {
                    "type": "string",
                    "required": True,
                    "description": "LiveKit API secret",
                },
                "room_name": {
                    "type": "string",
                    "default": "voice-session",
                    "description": "Room name",
                },
                "sip_trunk_id": {
                    "type": "string",
                    "required": False,
                    "description": "SIP trunk ID for telephony",
                },
            },
            "daily": {
                "url": {
                    "type": "string",
                    "required": True,
                    "description": "Daily room URL",
                },
                "token": {
                    "type": "string",
                    "required": False,
                    "description": "Daily meeting token",
                },
            },
            "webrtc": {
                "host": {
                    "type": "string",
                    "default": "localhost",
                    "description": "Server host",
                },
                "port": {
                    "type": "integer",
                    "default": 8080,
                    "description": "Server port",
                },
                "ssl_cert": {
                    "type": "string",
                    "required": False,
                    "description": "SSL certificate file",
                },
                "ssl_key": {
                    "type": "string",
                    "required": False,
                    "description": "SSL key file",
                },
            },
            "websocket": {
                "host": {
                    "type": "string",
                    "default": "localhost",
                    "description": "Server host",
                },
                "port": {
                    "type": "integer",
                    "default": 8000,
                    "description": "Server port",
                },
                "endpoint": {
                    "type": "string",
                    "default": "/ws",
                    "description": "WebSocket endpoint",
                },
            },
            "ws-server": {
                "host": {
                    "type": "string",
                    "default": "localhost",
                    "description": "Server host",
                },
                "port": {
                    "type": "integer",
                    "default": 8765,
                    "description": "Server port",
                },
                "audio_in_enabled": {
                    "type": "boolean",
                    "default": True,
                    "description": "Enable audio input",
                },
                "audio_out_enabled": {
                    "type": "boolean",
                    "default": True,
                    "description": "Enable audio output",
                },
            },
        }

        return schemas.get(transport_type, {})


# Auto-register transport factory
TransportAdapterFactory.create_transport = SuperTransportFactory.create_transport

# Alias for backward compatibility
TransportFactory = SuperTransportFactory

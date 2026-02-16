from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List

from super.core.callback.base import BaseCallback
from super.core.configuration import BaseModelConfig

# from super.core.context.schema import User


class Metrics:
    pass


class Modality(str, Enum):
    """Modality for voice agent sessions."""

    TEXT_AUDIO = "text_audio"  # Full voice mode with STT/TTS (default)
    TEXT = "text"  # Text-only hybrid mode (no STT/TTS)


@dataclass
class UserState:
    user_name: str = "User"
    space_name: str = "Unpod AI"
    contact_number: Optional[str] = None
    token: str = ""
    language: Optional[str] = None
    thread_id: str = ""
    user: dict = field(default_factory=dict)
    model_config: Optional[Dict[str, Any]] = None
    participant: Optional[Any] = None
    knowledge_base: list = field(default_factory=list)
    persona: Optional[str] = None
    system_prompt: Optional[str] = None
    first_message: Optional[str] = None
    objective: Optional[list] = field(default_factory=list)
    config: Optional[Dict[str, Any]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    usage: Optional[Dict] = field(default_factory=dict)
    recording_url: Optional[str] = None
    transcript: Optional[list] = field(default_factory=list)
    room_name: Optional[str] = None
    room_token: Optional[str] = None
    transport_type: Optional[str] = None
    call_error: Optional[str] = None
    call_status: Optional[str] = None
    end_reason: Optional[str] = None
    task_id: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = field(default_factory=dict)
    modality: str = Modality.TEXT_AUDIO  # text_audio (default) or text
    files: List[Dict[str, Any]] = field(default_factory=list)  # Attached files


@dataclass
class AgentConfig:
    """Enhanced agent configuration compatible with existing patterns"""

    agent_name: str = "SuperVoiceAgent"
    model_config: Optional[BaseModelConfig] = None
    custom_configs: Optional[Dict[str, Any]] = None
    callback: Optional[BaseCallback] = None
    transport_type: str = "livekit"  # livekit, webrtc, websocket
    transport_options: Dict[str, Any] = field(default_factory=dict)
    auto_answer: bool = True
    session_timeout: int = 300  # 5 minutes
    enable_sip: bool = True
    sip_trunk_id: Optional[str] = None
    knowledge_bases: List[str] = field(default_factory=list)


@dataclass
class CallSession:
    """Call session tracking"""

    session_id: str
    user_state: UserState
    context: Optional[Any] = None
    status: str = "initializing"  # initializing, active, ended
    pipeline_task: Optional[Any] = None
    context_aggregator: Optional[Any] = None
    created_at: datetime = field(default_factory=datetime.now)


class TransportType(str, Enum):
    LIVEKIT = "livekit"
    WEBRTC = "webrtc"
    WEBSOCKET = "websocket"
    DAILY = "daily"


@dataclass
class TaskData:
    assignee: str = None
    space_id: str = None
    user_id: str = None
    input: Optional[dict] = None
    output: Optional[dict] = None
    thread_id: Optional[str] = ""
    collection_ref: Optional[str] = ""
    ref_id: Optional[str] = ""
    status: Optional[Any] = None
    task_id: Optional[str] = None
    run_id: Optional[str] = None
    execution_type: Optional[str] = None


class CallStatusEnum(str, Enum):
    CONNECTED = "connected"
    NOT_CONNECTED = "notConnected"
    FAILED = "failed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    BUSY = "busy"
    VOICEMAIL = "voicemail"
    DROPPED = "droped"


@dataclass
class CallMeta:
    """Call metadata for session management"""

    call_id: str
    direction: str  # "inbound" or "outbound"
    from_number: Optional[str] = None
    to_number: Optional[str] = None
    sip_headers: Dict[str, Any] = field(default_factory=dict)
    custom_data: Dict[str, Any] = field(default_factory=dict)
    agent_name: Optional[str] = None

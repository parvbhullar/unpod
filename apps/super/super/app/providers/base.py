from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class CallResult:
    """Standard call result structure across all providers"""

    status: str
    call_id: Optional[str] = None
    customer: Optional[str] = None
    contact_number: Optional[str] = None
    call_end_reason: Optional[str] = None
    recording_url: Optional[str] = None
    transcript: Optional[list] = None
    error: Optional[str] = None
    notes: Optional[Dict[str, Any]] = field(default_factory=dict)
    call_summary: Optional[str] = None
    call_status: Optional[Any] = None
    status_update: Optional[str] = None
    data: Optional[Dict[str, Any]] = field(default_factory=dict)
    call_start: str = None
    call_end: str = None
    assistant_number: str = None
    duration: Optional[int] = 0


class CallProvider(ABC):
    """Abstract base class for call providers"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    @abstractmethod
    async def execute_call(
        self,
        agent_id: str,
        task_id: str,
        data: Dict[str, Any],
        instructions: Optional[str] = None,
        model_config: Any = None,
        callback: Any = None,
        call_type: str = "outbound",
    ) -> CallResult:
        """Execute a call using the specific provider"""
        pass

    @abstractmethod
    def supports_async(self) -> bool:
        """Whether this provider supports async operations"""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the name of this provider"""
        pass

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate if the data is suitable for this provider"""
        return "contact_number" in data or "room" in data

from typing import Dict, Any, Optional
from super.core.voice.providers.base import CallProvider
import os


class CallProviderFactory:
    """Factory class for creating call providers"""

    @staticmethod
    def create_provider(
        data: Dict[str, Any], config: Optional[Dict[str, Any]] = None
    ) -> CallProvider:
        provider = CallProviderFactory.get_provider_type(data)
        from .vapi_provider import VapiProvider
        from .livekit_provider import LiveKitProvider
        from .pipecat_provider import PipecatProvider

        if provider and provider == "livekit":
            return LiveKitProvider(config)
        elif provider and provider == "pipecat":
            return PipecatProvider(config)
        elif provider and provider == "vapi":
            return VapiProvider(config)
        elif any(
            key in data for key in ["phone", "number", "contact", "contact_number"]
        ):
            return VapiProvider(config)
        else:
            raise ValueError(
                "Unable to determine call provider. "
                "Data must contain either 'room' (for LiveKit) or 'contact_number' (for VAPI)"
            )

    @staticmethod
    def get_provider_type(data: Dict[str, Any]) -> str:
        quality = data.get("quality", "good")
        if quality == "high":
            provider = "vapi"
        else:
            provider = os.environ.get("AGENT_PROVIDER", "pipecat")
        return provider

    @staticmethod
    def get_available_providers() -> Dict[str, type]:
        from .vapi_provider import VapiProvider
        from .livekit_provider import LiveKitProvider
        from .pipecat_provider import PipecatProvider

        return {
            "vapi": VapiProvider,
            "livekit": LiveKitProvider,
            "pipecat": PipecatProvider,
        }

    @staticmethod
    def create_provider_by_name(
        provider_name: str, config: Optional[Dict[str, Any]] = None
    ) -> CallProvider:
        providers = CallProviderFactory.get_available_providers()

        if provider_name.lower() not in providers:
            available = ", ".join(providers.keys())
            raise ValueError(
                f"Unknown provider '{provider_name}'. Available providers: {available}"
            )

        provider_class = providers[provider_name.lower()]
        return provider_class(config)

"""
Voice services module - Lazy-loading service factories.

Import directly from submodules to avoid circular imports:
    from super.core.voice.services.lazy_factory import LazyServiceFactory
    from super.core.voice.services.livekit_services import LiveKitServiceFactory
"""

__all__ = [
    "LiveKitServiceFactory",
    "LiveKitServiceMode",
    "ServiceConfig",
    "InferenceFactory",
    "TransportFactory",
    "LazyServiceFactory",
]


def __getattr__(name: str):
    """Lazy import service factories to avoid heavy module side-effects."""
    if name in {"LiveKitServiceFactory", "LiveKitServiceMode", "ServiceConfig"}:
        from super.core.voice.services import livekit_services
        return getattr(livekit_services, name)
    if name == "InferenceFactory":
        from super.core.voice.services.inference_factory import InferenceFactory
        return InferenceFactory
    if name == "TransportFactory":
        from super.core.voice.services.transport_factory import TransportFactory
        return TransportFactory
    if name == "LazyServiceFactory":
        from super.core.voice.services.lazy_factory import LazyServiceFactory
        return LazyServiceFactory
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

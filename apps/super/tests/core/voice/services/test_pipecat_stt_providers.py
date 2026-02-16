import sys
import types

# Stub heavy imports before loading pipecat package
sys.modules.setdefault(
    "super.core.voice.managers.tools_manager",
    types.SimpleNamespace(ToolsManager=object),
)
sys.modules.setdefault(
    "super.core.voice.services.livekit_services",
    types.SimpleNamespace(
        DEFAULT_TTS_PROVIDER="openai",
        DEFAULT_TTS_MODEL="tts-1",
        DEFAULT_TTS_VOICE="alloy",
    ),
)
sys.modules.setdefault(
    "super.core.voice.pipecat.utils",
    types.SimpleNamespace(
        UpPipelineRunner=object,
        create_usage=lambda *_, **__: None,
        get_os_info=lambda *_, **__: None,
    ),
)

from super.core.voice.pipecat import services as svc


def test_stt_provider_dispatch_assemblyai():
    module = types.SimpleNamespace(AssemblyAISTTService=lambda **_: "assemblyai")
    sys.modules["pipecat.services.assemblyai.stt"] = module

    factory = svc.ServiceFactory({"stt_provider": "assemblyai"})
    stt = factory._create_stt_service()

    assert stt == "assemblyai"


def test_stt_provider_dispatch_speechmatics():
    module = types.SimpleNamespace(SpeechmaticsSTTService=lambda **_: "speechmatics")
    sys.modules["pipecat.services.speechmatics.stt"] = module

    factory = svc.ServiceFactory({"stt_provider": "speechmatics"})
    stt = factory._create_stt_service()

    assert stt == "speechmatics"


def test_stt_provider_missing_falls_back():
    sys.modules["pipecat.services.openai.stt"] = types.SimpleNamespace(
        OpenAISTTService=lambda **_: "openai"
    )

    factory = svc.ServiceFactory(
        {"stt_provider": "sarvam", "stt_model": "saarika:v2.5"}
    )
    stt = factory._create_stt_service()

    assert stt == "openai"

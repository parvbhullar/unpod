import importlib
import importlib.util
import sys
from pathlib import Path
import pytest

from tests.core.voice.helpers.runtime_imports import prepare_runtime_imports


def _load_service_common():
    root = Path(__file__).resolve().parents[4]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    module_path = root / "super" / "core" / "voice" / "services" / "service_common.py"
    spec = importlib.util.spec_from_file_location("service_common", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_livekit_import_resolves_sdk_when_test_path_is_present(monkeypatch):
    root = Path(__file__).resolve().parents[4]
    monkeypatch.syspath_prepend(str(root / "tests" / "core" / "voice"))
    sys.modules.pop("livekit", None)
    sys.modules.pop("livekit.api", None)
    shadowed_livekit = importlib.import_module("livekit")
    assert "tests/core/voice/livekit" in (getattr(shadowed_livekit, "__file__", "") or "")

    prepare_runtime_imports()
    from livekit import api  # type: ignore

    assert api is not None


def test_bson_stub_supports_objectid_import():
    objectid = importlib.import_module("bson.objectid")
    assert hasattr(objectid, "InvalidId")


def test_normalize_tts_provider_model_unpod_to_inworld():
    service_common = _load_service_common()
    provider, model = service_common.normalize_tts_provider_model(
        "unpod", "unpod-tts-1.5-max"
    )
    assert provider == "inworld"
    assert model == "inworld-tts-1.5-max"


def test_inference_flag_handles_dbeaver_values():
    service_common = _load_service_common()
    common = service_common.ServiceCommon({"tts_inference": "[v]"})
    assert common.get_inference_flag("tts_inference") is True
    common = service_common.ServiceCommon({"tts_inference": "[]"})
    assert common.get_inference_flag("tts_inference") is False


def test_should_use_inference_llm_env_gate(monkeypatch):
    service_common = _load_service_common()
    monkeypatch.setenv("AGENT_INFRA_MODE", "inference")
    cfg = {
        "llm_provider": "openai",
        "llm_model": service_common.INFERENCE_LLM_MODELS["openai"][0],
    }
    common = service_common.ServiceCommon(cfg)
    assert common.should_use_inference("llm") is True


def test_tts_inference_rejects_incompatible_elevenlabs_voice(monkeypatch):
    service_common = _load_service_common()
    monkeypatch.setenv("AGENT_INFRA_MODE", "inference")
    cfg = {
        "tts_provider": "elevenlabs",
        "tts_model": service_common.INFERENCE_TTS_MODELS["elevenlabs"][0],
        "tts_voice": "custom-voice-id",
    }
    common = service_common.ServiceCommon(cfg)
    assert common.should_use_inference("tts") is False


def test_livekit_factory_uses_shared_inference_logic(monkeypatch):
    root = Path(__file__).resolve().parents[4]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    prepare_runtime_imports()
    try:
        from super.core.voice.services.livekit_services import LiveKitServiceFactory
    except Exception as exc:
        pytest.skip(f"LiveKit services unavailable: {exc}")

    monkeypatch.setenv("AGENT_INFRA_MODE", "inference")
    config = {
        "llm_provider": "openai",
        "llm_model": "gpt-4o-mini",
        "stt_provider": "deepgram",
        "stt_model": "nova-3",
        "tts_provider": "cartesia",
        "tts_model": "sonic-3",
        "tts_voice": "95d51f79-c397-46f9-b49a-23763d3eaa2d",
    }
    factory = LiveKitServiceFactory(config)
    assert factory._common.should_use_inference("llm") is True

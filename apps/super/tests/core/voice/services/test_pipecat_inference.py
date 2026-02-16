import sys
from pathlib import Path
import types


def _install_pipecat_stubs(monkeypatch):
    monkeypatch.setitem(sys.modules, "pipecat", types.ModuleType("pipecat"))
    monkeypatch.setitem(sys.modules, "pipecat.services", types.ModuleType("pipecat.services"))
    monkeypatch.setitem(sys.modules, "pipecat.services.openai", types.ModuleType("pipecat.services.openai"))
    monkeypatch.setitem(sys.modules, "pipecat.adapters", types.ModuleType("pipecat.adapters"))
    monkeypatch.setitem(sys.modules, "pipecat.adapters.schemas", types.ModuleType("pipecat.adapters.schemas"))
    monkeypatch.setitem(sys.modules, "pipecat.pipeline", types.ModuleType("pipecat.pipeline"))
    monkeypatch.setitem(sys.modules, "pipecat.frames", types.ModuleType("pipecat.frames"))
    monkeypatch.setitem(sys.modules, "pipecat.processors", types.ModuleType("pipecat.processors"))
    monkeypatch.setitem(sys.modules, "pipecat.processors.filters", types.ModuleType("pipecat.processors.filters"))
    monkeypatch.setitem(sys.modules, "pipecat.transcriptions", types.ModuleType("pipecat.transcriptions"))

    parallel_pipeline_module = types.ModuleType("pipecat.pipeline.parallel_pipeline")

    class ParallelPipeline:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    parallel_pipeline_module.ParallelPipeline = ParallelPipeline
    monkeypatch.setitem(sys.modules, "pipecat.pipeline.parallel_pipeline", parallel_pipeline_module)

    frames_module = types.ModuleType("pipecat.frames.frames")

    class Frame:
        pass

    class TranscriptionFrame(Frame):
        def __init__(self, text=""):
            self.text = text

    frames_module.Frame = Frame
    frames_module.TranscriptionFrame = TranscriptionFrame
    monkeypatch.setitem(sys.modules, "pipecat.frames.frames", frames_module)

    function_filter_module = types.ModuleType("pipecat.processors.filters.function_filter")

    class FunctionFilter:
        def __init__(self, func):
            self.func = func

    function_filter_module.FunctionFilter = FunctionFilter
    monkeypatch.setitem(sys.modules, "pipecat.processors.filters.function_filter", function_filter_module)

    frame_processor_module = types.ModuleType("pipecat.processors.frame_processor")

    class FrameProcessor:
        def __init__(self, *args, **kwargs):
            pass

    frame_processor_module.FrameProcessor = FrameProcessor
    monkeypatch.setitem(sys.modules, "pipecat.processors.frame_processor", frame_processor_module)

    function_schema_module = types.ModuleType("pipecat.adapters.schemas.function_schema")

    class FunctionSchema:
        def __init__(self, name, description, properties, required):
            self.name = name
            self.description = description
            self.properties = properties
            self.required = required

        def to_default_dict(self):
            return {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.properties,
                    "required": self.required,
                },
            }

    function_schema_module.FunctionSchema = FunctionSchema

    tools_schema_module = types.ModuleType("pipecat.adapters.schemas.tools_schema")

    class ToolsSchema:
        def __init__(self, standard_tools):
            self.standard_tools = standard_tools

    tools_schema_module.ToolsSchema = ToolsSchema

    llm_service_module = types.ModuleType("pipecat.services.llm_service")

    class FunctionCallParams:
        def __init__(self, arguments=None, result_callback=None):
            self.arguments = arguments or {}
            self.result_callback = result_callback

    llm_service_module.FunctionCallParams = FunctionCallParams

    monkeypatch.setitem(sys.modules, "pipecat.services.llm_service", llm_service_module)
    monkeypatch.setitem(sys.modules, "pipecat.adapters.schemas.function_schema", function_schema_module)
    monkeypatch.setitem(sys.modules, "pipecat.adapters.schemas.tools_schema", tools_schema_module)

    llm_module = types.ModuleType("pipecat.services.openai.llm")

    class DummyOpenAILLMService:
        class InputParams:
            def __init__(self, *args, **kwargs):
                self.kwargs = kwargs

        def __init__(self, api_key=None, base_url=None, model=None, params=None, **kwargs):
            self.api_key = api_key
            self.base_url = base_url
            self.model = model
            self.params = params

    llm_module.OpenAILLMService = DummyOpenAILLMService
    monkeypatch.setitem(sys.modules, "pipecat.services.openai.llm", llm_module)

    language_module = types.ModuleType("pipecat.transcriptions.language")

    class Language:
        EN = "en"
        HI = "hi"
        PA = "pa"
        TA = "ta"
        UR = "ur"

    language_module.Language = Language
    monkeypatch.setitem(sys.modules, "pipecat.transcriptions.language", language_module)

    tts_module = types.ModuleType("pipecat.services.openai.tts")

    class DummyOpenAITTSService:
        def __init__(self, api_key=None, model=None, voice=None, language=None, instructions=None, **kwargs):
            self.api_key = api_key
            self.model = model
            self.voice = voice
            self.language = language
            self.instructions = instructions

    tts_module.OpenAITTSService = DummyOpenAITTSService
    monkeypatch.setitem(sys.modules, "pipecat.services.openai.tts", tts_module)

    livekit_utils = types.ModuleType("livekit.agents.inference._utils")

    def create_access_token(api_key, api_secret):
        return f"token:{api_key}:{api_secret}"

    livekit_utils.create_access_token = create_access_token

    monkeypatch.setitem(sys.modules, "livekit", types.ModuleType("livekit"))
    monkeypatch.setitem(sys.modules, "livekit.agents", types.ModuleType("livekit.agents"))
    monkeypatch.setitem(sys.modules, "livekit.agents.inference", types.ModuleType("livekit.agents.inference"))
    monkeypatch.setitem(sys.modules, "livekit.agents.inference._utils", livekit_utils)

    managers_pkg = types.ModuleType("super.core.voice.managers")
    managers_pkg.__path__ = []

    tools_manager_module = types.ModuleType("super.core.voice.managers.tools_manager")

    class ToolsManager:
        def __init__(self, config):
            self.config = config

        def build_function_schemas(self):
            return []

    tools_manager_module.ToolsManager = ToolsManager

    monkeypatch.setitem(sys.modules, "super.core.voice.managers", managers_pkg)
    monkeypatch.setitem(sys.modules, "super.core.voice.managers.tools_manager", tools_manager_module)


def test_pipecat_openai_llm_inference_path(monkeypatch):
    root = Path(__file__).resolve().parents[4]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    for key in list(sys.modules.keys()):
        if key == "super" or key.startswith("super."):
            sys.modules.pop(key, None)

    _install_pipecat_stubs(monkeypatch)

    monkeypatch.setenv("AGENT_INFRA_MODE", "inference")
    monkeypatch.setenv("LIVEKIT_INFERENCE_URL", "https://agent-gateway.livekit.cloud/v1")
    monkeypatch.setenv("LIVEKIT_INFERENCE_API_KEY", "test_key")
    monkeypatch.setenv("LIVEKIT_INFERENCE_API_SECRET", "test_secret")

    from super.core.voice.pipecat.services import ServiceFactory

    config = {
        "llm_provider": "openai",
        "llm_model": "gpt-4o-mini",
        "llm_inference": True,
    }

    factory = ServiceFactory(config)
    llm = factory._create_llm_service()
    assert getattr(llm, "base_url", None) == "https://agent-gateway.livekit.cloud/v1"


def test_pipecat_tts_provider_dispatch(monkeypatch):
    _install_pipecat_stubs(monkeypatch)

    root = Path(__file__).resolve().parents[4]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    from super.core.voice.pipecat.services import ServiceFactory

    config = {
        "tts_provider": "openai",
        "tts_model": "gpt-4o-mini-tts",
        "tts_voice": "alloy",
        "language": "en",
    }

    factory = ServiceFactory(config)
    tts = factory._create_tts_service()
    assert getattr(tts, "model", None) == "gpt-4o-mini-tts"

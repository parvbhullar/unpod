import importlib
import sys
import types


def ensure_bson_stubs() -> None:
    """Ensure bson symbols required by runtime imports are present in tests."""
    bson_module = types.ModuleType("bson")
    objectid_module = types.ModuleType("bson.objectid")

    class InvalidId(Exception):
        pass

    objectid_module.InvalidId = InvalidId
    bson_module.ObjectId = object
    bson_module.Decimal128 = object
    bson_module.objectid = objectid_module

    sys.modules["bson"] = bson_module
    sys.modules["bson.objectid"] = objectid_module


def ensure_real_livekit() -> None:
    """Prevent `tests/core/voice/livekit` package shadowing upstream `livekit`."""

    def _norm(path: str) -> str:
        return path.replace("\\", "/")

    livekit_mod = sys.modules.get("livekit")
    livekit_file = _norm(getattr(livekit_mod, "__file__", "") or "")
    shadowed = "tests/core/voice/livekit" in livekit_file

    if shadowed:
        for name in list(sys.modules):
            if name == "livekit" or name.startswith("livekit."):
                sys.modules.pop(name, None)

    sys.path = [
        p
        for p in sys.path
        if not _norm(p).endswith("/tests/core/voice")
        and not _norm(p).endswith("/tests/core/voice/livekit")
    ]

    if "livekit" not in sys.modules:
        importlib.import_module("livekit")


def ensure_lightweight_prompt_manager() -> None:
    """Stub PromptManager imports to avoid heavy manager side effects in tests."""
    managers_pkg = types.ModuleType("super.core.voice.managers")
    managers_pkg.__path__ = []

    prompt_module = types.ModuleType("super.core.voice.managers.prompt_manager")

    class PromptManager:
        def __init__(self, *args, **kwargs):
            self.user_state = None

        def _create_assistant_prompt(self):
            return ""

        def _replace_template_params(self, text: str) -> str:
            return text

        def get_message(self, _lang: str, _param: str):
            return None

    prompt_module.PromptManager = PromptManager

    sys.modules["super.core.voice.managers"] = managers_pkg
    sys.modules["super.core.voice.managers.prompt_manager"] = prompt_module


def prepare_runtime_imports(*, lite_handler_safe: bool = False) -> None:
    ensure_bson_stubs()
    ensure_real_livekit()
    if lite_handler_safe:
        ensure_lightweight_prompt_manager()

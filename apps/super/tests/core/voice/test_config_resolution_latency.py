import ast
from pathlib import Path


SOURCE_PATH = Path("super/core/voice/voice_agent_handler.py")


def _class_and_methods():
    module = ast.parse(SOURCE_PATH.read_text(encoding="utf-8"))
    class_node = next(
        node
        for node in module.body
        if isinstance(node, ast.ClassDef) and node.name == "VoiceAgentHandler"
    )
    methods = {}
    for node in class_node.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods[node.name] = node
    return methods


def test_get_config_with_cache_uses_asyncio_to_thread() -> None:
    methods = _class_and_methods()
    method = methods["_get_config_with_cache"]
    has_to_thread_call = False
    for node in ast.walk(method):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if (
                isinstance(node.func.value, ast.Name)
                and node.func.value.id == "asyncio"
                and node.func.attr == "to_thread"
            ):
                has_to_thread_call = True
                break
    assert has_to_thread_call


def test_resolve_agent_config_has_no_sync_get_space_id_call() -> None:
    methods = _class_and_methods()
    method = methods["_resolve_agent_config"]
    for node in ast.walk(method):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "get_space_id"

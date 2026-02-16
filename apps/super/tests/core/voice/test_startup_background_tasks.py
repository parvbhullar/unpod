import ast
from pathlib import Path


SOURCE_PATH = Path("super/core/voice/voice_agent_handler.py")


def _class_methods():
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


def test_recording_background_helper_uses_wait_for_timeout() -> None:
    methods = _class_methods()
    method = methods["_start_recording_background"]
    found_wait_for = False
    for node in ast.walk(method):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if (
                isinstance(node.func.value, ast.Name)
                and node.func.value.id == "asyncio"
                and node.func.attr == "wait_for"
            ):
                found_wait_for = True
                timeout_kw = next((kw for kw in node.keywords if kw.arg == "timeout"), None)
                assert timeout_kw is not None
                assert isinstance(timeout_kw.value, ast.Constant)
                assert timeout_kw.value.value == 2.0
    assert found_wait_for


def test_entrypoint_schedules_recording_helper_in_background() -> None:
    methods = _class_methods()
    entrypoint = methods["entrypoint"]
    helper_used = False
    for node in ast.walk(entrypoint):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "_start_recording_background":
                helper_used = True
                break
    assert helper_used

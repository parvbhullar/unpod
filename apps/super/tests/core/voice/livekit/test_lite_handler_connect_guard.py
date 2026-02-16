import ast
from pathlib import Path


SOURCE_PATH = Path("super/core/voice/livekit/lite_handler.py")


def _class_methods():
    module = ast.parse(SOURCE_PATH.read_text(encoding="utf-8"))
    class_node = next(
        node
        for node in module.body
        if isinstance(node, ast.ClassDef) and node.name == "LiveKitLiteHandler"
    )
    methods = {}
    for node in class_node.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods[node.name] = node
    return methods


def test_lite_handler_has_connect_guard_helper() -> None:
    methods = _class_methods()
    assert "_connect_room_if_needed" in methods


def test_execute_with_context_uses_connect_guard_helper() -> None:
    methods = _class_methods()
    execute_with_context = methods["execute_with_context"]
    helper_call_found = False

    for node in ast.walk(execute_with_context):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if (
                isinstance(node.func.value, ast.Name)
                and node.func.value.id == "self"
                and node.func.attr == "_connect_room_if_needed"
            ):
                helper_call_found = True
            if (
                isinstance(node.func.value, ast.Name)
                and node.func.value.id == "ctx"
                and node.func.attr == "connect"
            ):
                raise AssertionError("execute_with_context should not call ctx.connect directly")

    assert helper_call_found

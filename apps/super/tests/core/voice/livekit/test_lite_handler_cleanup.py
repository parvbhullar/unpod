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


def test_execute_with_context_uses_runtime_cleanup_helper() -> None:
    methods = _class_methods()
    execute_with_context = methods["execute_with_context"]
    helper_call_found = False

    for node in ast.walk(execute_with_context):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if (
                isinstance(node.func.value, ast.Name)
                and node.func.value.id == "self"
                and node.func.attr == "_cleanup_runtime_resources"
            ):
                helper_call_found = True
                break

    assert helper_call_found


def test_end_call_uses_runtime_cleanup_helper() -> None:
    methods = _class_methods()
    end_call = methods["end_call"]
    helper_call_found = False

    for node in ast.walk(end_call):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if (
                isinstance(node.func.value, ast.Name)
                and node.func.value.id == "self"
                and node.func.attr == "_cleanup_runtime_resources"
            ):
                helper_call_found = True
                break

    assert helper_call_found


def test_runtime_cleanup_helper_exists_and_targets_background_tasks() -> None:
    methods = _class_methods()
    assert "_cleanup_runtime_resources" in methods
    cleanup = methods["_cleanup_runtime_resources"]

    referenced_attrs = {
        node.attr
        for node in ast.walk(cleanup)
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self"
    }
    assert "_kb_warmup_task" in referenced_attrs
    assert "_participant_stt_tasks" in referenced_attrs
    assert "_participant_stt_streams" in referenced_attrs

    called_self_methods = {
        node.func.attr
        for node in ast.walk(cleanup)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "self"
    }
    assert "_stop_idle_monitor" in called_self_methods
    assert "_stop_background_audio" in called_self_methods

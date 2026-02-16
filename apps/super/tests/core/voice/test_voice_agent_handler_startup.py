import ast
from pathlib import Path


SOURCE_PATH = Path("super/core/voice/voice_agent_handler.py")


def _module_ast() -> ast.Module:
    return ast.parse(SOURCE_PATH.read_text(encoding="utf-8"))


def test_has_single_shot_assistant_task_helper() -> None:
    module = _module_ast()
    class_node = next(
        node
        for node in module.body
        if isinstance(node, ast.ClassDef) and node.name == "VoiceAgentHandler"
    )
    helper_names = {
        node.name for node in class_node.body if isinstance(node, ast.FunctionDef)
    }
    assert "_start_assistant_task" in helper_names


def test_entrypoint_uses_assistant_task_helper_instead_of_raw_create_task() -> None:
    module = _module_ast()
    class_node = next(
        node
        for node in module.body
        if isinstance(node, ast.ClassDef) and node.name == "VoiceAgentHandler"
    )
    entrypoint_node = next(
        node
        for node in class_node.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "entrypoint"
    )

    helper_call_count = 0
    for node in ast.walk(entrypoint_node):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            # Ensure entrypoint doesn't directly call asyncio.create_task(self._create_assistant(...))
            if node.func.attr == "create_task" and node.args:
                first_arg = node.args[0]
                if (
                    isinstance(first_arg, ast.Call)
                    and isinstance(first_arg.func, ast.Attribute)
                    and first_arg.func.attr == "_create_assistant"
                ):
                    raise AssertionError(
                        "entrypoint directly schedules _create_assistant via create_task"
                    )
            if node.func.attr == "_start_assistant_task":
                helper_call_count += 1
                kw = {
                    k.arg: k.value
                    for k in node.keywords
                    if k.arg is not None
                }
                assert "existing_task" in kw
                assert isinstance(kw["existing_task"], ast.Name)
                assert kw["existing_task"].id == "pipecat_task"
    assert helper_call_count >= 2

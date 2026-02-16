import ast
from pathlib import Path


SOURCE_PATH = Path("super/core/voice/voice_agent_handler.py")


def _read_literal_assignment(name: str):
    module = ast.parse(SOURCE_PATH.read_text(encoding="utf-8"))
    for node in module.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return ast.literal_eval(node.value)
    raise AssertionError(f"{name} not found")


def test_required_startup_stages_defined() -> None:
    required = _read_literal_assignment("REQUIRED_STARTUP_PERF_STAGES")
    assert set(required) == {
        "room_connect",
        "config_resolution",
        "pipecat_setup",
        "total_entrypoint",
    }


def test_required_startup_stages_have_budgets() -> None:
    required = _read_literal_assignment("REQUIRED_STARTUP_PERF_STAGES")
    budgets = _read_literal_assignment("STARTUP_STAGE_BUDGETS_MS")
    for stage in required:
        assert stage in budgets
        assert budgets[stage] > 0

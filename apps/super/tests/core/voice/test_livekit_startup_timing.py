import ast
from pathlib import Path


def _read_startup_budget_mapping() -> dict:
    source_path = Path("super/core/voice/voice_agent_handler.py")
    module = ast.parse(source_path.read_text(encoding="utf-8"))
    for node in module.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "STARTUP_STAGE_BUDGETS_MS":
                    return ast.literal_eval(node.value)
    raise AssertionError("STARTUP_STAGE_BUDGETS_MS not found")


def test_stage_budget_constants_exist() -> None:
    budgets = _read_startup_budget_mapping()
    assert "room_connect" in budgets
    assert "config_resolution" in budgets


def test_required_stage_budgets_are_positive() -> None:
    budgets = _read_startup_budget_mapping()
    required = ("assistant_create", "pipecat_setup", "total_entrypoint")
    for stage in required:
        assert budgets[stage] > 0

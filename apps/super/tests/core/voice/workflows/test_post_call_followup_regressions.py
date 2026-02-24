from datetime import datetime, timezone
import importlib
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock
import sys
import types

import pytest

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Keep imports isolated from real DB/bootstrap in model modules.
fake_config = types.ModuleType("super_services.libs.config")
fake_config.settings = SimpleNamespace(MONGO_DSN="mongodb://localhost:27017", MONGO_DB="test")
sys.modules["super_services.libs.config"] = fake_config

fake_db = types.ModuleType("super_services.libs.core.db")
fake_db.executeQuery = lambda *args, **kwargs: {}
sys.modules["super_services.libs.core.db"] = fake_db

fake_model_config = types.ModuleType("super_services.voice.models.config")

class _DummyModelConfig:
    pass

fake_model_config.ModelConfig = _DummyModelConfig
sys.modules["super_services.voice.models.config"] = fake_model_config

fake_task_service = types.ModuleType("super_services.orchestration.task.task_service")

class _DummyTaskService:
    def get_task(self, *_args, **_kwargs):
        return None

fake_task_service.TaskService = _DummyTaskService
sys.modules["super_services.orchestration.task.task_service"] = fake_task_service

fake_voice_eval = types.ModuleType("super.core.voice.voice_agent_evals.voice_evaluation")

async def _dummy_evaluate_voice_call(**_kwargs):
    return {
        "session_id": None,
        "evaluation_results": [],
        "quality_metrics": {},
        "audio_file_path": None,
    }

fake_voice_eval.evaluate_voice_call = _dummy_evaluate_voice_call
sys.modules["super.core.voice.voice_agent_evals.voice_evaluation"] = fake_voice_eval

# Force local `super` package resolution (some environments include a third-party `super` package).
local_super_init = ROOT / "super" / "__init__.py"
spec = importlib.util.spec_from_file_location("super", local_super_init)
local_super = importlib.util.module_from_spec(spec)
spec.loader.exec_module(local_super)
local_super.__path__ = [str(ROOT / "super")]
sys.modules["super"] = local_super


def _import(path: str):
    loaded_super = sys.modules.get("super")
    loaded_from = str(getattr(loaded_super, "__file__", "") or "")
    expected_prefix = str(ROOT / "super")
    if loaded_super and expected_prefix not in loaded_from:
        for name in list(sys.modules):
            if name == "super" or name.startswith("super."):
                sys.modules.pop(name, None)
    return importlib.import_module(path)


class _FakeAnalyzerResult:
    def __init__(self, requires_followup=True, followup_time=None, reason=""):
        self.requires_followup = requires_followup
        self.followup_time = followup_time or datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)
        self.reason = reason


class _FakeAnalyzerCallable:
    def __init__(self, result):
        self._result = result

    def __call__(self, **_kwargs):
        return self._result


@pytest.mark.unit
def test_followup_analyzer_blocks_when_next_retry_reaches_total_max(monkeypatch):
    FollowUpAnalyzer = _import(
        "super.core.voice.workflows.tools.call_scheduler"
    ).FollowUpAnalyzer
    analyzer = object.__new__(FollowUpAnalyzer)
    analyzer.lm = object()
    analyzer.analyzer = _FakeAnalyzerCallable(
        _FakeAnalyzerResult(requires_followup=True, reason="model says retry")
    )

    monkeypatch.setattr(
        analyzer,
        "_get_logs",
        lambda *args, **kwargs: [{"output": {"followup_count": 3}}],
    )
    monkeypatch.setattr(analyzer, "_extract_max_calls", lambda _prompt: 4)

    result = FollowUpAnalyzer.forward(
        analyzer,
        call_transcript="",
        prompt="initial call + 3 retries",
        token="token",
        document_id="doc-id",
    )

    assert result.followup_required is False
    assert "max_calls=4" in result.reason


@pytest.mark.unit
def test_followup_analyzer_accepts_loose_true_string(monkeypatch):
    FollowUpAnalyzer = _import(
        "super.core.voice.workflows.tools.call_scheduler"
    ).FollowUpAnalyzer
    analyzer = object.__new__(FollowUpAnalyzer)
    analyzer.lm = object()
    analyzer.analyzer = _FakeAnalyzerCallable(
        _FakeAnalyzerResult(requires_followup="TRUE.", reason="retry needed")
    )

    monkeypatch.setattr(analyzer, "_get_logs", lambda *args, **kwargs: [])
    monkeypatch.setattr(analyzer, "_extract_max_calls", lambda _prompt: 4)

    result = FollowUpAnalyzer.forward(
        analyzer,
        call_transcript="",
        prompt="retry",
        token="token",
        document_id="doc-id",
    )

    assert result.followup_required is True


@pytest.mark.asyncio
@pytest.mark.unit
async def test_post_call_follow_up_passes_model_max_calls_to_scheduler(monkeypatch):
    PostCallWorkflow = _import("super.core.voice.workflows.post_call").PostCallWorkflow
    workflow = object.__new__(PostCallWorkflow)
    workflow.follow_up_enabled = True
    workflow.followup_prompt = "initial call + 3 retries"
    workflow.transcript = []
    workflow.token = "token"
    workflow.document_id = "doc-id"
    workflow.data = {"task_id": "task-1"}
    workflow.model_config = {}
    workflow.agent = "agent-x"
    workflow.user_state = None

    workflow.follow_up_service = SimpleNamespace(
        forward=lambda **_kwargs: SimpleNamespace(
            followup_required=True,
            followup_time=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
            reason="allowed",
            max_calls=4,
        )
    )

    captured = {}

    async def _fake_create_follow_up_task(time, max_calls):
        captured["time"] = time
        captured["max_calls"] = max_calls
        return "call_scheduled"

    workflow.create_follow_up_task = _fake_create_follow_up_task
    workflow._get_available_slots = lambda: {}

    result = await PostCallWorkflow.follow_up(workflow)

    assert result["required"] is True
    assert captured["max_calls"] == 4


@pytest.mark.asyncio
@pytest.mark.unit
async def test_in_call_handover_summary_uses_handover_prompt():
    InCallWorkflow = _import("super.core.voice.workflows.in_call").InCallWorkflow
    workflow = object.__new__(InCallWorkflow)
    workflow.logger = MagicMock()
    workflow.user_state = SimpleNamespace(
        transcript=[{"role": "assistant", "content": "Hi"}],
        start_time=datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc),
        model_config={"handover_prompt": "Use concise handover format"},
    )

    captured = {}

    class _FakeSummarizer:
        def forward(self, call_transcript, call_datetime, prompt):
            captured["call_transcript"] = call_transcript
            captured["call_datetime"] = call_datetime
            captured["prompt"] = prompt
            return SimpleNamespace(summary="handover summary")

    workflow.summarizer = _FakeSummarizer()

    async def _fake_fetch_history():
        return []

    workflow._fetch_past_call_history = _fake_fetch_history

    response = await InCallWorkflow.generate_handover_summary(workflow)

    assert response["handover_summary"]["current_call"]["summary"] == "handover summary"
    assert captured["prompt"] == "Use concise handover format"

from types import SimpleNamespace
from unittest.mock import MagicMock

from tests.core.voice.helpers.runtime_imports import prepare_runtime_imports


def _load_lite_agent_module():
    prepare_runtime_imports()
    import super.core.voice.livekit.livekit_lite_agent as lka

    return lka


class _FakeTopic:
    def __init__(self, topic_id: str, content: str, delivered: bool = False):
        self.id = topic_id
        self.content = content
        self.delivered = delivered


class _FakeConvState:
    def __init__(self):
        self.marked = []
        self.user_info = {}
        self.objective_achieved = False
        self.objective_outcome = None
        self._topics = [
            _FakeTopic("pricing", "pricing benefits and details"),
            _FakeTopic("location", "location and distance"),
        ]

    def record_agent_response(self, **_kwargs):
        return {"issues": []}

    def mark_block_delivered(self, topic_id: str):
        self.marked.append(topic_id)
        for topic in self._topics:
            if topic.id == topic_id:
                topic.delivered = True

    def record_user_info_item(self, key: str, value: str):
        self.user_info[key] = value

    def get_delivery_progress(self):
        delivered = sum(1 for t in self._topics if t.delivered)
        return {"delivered": delivered, "total": len(self._topics)}

    def get_topics(self):
        return self._topics


def test_process_llm_response_parses_codeblock_json() -> None:
    lka = _load_lite_agent_module()
    agent = object.__new__(lka.LiveKitLiteAgent)
    agent._logger = MagicMock()
    agent._conv_state = _FakeConvState()
    agent._record_agent_response = lambda _response: None

    agent._process_llm_response(
        'hello ```json {"covered":["pricing"],"user_info":{"name":"sam"},'
        '"objective_outcome":"primary_success"} ```'
    )

    assert "pricing" in agent._conv_state.marked
    assert agent._conv_state.user_info["name"] == "sam"
    assert agent._conv_state.objective_achieved is True
    assert agent._conv_state.objective_outcome == "primary_success"


def test_truncate_context_respects_effective_limit() -> None:
    lka = _load_lite_agent_module()
    agent = object.__new__(lka.LiveKitLiteAgent)
    agent._logger = MagicMock()
    agent._effective_context_limit = 50
    agent._max_turns = 2

    messages = [
        SimpleNamespace(role="system", content="system instructions " * 20),
        SimpleNamespace(role="user", content="u1 " * 60),
        SimpleNamespace(role="assistant", content="a1 " * 60),
        SimpleNamespace(role="user", content="u2 " * 60),
        SimpleNamespace(role="assistant", content="a2 " * 60),
    ]

    out = agent._truncate_context_to_limit(messages)

    assert len(out) >= 1
    assert len(out) <= len(messages)
    assert any(getattr(msg, "role", "") == "system" for msg in out)

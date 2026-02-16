from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from tests.core.voice.helpers.runtime_imports import prepare_runtime_imports


def _load_lite_agent_module():
    prepare_runtime_imports()
    import super.core.voice.livekit.livekit_lite_agent as lka

    return lka


@pytest.mark.asyncio
async def test_end_call_tool_returns_testing_mode_status() -> None:
    lka = _load_lite_agent_module()

    agent = object.__new__(lka.LiveKitLiteAgent)
    agent._logger = MagicMock()
    agent.testing_mode = True

    result = await agent.end_call_tool(MagicMock(), reason="user_goodbye")

    assert result["status"] == "call ended successfully"


@pytest.mark.asyncio
async def test_tts_node_strips_command_tags(monkeypatch) -> None:
    lka = _load_lite_agent_module()
    agent = object.__new__(lka.LiveKitLiteAgent)

    captured_text_chunks = []

    async def fake_tts_node(_self_ref, text_iter, _model_settings):
        async for chunk in text_iter:
            captured_text_chunks.append(chunk)
            yield chunk.upper()

    monkeypatch.setattr(
        lka.Agent,
        "default",
        SimpleNamespace(tts_node=fake_tts_node),
        raising=False,
    )

    async def text_stream():
        yield "Hello there <Disconnect the call>"
        yield " <Transfer the call here> "
        yield "thanks"

    output = []
    async for frame in agent.tts_node(text_stream(), model_settings=None):
        output.append(frame)

    assert captured_text_chunks == ["Hello there", "thanks"]
    assert output == ["HELLO THERE", "THANKS"]

from types import SimpleNamespace
from unittest.mock import MagicMock
from time import perf_counter

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

    combined = "".join(captured_text_chunks)
    normalized = " ".join(combined.split())

    assert "<" not in combined
    assert ">" not in combined
    assert normalized == "Hello there thanks"
    assert " ".join("".join(output).split()) == "HELLO THERE THANKS"


@pytest.mark.asyncio
async def test_tts_node_handles_split_command_tags_without_word_join(monkeypatch) -> None:
    lka = _load_lite_agent_module()
    agent = object.__new__(lka.LiveKitLiteAgent)

    captured_text_chunks = []

    async def fake_tts_node(_self_ref, text_iter, _model_settings):
        async for chunk in text_iter:
            captured_text_chunks.append(chunk)
            yield chunk

    monkeypatch.setattr(
        lka.Agent,
        "default",
        SimpleNamespace(tts_node=fake_tts_node),
        raising=False,
    )

    async def text_stream():
        yield "Great! So I can see"
        yield " you were purchasing"
        yield " <Tran"
        yield "sfer the call here>"
        yield " bonsai plants"
        yield " on our website."

    async for _ in agent.tts_node(text_stream(), model_settings=None):
        pass

    combined = "".join(captured_text_chunks)
    normalized = " ".join(combined.split())

    assert "<" not in combined
    assert ">" not in combined
    assert "purchasingbonsai" not in combined
    assert normalized == "Great! So I can see you were purchasing bonsai plants on our website."


@pytest.mark.asyncio
async def test_tts_node_retries_with_ascii_fallback_on_no_audio_frames(monkeypatch) -> None:
    lka = _load_lite_agent_module()
    agent = object.__new__(lka.LiveKitLiteAgent)
    agent._logger = MagicMock()

    captured_passes = []

    async def fake_tts_node(_self_ref, text_iter, _model_settings):
        chunks = []
        async for chunk in text_iter:
            chunks.append(chunk)
        text = "".join(chunks)
        captured_passes.append(text)

        if len(captured_passes) == 1:
            raise RuntimeError(f"no audio frames were pushed for text: {text}")
        yield "AUDIO_FRAME"

    monkeypatch.setattr(
        lka.Agent,
        "default",
        SimpleNamespace(tts_node=fake_tts_node),
        raising=False,
    )

    async def text_stream():
        yield "Hello I am Saanvi from वाजीराम & Ravi."
        yield " How may I assist you today?"

    output = []
    async for frame in agent.tts_node(text_stream(), model_settings=None):
        output.append(frame)

    assert output == ["AUDIO_FRAME"]
    assert len(captured_passes) == 2
    assert "वाजीराम" in captured_passes[0]
    assert "वाजीराम" not in captured_passes[1]
    assert "&" not in captured_passes[1]
    assert "and" in captured_passes[1]


@pytest.mark.asyncio
async def test_tts_node_strips_split_tool_code_without_skipping_normal_words(
    monkeypatch,
) -> None:
    lka = _load_lite_agent_module()
    agent = object.__new__(lka.LiveKitLiteAgent)
    agent._logger = MagicMock()

    captured_text_chunks = []

    async def fake_tts_node(_self_ref, text_iter, _model_settings):
        async for chunk in text_iter:
            captured_text_chunks.append(chunk)
            yield chunk

    monkeypatch.setattr(
        lka.Agent,
        "default",
        SimpleNamespace(tts_node=fake_tts_node),
        raising=False,
    )

    async def text_stream():
        # User-provided conversation sample around tool call leakage.
        yield "I'm sorry, I didn't quite catch that. Could you please repeat it. "
        yield (
            'I am not familiar with Sure Shot P Y Q W. We do have previous year '
            "question papers and test series available. "
        )
        yield "tool_code\nprint(default_api.get_"
        yield (
            'docs(kb_name = "Vajiram Knowledge base", query = "previous year '
            'question papers and test series"))'
        )
        yield " या टेल मी अबाउट दैट। क्या बात है? "
        yield "अब इसको क्या हो गया यार, ये चलते चलते क्या मौत पड़ गई।"

    async for _ in agent.tts_node(text_stream(), model_settings=None):
        pass

    combined = "".join(captured_text_chunks)
    normalized = " ".join(combined.split())

    assert "tool_code" not in normalized
    assert "default_api.get_docs" not in normalized
    assert "kb_name" not in normalized
    assert "Could you please repeat it." in normalized
    assert "previous year question papers and test series available." in normalized
    assert "क्या बात है?" in normalized
    assert "अब इसको क्या हो गया यार" in normalized


@pytest.mark.benchmark
def test_strip_non_speakable_latency_budget() -> None:
    lka = _load_lite_agent_module()

    sample = (
        "I'm sorry, I didn't quite catch that. "
        "tool_code\n"
        'print(default_api.get_docs(kb_name = "Vajiram Knowledge base", '
        'query = "previous year question papers and test series")) '
        "We do have previous year question papers and test series available. "
        "या टेल मी अबाउट दैट। क्या बात है?"
    )

    iterations = 2000
    start = perf_counter()
    cleaned = ""
    for _ in range(iterations):
        cleaned = lka.LiveKitLiteAgent._strip_non_speakable(sample)
    elapsed_ms = (perf_counter() - start) * 1000
    avg_ms = elapsed_ms / iterations
    print(f"[LATENCY] _strip_non_speakable avg_ms={avg_ms:.6f} over {iterations} iterations")

    assert "tool_code" not in cleaned
    assert "default_api.get_docs" not in cleaned
    # Keep a conservative budget to avoid flaky CI while still catching regressions.
    assert avg_ms < 3.0

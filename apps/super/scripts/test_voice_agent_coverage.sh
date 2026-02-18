#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

export PYTEST_DISABLE_PLUGIN_AUTOLOAD="${PYTEST_DISABLE_PLUGIN_AUTOLOAD:-1}"
export PYDANTIC_DISABLE_PLUGINS="${PYDANTIC_DISABLE_PLUGINS:-__all__}"
export PYTHONPATH="$ROOT_DIR"

PYTHON_BIN="python"
if [[ -x "$ROOT_DIR/venv/bin/python" ]]; then
  PYTHON_BIN="$ROOT_DIR/venv/bin/python"
else
  MAIN_WORKTREE="$(git worktree list --porcelain | awk '/^worktree / {print $2; exit}')"
  if [[ -n "$MAIN_WORKTREE" && -x "$MAIN_WORKTREE/venv/bin/python" ]]; then
    PYTHON_BIN="$MAIN_WORKTREE/venv/bin/python"
  fi
fi

VOICE_AGENT_TESTS=(
  "tests/core/voice/common/test_pilot.py"
  "tests/core/voice/services/test_service_common.py"
  "tests/core/voice/test_livekit_startup_timing.py"
  "tests/core/voice/test_voice_agent_handler_startup.py"
  "tests/core/voice/test_config_resolution_latency.py"
  "tests/core/voice/test_startup_background_tasks.py"
  "tests/core/voice/livekit/test_lite_handler_connect_guard.py"
  "tests/core/voice/test_startup_latency_regression.py"
  "tests/core/voice/livekit/test_harness_fakes.py"
  "tests/core/voice/test_voice_agent_handler_service_cache.py"
  "tests/core/voice/test_voice_agent_handler_config_resolution.py"
  "tests/core/voice/test_voice_agent_handler_recording_publish.py"
  "tests/core/voice/livekit/test_lite_handler_parsing_response.py"
  "tests/core/voice/livekit/test_lite_handler_session_flow.py"
  "tests/core/voice/livekit/test_lite_handler_idle_goodbye.py"
  "tests/core/voice/managers/test_knowledge_base_manager.py"
  "tests/core/voice/livekit/test_livekit_lite_agent_context.py"
  "tests/core/voice/livekit/test_livekit_lite_agent_tools.py"
  "tests/core/voice/test_chroma_fetch_k.py"
  "tests/core/voice/test_kb_chroma_kn_base_integration.py"
  "tests/test_kb_search_quality.py"
  "tests/core/voice/test_voice_agent_suite_manifest.py"
  # Eval suite — retrieval metrics + structural flow validation (no API key needed)
  "tests/eval/test_retrieval_eval.py"
  "tests/eval/test_conversation_flow.py"
)

COVERAGE_TARGETS=(
  "super/core/voice/voice_agent_handler.py"
  "super/core/voice/livekit/lite_handler.py"
  "super/core/voice/livekit/livekit_lite_agent.py"
  "super/core/voice/managers/knowledge_base.py"
  "super/core/memory/index/chroma.py"
  "super/core/memory/search/reranker.py"
)

echo "[coverage] Voice agent tests (${#VOICE_AGENT_TESTS[@]} files)" >&2
echo "[coverage] Python binary: $PYTHON_BIN" >&2
echo "[coverage] Coverage targets:" >&2
for target in "${COVERAGE_TARGETS[@]}"; do
  echo "  - $target" >&2
done

if [[ "${ENABLE_PYTEST_COV:-0}" == "1" ]] && "$PYTHON_BIN" -c "import pytest_cov" >/dev/null 2>&1; then
  echo "[coverage] Running pytest-cov mode (opt-in)." >&2
  ./scripts/test_voice_agent_suite.sh \
    -p pytest_cov \
    --cov=super.core.voice.voice_agent_handler \
    --cov=super.core.voice.livekit.lite_handler \
    --cov=super.core.voice.livekit.livekit_lite_agent \
    --cov=super.core.voice.managers.knowledge_base \
    --cov=super.core.memory.index.chroma \
    --cov-report=term-missing \
    --cov-fail-under="${COV_FAIL_UNDER:-20}" \
    "$@"
  exit 0
fi

echo "[coverage] Running stable coverage mode via coverage.py. Set ENABLE_PYTEST_COV=1 to force pytest-cov mode." >&2
"$PYTHON_BIN" -m coverage erase
"$PYTHON_BIN" -m coverage run \
  -m pytest -ra -p pytest_asyncio.plugin "${VOICE_AGENT_TESTS[@]}" "$@"

"$PYTHON_BIN" -m coverage report -m \
  --fail-under="${COV_FAIL_UNDER:-20}" \
  "${COVERAGE_TARGETS[@]}"

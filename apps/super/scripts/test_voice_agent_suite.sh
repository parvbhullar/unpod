#!/usr/bin/env bash
set -euo pipefail

SCRIPT_PATH="${BASH_SOURCE[0]:-$0}"
ROOT_DIR="$(cd "$(dirname "$SCRIPT_PATH")/.." && pwd)"
cd "$ROOT_DIR"

# Keep local runs deterministic in environments with noisy global plugins.
export PYTEST_DISABLE_PLUGIN_AUTOLOAD="${PYTEST_DISABLE_PLUGIN_AUTOLOAD:-1}"
export PYDANTIC_DISABLE_PLUGINS="${PYDANTIC_DISABLE_PLUGINS:-__all__}"
export PYTHONPATH="$ROOT_DIR"

PYTEST_BIN="pytest"
PYTHON_BIN="python"
if [[ -x "$ROOT_DIR/.venv/bin/pytest" ]]; then
  PYTEST_BIN="$ROOT_DIR/.venv/bin/pytest"
  PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
elif [[ -x "$ROOT_DIR/venv/bin/pytest" ]]; then
  PYTEST_BIN="$ROOT_DIR/venv/bin/pytest"
  PYTHON_BIN="$ROOT_DIR/venv/bin/python"
else
  MAIN_WORKTREE="$(git worktree list --porcelain | awk '/^worktree / {print $2; exit}')"
  if [[ -n "$MAIN_WORKTREE" && -x "$MAIN_WORKTREE/.venv/bin/pytest" ]]; then
    PYTEST_BIN="$MAIN_WORKTREE/.venv/bin/pytest"
    PYTHON_BIN="$MAIN_WORKTREE/.venv/bin/python"
  elif [[ -n "$MAIN_WORKTREE" && -x "$MAIN_WORKTREE/venv/bin/pytest" ]]; then
    PYTEST_BIN="$MAIN_WORKTREE/venv/bin/pytest"
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
  "tests/core/voice/livekit/test_lite_handler_cleanup.py"
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

EMBEDDING_OPTIONAL_TESTS=(
  "tests/core/voice/test_chroma_fetch_k.py"
  "tests/core/voice/test_kb_chroma_kn_base_integration.py"
  "tests/test_kb_search_quality.py"
  "tests/eval/test_retrieval_eval.py"
)

DB_OPTIONAL_TESTS=(
  "tests/core/voice/common/test_pilot.py"
  "tests/core/voice/test_voice_agent_handler_service_cache.py"
  "tests/core/voice/test_voice_agent_handler_config_resolution.py"
  "tests/core/voice/test_voice_agent_handler_recording_publish.py"
  "tests/core/voice/livekit/test_lite_handler_parsing_response.py"
  "tests/core/voice/livekit/test_lite_handler_session_flow.py"
  "tests/core/voice/livekit/test_lite_handler_idle_goodbye.py"
  "tests/core/voice/managers/test_knowledge_base_manager.py"
  "tests/core/voice/livekit/test_livekit_lite_agent_context.py"
  "tests/core/voice/livekit/test_livekit_lite_agent_tools.py"
)

NETWORK_OPTIONAL_TESTS=(
  "tests/eval/test_conversation_flow.py"
)

filter_out_tests() {
  local -a skip_list=("$@")
  FILTERED_TESTS=()
  for test_file in "${VOICE_AGENT_TESTS[@]}"; do
    SHOULD_SKIP=0
    for skipped in "${skip_list[@]}"; do
      if [[ "$test_file" == "$skipped" ]]; then
        SHOULD_SKIP=1
        break
      fi
    done
    if [[ "$SHOULD_SKIP" -eq 0 ]]; then
      FILTERED_TESTS+=("$test_file")
    fi
  done
  VOICE_AGENT_TESTS=("${FILTERED_TESTS[@]}")
}

announce_skips() {
  local reason="$1"
  shift
  local -a files=("$@")
  echo "[suite] $reason"
  for skipped in "${files[@]}"; do
    echo "  - $skipped"
  done
}

if ! "$PYTHON_BIN" -c "import sentence_transformers" >/dev/null 2>&1; then
  announce_skips \
    "sentence_transformers not installed; skipping embedding-heavy tests:" \
    "${EMBEDDING_OPTIONAL_TESTS[@]}"
  filter_out_tests "${EMBEDDING_OPTIONAL_TESTS[@]}"
fi

if [[ "${VOICE_SUITE_WITH_DB:-0}" != "1" ]]; then
  announce_skips \
    "VOICE_SUITE_WITH_DB!=1; skipping DB-dependent tests:" \
    "${DB_OPTIONAL_TESTS[@]}"
  filter_out_tests "${DB_OPTIONAL_TESTS[@]}"
fi

if [[ "${VOICE_SUITE_ALLOW_NETWORK:-0}" != "1" ]]; then
  announce_skips \
    "VOICE_SUITE_ALLOW_NETWORK!=1; skipping network-dependent tests:" \
    "${NETWORK_OPTIONAL_TESTS[@]}"
  filter_out_tests "${NETWORK_OPTIONAL_TESTS[@]}"
fi

VOICE_AGENT_MODULES=(
  "super.core.voice.voice_agent_handler"
  "super.core.voice.livekit.lite_handler"
  "super.core.voice.livekit.livekit_lite_agent"
  "super.core.voice.managers.knowledge_base"
  "super.core.memory.index.chroma"
  "super.core.memory.search.reranker"
)

COVERAGE_TARGETS=(
  "super/core/voice/voice_agent_handler.py"
  "super/core/voice/livekit/lite_handler.py"
  "super/core/voice/livekit/livekit_lite_agent.py"
  "super/core/voice/managers/knowledge_base.py"
  "super/core/memory/index/chroma.py"
)

echo "[suite] Voice agent tests (${#VOICE_AGENT_TESTS[@]} files)"
echo "[suite] Pytest binary: $PYTEST_BIN"
echo "[suite] Modules under test:"
for module in "${VOICE_AGENT_MODULES[@]}"; do
  echo "  - $module"
done
echo "[suite] Test files:"
for test_file in "${VOICE_AGENT_TESTS[@]}"; do
  echo "  - $test_file"
done

if [[ "${VOICE_SUITE_WITH_COVERAGE:-0}" == "1" ]]; then
  if ! "$PYTHON_BIN" -c "import coverage" >/dev/null 2>&1; then
    echo "[suite] Coverage requested but 'coverage' is not installed in $PYTHON_BIN." >&2
    exit 1
  fi

  echo "[suite] Coverage mode enabled (minimum total: ${COV_FAIL_UNDER:-20}%)."
  "$PYTHON_BIN" -m coverage erase
  "$PYTHON_BIN" -m coverage run \
    -m pytest -ra -p pytest_asyncio.plugin "${VOICE_AGENT_TESTS[@]}" "$@"

  echo "[suite] Coverage targets:"
  for target in "${COVERAGE_TARGETS[@]}"; do
    echo "  - $target"
  done

  "$PYTHON_BIN" -m coverage report -m \
    --fail-under="${COV_FAIL_UNDER:-20}" \
    "${COVERAGE_TARGETS[@]}"
  exit 0
fi

echo "[suite] Running without coverage. Set VOICE_SUITE_WITH_COVERAGE=1 for an overall coverage report."
"$PYTEST_BIN" -ra -p pytest_asyncio.plugin "${VOICE_AGENT_TESTS[@]}" "$@"

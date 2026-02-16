#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Keep local runs deterministic in environments with noisy global plugins.
export PYTEST_DISABLE_PLUGIN_AUTOLOAD="${PYTEST_DISABLE_PLUGIN_AUTOLOAD:-1}"
export PYDANTIC_DISABLE_PLUGINS="${PYDANTIC_DISABLE_PLUGINS:-__all__}"
export PYTHONPATH="$ROOT_DIR"

PYTEST_BIN="pytest"
if [[ -x "$ROOT_DIR/venv/bin/pytest" ]]; then
  PYTEST_BIN="$ROOT_DIR/venv/bin/pytest"
else
  MAIN_WORKTREE="$(git worktree list --porcelain | awk '/^worktree / {print $2; exit}')"
  if [[ -n "$MAIN_WORKTREE" && -x "$MAIN_WORKTREE/venv/bin/pytest" ]]; then
    PYTEST_BIN="$MAIN_WORKTREE/venv/bin/pytest"
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
  "tests/core/voice/livekit/test_livekit_lite_agent_context.py"
  "tests/core/voice/livekit/test_livekit_lite_agent_tools.py"
  "tests/core/voice/test_voice_agent_suite_manifest.py"
)

"$PYTEST_BIN" -q -p pytest_asyncio.plugin "${VOICE_AGENT_TESTS[@]}" "$@"

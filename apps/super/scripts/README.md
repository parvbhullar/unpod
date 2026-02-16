# Voice Agent Test Suite

This folder contains one-command scripts to run the voice-agent-focused tests.

## Prerequisites

- Python environment with project deps installed
- `pytest` installed in the same environment
- Optional for opt-in mode: `pytest-cov`

The scripts auto-resolve Python/pytest from:
1. `./venv` in the current worktree
2. the main worktree `venv` (if present)

## Commands

Run the suite:

```bash
bash scripts/test_voice_agent_suite.sh
```

Run suite + coverage (stable default):

```bash
bash scripts/test_voice_agent_coverage.sh
```

Run coverage with custom minimum threshold:

```bash
COV_FAIL_UNDER=25 bash scripts/test_voice_agent_coverage.sh
```

Try `pytest-cov` mode explicitly (optional):

```bash
ENABLE_PYTEST_COV=1 COV_FAIL_UNDER=25 bash scripts/test_voice_agent_coverage.sh
```

## Passing pytest filters

Both scripts forward extra args to pytest, so you can use filters like:

```bash
bash scripts/test_voice_agent_suite.sh -k startup
bash scripts/test_voice_agent_coverage.sh -k "session_flow or idle"
```

## What gets covered

Coverage reports are scoped to:

- `super/core/voice/voice_agent_handler.py`
- `super/core/voice/livekit/lite_handler.py`
- `super/core/voice/livekit/livekit_lite_agent.py`

## Known local behavior

- One skip can be expected on some setups:
  - `tests/core/voice/services/test_service_common.py:65`
  - Reason: LiveKit `api` import shadowing by `tests/core/voice/livekit/__init__.py`
- If you see `ImportError: cannot load module more than once per process` in opt-in mode, switch back to default stable coverage mode (without `ENABLE_PYTEST_COV=1`).

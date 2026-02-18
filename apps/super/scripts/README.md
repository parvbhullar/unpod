# Voice Agent Test Suite

This folder contains one-command scripts to run the voice-agent-focused tests.

## Prerequisites

- Python environment with project deps installed
- `pytest` installed in the same environment
- Optional for opt-in mode: `pytest-cov`
- Optional for LLM-judged eval: `OPENAI_API_KEY` env var

The scripts auto-resolve Python/pytest from:
1. `./venv` in the current worktree
2. the main worktree `venv` (if present)

## Commands

Run the suite:

```bash
bash scripts/test_voice_agent_suite.sh
```

Run the suite with inline overall coverage summary:

```bash
VOICE_SUITE_WITH_COVERAGE=1 bash scripts/test_voice_agent_suite.sh
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

Run remote KN_BASE Chroma Q&A integration checks (prints question + returned docs):

```bash
RUN_KB_REMOTE_E2E=1 SEARCH_SERVICE_URL=http://<search-service> \
  bash scripts/test_voice_agent_suite.sh -k "kb_chroma_kn_base_integration"
```

## Evaluation Suite

The eval tests in `tests/eval/` provide quality metrics beyond pass/fail:

### Retrieval metrics (no API key needed)

```bash
pytest tests/eval/test_retrieval_eval.py -v
```

Measures MRR, Hit Rate@5, Precision@1, NDCG@5 over 9 ground-truth Q&A pairs.

### Conversation flow validation (no API key needed)

```bash
pytest tests/eval/test_conversation_flow.py -v -k "not E2E"
```

Validates structural integrity of multi-turn conversation patterns:
- Flows start with greetings (no tool call)
- Tool names are valid
- `end_call` is terminal
- All 6 intent types covered across flows

### Intent classification eval (requires `OPENAI_API_KEY`)

```bash
pytest tests/eval/test_intent_eval.py -v -m ragas -s
```

Sends 30 user messages to gpt-4o-mini, compares predicted tool calls against
ground truth. Reports overall accuracy, per-intent precision/recall, and
confusion matrix. Threshold: 90% overall accuracy.

**Covered intents (6):**

| Intent | Tool | Cases |
|--------|------|-------|
| Greet | none | 3 |
| KB query | `get_docs` | 12 |
| Record info | `record_user_info` | 4 |
| Callback | `create_followup_or_callback` | 3 |
| Handover | `handover_tool` | 4 |
| End call | `end_call` | 4 |

### E2E conversation flow eval (requires `OPENAI_API_KEY`)

```bash
pytest tests/eval/test_conversation_flow.py -v -m ragas -s
```

Runs 4 multi-turn conversation flows through the LLM classifier and validates
tool predictions at each turn. Covers full lifecycle patterns from the
production Q&A data.

### RAGAS LLM-judged quality (requires `OPENAI_API_KEY`)

```bash
pytest tests/eval/test_ragas_eval.py -v -m ragas -s
```

Measures context_precision, context_recall, faithfulness, and answer_relevancy
using RAGAS 0.3.x with gpt-4o-mini as judge. Evaluates both the 9 core KB
questions and 12 KB questions from the intent eval dataset.

### Run all eval tests together

```bash
# Structural only (fast, no API key)
pytest tests/eval/ -v -k "not E2E" --ignore=tests/eval/test_ragas_eval.py --ignore=tests/eval/test_intent_eval.py

# Full eval (needs OPENAI_API_KEY)
pytest tests/eval/ -v -m ragas -s
```

## What gets covered

Coverage reports are scoped to:

- `super/core/voice/voice_agent_handler.py`
- `super/core/voice/livekit/lite_handler.py`
- `super/core/voice/livekit/livekit_lite_agent.py`
- `super/core/voice/managers/knowledge_base.py`
- `super/core/memory/index/chroma.py`
- `super/core/memory/search/reranker.py`

## Known local behavior

- One skip can be expected on some setups:
  - `tests/core/voice/services/test_service_common.py:65`
  - Reason: LiveKit `api` import shadowing by `tests/core/voice/livekit/__init__.py`
- If you see `ImportError: cannot load module more than once per process` in opt-in mode, switch back to default stable coverage mode (without `ENABLE_PYTEST_COV=1`).

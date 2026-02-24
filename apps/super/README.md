# Super — Voice AI Framework

Multi-role voice AI agents powered by LiveKit, Pipecat, LangChain, and LangGraph.

## Prerequisites

- Python 3.10+ (3.12 recommended)
- [uv](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- LiveKit server (cloud or self-hosted)
- MongoDB (conversation storage)
- PostgreSQL (agent config)
- Redis (optional — set `USE_REDIS=false` to disable caching)

## Quick Start

```bash
# 1. Set up local environment (installs deps, creates .env)
make setup

# 2. Edit .env with your API keys (see Environment Variables below)

# 3. Run the voice executor
make local          # Local dev mode
make run            # Docker
```

### Manual Setup

```bash
uv sync
cp .env.example .env
# Edit .env with your keys

# Voice executor (general agent)
uv run python super_services/orchestration/executors/voice_executor_v3.py dev

# SuperKik executor (assistant agent)
uv run python super_services/orchestration/executors/superkik_executor_v1.py dev
```

## Available Commands

```
$ make help
  build           Build Docker image
  run             Build + run Docker container
  setup           Set up local dev environment (venv + .env)
  local           Run locally in dev mode
  validate        Check required env vars
  health          Check service connectivity
  test            Run unit tests
  k8s-qa          Deploy to K8s QA
  k8s-prod        Deploy to K8s Prod
  help            Show this help
```

## Project Structure

```
super/                  # Core AI framework (workspace package)
├── core/
│   ├── voice/          # VoiceAgentHandler, SuperkikAgentHandler
│   ├── callback/       # BaseCallback
│   ├── context/        # Message, Event schemas
│   └── configuration/  # BaseModelConfig
super_services/         # Infrastructure services (workspace package)
├── orchestration/
│   └── executors/      # Entry points (voice_executor_v3, superkik_executor_v1)
├── voice/              # Voice models, workflows, analysis
├── db/                 # PostgreSQL queries, conversation blocks
├── libs/               # Shared utils (redis, postgres, logger, S3)
└── settings/           # Environment-specific settings
super_os/               # Self-contained voice extraction from super/
superkik/               # SuperKik app (independent)
deployment/             # Docker, K8s manifests, production compose
tests/                  # Unit tests and evals
pyproject.toml          # uv workspace root
Dockerfile              # Multi-stage production build
Makefile                # Common commands
deploy.sh               # Deployment script
```

## Environment Variables

### Required

These 5 vars are checked by `make validate`. The voice executor will not start without them.

| Variable | Description |
|----------|-------------|
| `LIVEKIT_URL` | LiveKit server URL (wss://...) |
| `LIVEKIT_API_KEY` | LiveKit API key |
| `LIVEKIT_API_SECRET` | LiveKit API secret |
| `OPENAI_API_KEY` | OpenAI API key |
| `DEEPGRAM_API_KEY` | Deepgram STT key |

### Recommended

The agent works without these but functionality is reduced.

| Variable | Description |
|----------|-------------|
| `SETTINGS_FILE` | Settings module (default: `super_services.settings.qa`) |
| `ANTHROPIC_API_KEY` | Anthropic API key (fallback LLM) |
| `CARTESIA_API_KEY` | Cartesia TTS key |
| `MONGO_DSN` | MongoDB connection string (conversation storage) |
| `REDIS_URI` | Redis connection URI (caching) |
| `SIP_OUTBOUND_TRUNK_ID` | LiveKit SIP trunk ID (outbound calls, must start with `ST_`) |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `ENV` | from `SETTINGS_FILE` | Environment name (`qa`, `prod`) |
| `AGENT_NAME` | `unpod-{env}-general-agent-v3` | Agent handle in DB |
| `WORKER_HANDLER` | `livekit` | Voice handler (`livekit` or `pipecat`) |
| `USE_REDIS` | `true` | Enable Redis config caching |
| `ELEVEN_API_KEY` | — | ElevenLabs TTS key |
| `GROQ_API_KEY` | — | Groq LLM key |
| `EXA_API_KEY` | — | Exa search API key |
| `TAVILY_API_KEY` | — | Tavily search API key |

## Deployment

See [deployment/README.md](deployment/README.md) for Docker, Kubernetes, and production deployment.

```bash
make build          # Build Docker image
make run            # Build + run container
make k8s-qa         # Deploy to K8s QA
make k8s-prod       # Deploy to K8s Prod
./deploy.sh --help  # All deployment options
```

## Prefect (Task Orchestration)

Prefect manages async workflows (post-call analysis, follow-ups, etc.). Each environment needs a Prefect server and a call worker.

### Local

```bash
# Start Prefect server + PostgreSQL
docker compose -f super_services/prefect_setup/local/docker-compose-local-base.yaml down --remove-orphans
docker compose -f super_services/prefect_setup/local/docker-compose-local-base.yaml up -d

# Start call worker
docker compose -f super_services/prefect_setup/local/docker-call-worker-compose.yaml down --remove-orphans
docker compose -f super_services/prefect_setup/local/docker-call-worker-compose.yaml up -d

# Create / refresh deployments
uv run python super_services/orchestration/task/deployments/task_deployments.py
```

### QA

```bash
docker compose -f super_services/prefect_setup/qa/docker-compose-qa.yaml down --remove-orphans
docker compose -f super_services/prefect_setup/qa/docker-compose-qa.yaml up -d

docker compose -f super_services/prefect_setup/qa/docker-call-worker-compose.yaml down --remove-orphans
docker compose -f super_services/prefect_setup/qa/docker-call-worker-compose.yaml up -d

uv run python super_services/orchestration/task/deployments/task_deployments.py
```

### Prod

```bash
docker compose -f super_services/prefect_setup/prod/docker-prefect-sever-compose.yaml down --remove-orphans
docker compose -f super_services/prefect_setup/prod/docker-prefect-sever-compose.yaml up -d

docker compose -f super_services/prefect_setup/prod/docker-call-worker-compose.yaml down --remove-orphans
docker compose -f super_services/prefect_setup/prod/docker-call-worker-compose.yaml up -d

uv run python super_services/orchestration/task/deployments/task_deployments.py
```

> To refresh deployments after code changes, re-run the `task_deployments.py` script. No restart of Prefect server or workers needed.

## Testing

```bash
make test
# or
uv run pytest
```

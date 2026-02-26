# Super — Voice AI Framework

Multi-role voice AI agents powered by LiveKit, Pipecat, LangChain, and LangGraph.

## Prerequisites

- Python 3.10+ (3.12 recommended)
- [uv](https://docs.astral.sh/uv/) (auto-installed by `make setup` if missing)
- LiveKit server (cloud or self-hosted)
- MongoDB (conversation storage)
- PostgreSQL (agent config)
- Redis (optional — set `USE_REDIS=false` to disable caching)

## Quick Start

```bash
# 1. Install deps + configure .env (will prompt for API keys)
make setup

# 2. Run the voice executor
make local          # Local dev mode
make run            # Docker
```

`make setup` will auto-install `uv` if missing, sync Python dependencies,
then interactively prompt for required API keys (LiveKit, OpenAI, Deepgram)
and optional ones (Anthropic, Cartesia, MongoDB, Redis). Values are saved
to `.env`. Existing values are shown as defaults — press Enter to keep them.

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
  setup           Install deps + configure .env (interactive)
  local           Run locally in dev mode
  validate        Check required env vars
  health          Check service connectivity
  test            Run voice agent test suite
  deploy-service  Deploy systemd service (run make setup first)
  prefect-up      Start Prefect server + worker (local)
  prefect-down    Stop Prefect server + worker (local)
  prefect-deploy  Register Prefect flow deployments
  prefect-refresh Sync deps + rebuild task image + re-register
  prefect-remote  Start Prefect for qa/prod (ENV=qa|prod)
  k8s-qa          Deploy all to K8s QA (executor + Prefect)
  k8s-prod        Deploy all to K8s Prod (executor + Prefect)
  k8s-prefect-qa  Deploy only Prefect to K8s QA
  k8s-prefect-prod Deploy only Prefect to K8s Prod
  cerebrium-setup Setup + deploy to Cerebrium (interactive)
  cerebrium-deploy Deploy to Cerebrium (skip login/secrets)
  cerebrium-logs  View Cerebrium deployment logs
  cerebrium-status Check Cerebrium deployment status
  modal-setup     Install Modal CLI + authenticate
  modal-deploy    Deploy voice executor to Modal
  modal-dev       Run Modal in dev mode (live reload)
  modal-logs      View Modal deployment logs
  modal-stop      Stop Modal deployment
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

See [deployment/README.md](deployment/README.md) for full details on all deployment methods.

### Docker

```bash
make build          # Build Docker image
make run            # Build + run container
./deploy.sh docker build
./deploy.sh docker run
```

### Systemd (Linux VM)

Deploy directly on an Ubuntu/Debian box as a systemd service:

```bash
# Step 1: Install deps + configure .env (interactive prompts for API keys)
make setup

# Step 2: Deploy the systemd service
make deploy-service

# Manage the service
sudo systemctl status voice_lk_executor_v3
sudo systemctl restart voice_lk_executor_v3
sudo journalctl -u voice_lk_executor_v3 -f
```

### Kubernetes

```bash
make k8s-qa         # Deploy everything (executor + Prefect) to K8s QA
make k8s-prod       # Deploy everything to K8s Prod

# Deploy only Prefect to K8s (server + worker + HPA)
make k8s-prefect-qa
make k8s-prefect-prod
```

K8s Prefect uses a `kubernetes` work pool type (`call-work-pool-k8s`) which spawns
K8s Jobs for each flow run, enabling horizontal scaling via HPA.

### Cerebrium (Managed Cloud)

```bash
# Interactive: login → upload secrets → review → deploy
make cerebrium-setup

# If already set up, deploy directly
make cerebrium-deploy

# Monitor
make cerebrium-logs
make cerebrium-status
```

See [deployment/README.md](deployment/README.md#cerebrium) for full details.

### Modal (Serverless)

```bash
# One-time: install CLI + authenticate
make modal-setup

# Deploy to production
make modal-deploy

# Dev mode with live reload
make modal-dev

# Monitor / stop
make modal-logs
make modal-stop
```

See [deployment/README.md](deployment/README.md#modal) for secrets setup and configuration.

## Prefect (Task Orchestration)

Prefect manages async workflows (post-call analysis, follow-ups, etc.). Each environment needs a Prefect server and a call worker.

### Local

```bash
make prefect-up       # Start Prefect server + worker
make prefect-deploy   # Register flow deployments
make prefect-down     # Stop everything
```

Prefect UI: http://localhost:4200

After code or dependency changes:

```bash
make prefect-refresh  # Sync deps + rebuild task image + re-register
```

### QA / Prod

```bash
make prefect-remote ENV=qa    # Start server + worker + register deployments
make prefect-remote ENV=prod
```

> To refresh deployments after code changes, re-run the `task_deployments.py` script. No restart of Prefect server or workers needed.

## Testing

```bash
make test
# or
uv run pytest
```

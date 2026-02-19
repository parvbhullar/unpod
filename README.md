<!--
Unpod — Open-source AI voice agent platform
https://unpod.ai | https://docs.unpod.dev
-->

<div align="center">

# Unpod

### Open-source AI Native Communication Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Docs](https://img.shields.io/badge/docs-unpod.dev-blue)](https://docs.unpod.dev)
[![Website](https://img.shields.io/badge/website-unpod.ai-purple)](https://unpod.ai)

[Documentation](https://docs.unpod.dev) | [Website](https://unpod.ai) | [Contributing](#contributing)

</div>

---

Unpod is an open-source communication platform for creating AI  agents with dedicated phone numbers. Build agents that handle incoming calls and messages, filter communications intelligently, and deliver actionable insights — all while integrating with your existing business tools.

## Features

- **AI Voice Agents** — Build conversational voice agents powered by LLMs with customizable personality, knowledge, and tools
- **Multi-Channel** — Voice calls, WhatsApp, and email through a unified agent interface
- **Real-Time Voice Pipeline** — Sub-second latency using LiveKit, Pipecat, and streaming TTS/STT
- **Agent Studio** — Visual no-code builder for configuring agent behavior, prompts, and workflows
- **Knowledge Base** — Upload documents and data sources for RAG-powered agent responses
- **Multi-Tenant Workspaces** — Organizations, teams, RBAC, and shared spaces
- **Telephony Integration** — Dedicated phone numbers with SIP trunking and call routing
- **Call Analytics** — Real-time dashboards, conversation logs, and performance metrics
- **Workflow Automation** — Trigger actions (scheduling, CRM updates, notifications) from conversations
- **Desktop App** — Native cross-platform desktop client built with Tauri

## Quick Start

### Prerequisites

- **Node.js** 20+ / npm 10+
- **Python** 3.11+ (3.10+ for `apps/super`)
- **Docker** & Docker Compose
- **[uv](https://docs.astral.sh/uv/)** (only for `apps/super`)

### One-Command Setup

```bash
make quick-start    # Install deps, start Docker, run migrations
make dev            # Start frontend (port 3000) + backend (port 8000)
```

### Docker-Only (No Local Dependencies)

```bash
docker compose -f docker-compose.simple.yml up -d --build
```

Starts everything in containers with working defaults. Default admin: `admin@unpod.dev` / `admin123`.

### Manual Setup

```bash
# Install Node.js dependencies
npm install

# Create Python venv for backend
python3 -m venv apps/backend-core/.venv
source apps/backend-core/.venv/bin/activate
pip install -r apps/backend-core/requirements/local.txt

# Start infrastructure (PostgreSQL, MongoDB, Redis, Centrifugo)
docker compose -f docker-compose.simple.yml up -d postgres mongodb redis centrifugo

# Run migrations and start dev servers
cd apps/backend-core && python manage.py migrate --no-input && cd ../..
npm run dev
```

### Access Points

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000/api/v1/ |
| Admin Panel | http://localhost:8000/unpod-admin/ |
| API Services | http://localhost:9116/docs |
| Centrifugo | http://localhost:8100 |

---

## Architecture

Unpod is an NX monorepo with four main applications and a shared library layer:

```
unpod/
├── apps/
│   ├── web/              # Next.js 16 frontend (React 19)
│   ├── backend-core/     # Django 5 REST API
│   ├── api-services/     # FastAPI microservices
│   ├── super/            # Voice AI engine (LiveKit + Pipecat)
│   └── unpod-tauri/      # Desktop app (Tauri 2)
├── libs/
│   └── nextjs/           # Shared React libraries (@unpod/*)
├── infrastructure/
│   └── docker/           # Dockerfiles & service configs
└── scripts/              # Setup, migration, and utility scripts
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16 / React 19 / styled-components / Ant Design |
| Monorepo | NX 22 |
| Desktop | Tauri 2 |
| Backend | Django 5 + DRF / FastAPI |
| Voice AI | LiveKit + Pipecat + LangChain |
| Databases | PostgreSQL 16, MongoDB 7, Redis 7 |
| Messaging | Kafka (KRaft), Centrifugo v5 |

---

## Apps

### Web — `apps/web/`

Next.js 16 frontend with App Router, group-based layouts, styled-components, and Ant Design.

```bash
npx nx dev web              # Dev server at port 3000
npx nx build web            # Production build
npx nx e2e web              # Playwright E2E tests
```

Environment: copy `apps/web/.env.local.example` to `apps/web/.env.local`.

<details>
<summary>Key routes</summary>

| Area | Routes |
|------|--------|
| Auth | `/auth/signin`, `/auth/signup`, `/auth/forgot-password`, `/auth/reset-password` |
| Onboarding | `/create-org`, `/join-org`, `/verify-invite`, `/ai-identity`, `/business-identity` |
| Dashboard | `/dashboard` |
| AI Studio | `/ai-studio`, `/ai-studio/new`, `/ai-studio/[pilotSlug]` |
| Agent Studio | `/agent-studio/[spaceSlug]`, `/configure-agent/[spaceSlug]` |
| Spaces | `/spaces`, `/spaces/[spaceSlug]/chat`, `/spaces/[spaceSlug]/call`, `/spaces/[spaceSlug]/doc` |
| Knowledge | `/knowledge-bases`, `/knowledge-bases/[kbSlug]` |
| Settings | `/profile`, `/settings`, `/org/settings`, `/api-keys` |

</details>

**Desktop app** (Tauri): `npm run desktop:dev` / `npm run desktop:build`

### Backend Core — `apps/backend-core/`

Django 5 REST API with JWT auth, multi-tenant organizations, RBAC, and background tasks.

```bash
cd apps/backend-core
source .venv/bin/activate
python manage.py runserver        # API at port 8000
pytest                            # Run tests
```

<details>
<summary>Management commands</summary>

```bash
python manage.py migrate                # Run migrations
python manage.py createsuperuser        # Create admin user
python manage.py create_default_user    # Create default test user
python manage.py seed_reference_data    # Seed initial data
python manage.py setup_schedules        # Setup scheduled tasks
python manage.py update_pilot           # Update AI pilot configs
python manage.py update_voice_profile   # Update voice profiles
python manage.py update_models          # Update AI model configs
python manage.py process_calls          # Process call logs
```

</details>

<details>
<summary>API endpoints (all under /api/v1/)</summary>

| Prefix | Description |
|--------|-------------|
| `auth/` | JWT authentication & registration |
| `password/` | Password reset flow |
| `organization/` | Organization management |
| `spaces/` | Workspace management |
| `threads/` | Conversation threads |
| `roles/` | RBAC roles & permissions |
| `knowledge_base/` | Knowledge base & documents |
| `documents/` | File management |
| `metrics/` | Analytics & call logs |
| `core/pilots/` | AI voice agent profiles |
| `core/providers/` | LLM/voice provider listing |
| `core/voice/` | LiveKit room tokens |
| `core/voice-profiles/` | Voice profile management |
| `media/upload/` | File upload |

</details>

### API Services — `apps/api-services/`

FastAPI microservices for messaging, document store, AI search, and task management. MongoDB primary storage.

```bash
cd apps/api-services
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 9116 --reload
```

Interactive docs at http://localhost:9116/docs.

| Route | Service | Description |
|-------|---------|-------------|
| `/api/v1/store` | store_service | Document store & indexing |
| `/api/v1/connector` | store_service | Data connectors |
| `/api/v1/voice` | store_service | LiveKit voice/video |
| `/api/v1/search` | search_service | AI-powered search |
| `/api/v1/conversation` | messaging_service | Chat conversations |
| `/api/v1/agent` | messaging_service | Agent management |
| `/api/v1/task` | task_service | Task management |

WebSocket: `ws://localhost:9116/ws/v1/conversation/{thread_id}/`

### Voice AI — `apps/super/`

Voice AI engine built on LiveKit and Pipecat. Orchestrates real-time voice agents with LLM providers, TTS/STT engines, and workflow automation via Prefect.

```bash
cd apps/super

# Install (uv recommended)
uv pip install -r requirements/super.txt -r requirements/super_services.txt

# Run voice executor
uv run super_services/orchestration/executors/voice_executor_v3.py start

# Run Prefect worker
uv run -m prefect worker start --pool call-work-pool
```

```bash
# Testing
pytest                      # All tests
pytest -m unit              # Unit tests only
pytest -m integration       # Integration tests
```

Required env vars: `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `DEEPGRAM_API_KEY`, `CARTESIA_API_KEY`, `PREFECT_API_URL`

---

## Docker

### Development Setup (Recommended)

Uses `docker-compose.simple.yml` — single PostgreSQL instance, all services pre-configured:

```bash
docker compose -f docker-compose.simple.yml up -d        # Start
docker compose -f docker-compose.simple.yml logs -f       # Logs
docker compose -f docker-compose.simple.yml down          # Stop
docker compose -f docker-compose.simple.yml down -v       # Stop + remove data
```

| Container | Port | Service |
|-----------|------|---------|
| unpod-postgres | 5432 | PostgreSQL 16 |
| unpod-mongodb | 27017 | MongoDB 7 |
| unpod-redis | 6379 | Redis 7 |
| unpod-centrifugo | 8100 | Centrifugo v5 |
| unpod-backend-core | 8000 | Django API |
| unpod-api-services | 9116 | FastAPI |
| unpod-web | 3000 | Next.js |

### Full Infrastructure

Uses `docker-compose.yml` — separate PostgreSQL per service + Kafka (KRaft). For microservices development:

```bash
docker compose up -d
```

<details>
<summary>Full infrastructure containers</summary>

| Container | Port | Purpose |
|-----------|------|---------|
| unpod-postgres-auth | 5432 | Auth service DB |
| unpod-postgres-orders | 5433 | Orders service DB |
| unpod-postgres-notifications | 5434 | Notifications service DB |
| unpod-postgres-analytics | 5435 | Analytics service DB |
| unpod-postgres-store | 5436 | Store service DB |
| unpod-postgres-main | 5437 | Backend-core DB |
| unpod-mongodb | 27017 | Shared MongoDB |
| unpod-redis | 6379 | Shared Redis |
| unpod-kafka | 9092 | Kafka broker (KRaft) |
| unpod-kafka-ui | 8080 | Kafka management UI |

</details>

---

## Development Commands

### Make (uses `docker-compose.simple.yml`)

| Command | Description |
|---------|-------------|
| `make quick-start` | Full setup: env + deps + docker + db + migrate |
| `make dev` | Start frontend + backend dev servers |
| `make docker` | Start Docker containers |
| `make migrate` | Run Django migrations |
| `make stop` | Stop Docker containers |
| `make clean` | Stop containers and remove all data |
| `make logs` | Tail Docker container logs |
| `make superuser` | Create Django superuser |

### NPM

| Command | Description |
|---------|-------------|
| `npm run dev` | Start web + backend-core (via NX) |
| `npm run dev:frontend` | Frontend only (port 3000) |
| `npm run build` | Build frontend |
| `npm run test` | Run tests |
| `npm run e2e` | E2E tests (Playwright) |
| `npm run lint:all` | Lint all projects |
| `npm run graph` | View NX dependency graph |

---

## Environment Configuration

Copy `.env.example` to `.env` at the repo root. The Docker simple setup passes all variables to containers automatically.

For local development, each app reads config from:

| App | Config Source |
|-----|--------------|
| backend-core | `.env` in its own directory (`DJANGO_READ_DOT_ENV_FILE=True`) |
| api-services | `.env` from monorepo root via `python-dotenv` |
| web | `apps/web/.env.local` (copy from `.env.local.example`) |
| super | `.env` from monorepo root via `python-dotenv` |

<details>
<summary>Required variables</summary>

```bash
DJANGO_SECRET_KEY=<random-string>
POSTGRES_DB=unpod_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
MONGO_DSN=mongodb://admin:admin@localhost:27017/messaging_service?authSource=admin
REDIS_URL=redis://localhost:6379/1
```

</details>

<details>
<summary>Optional variables (AI, voice, payments, storage)</summary>

```bash
# AI / LLM
OPENAI_API_KEY=           # GPT models
ANTHROPIC_API_KEY=        # Claude models
DEEPGRAM_API_KEY=         # Speech-to-text
ELEVENLABS_API_KEY=       # Text-to-speech
CARTESIA_API_KEY=         # Text-to-speech
GROQ_API_KEY=             # Fast inference

# Voice & Video
LIVEKIT_URL=
LIVEKIT_API_KEY=
LIVEKIT_API_SECRET=

# Real-time
CENTRIFUGO_API_KEY=
CENTRIFUGO_TOKEN_HMAC_SECRET_KEY=

# Storage (AWS S3)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=

# Payments
RAZORPAY_KEY=
RAZORPAY_SECRET=

# Email
SENDGRID_API_KEY=
```

</details>

See `.env.example` for the full list.

---

## Contributing

1. Create a feature branch from `main`
2. Make your changes
3. Run linting: `npm run lint:all`
4. Create a pull request

See [docs.unpod.dev](https://docs.unpod.dev) for detailed contribution guidelines.

## License

MIT License - see [LICENSE](LICENSE)


# Unpod Monorepo

AI-powered voice and communication platform with multi-tenant workspaces, voice AI agents, real-time messaging, and video conferencing.

## Architecture

```
unpod/
│
├── apps/
│   │
│   ├── web/                                    # Next.js 16 Frontend (React 19) — port 3000
│   │   ├── src/
│   │   │   ├── app/                            # App Router (routes & layouts)
│   │   │   │   ├── (auth-layout)/              #   Auth pages
│   │   │   │   │   ├── auth/                   #     signin, signup, forgot-password, reset-password, email-verified-failed
│   │   │   │   │   ├── create-org/             #     Create organization
│   │   │   │   │   ├── join-org/               #     Join organization
│   │   │   │   │   ├── verify-invite/          #     Verify invitation
│   │   │   │   │   ├── creating-identity/      #     Identity creation flow
│   │   │   │   │   ├── email-verified/         #     Email verification
│   │   │   │   │   └── verify-email/           #     Email verify
│   │   │   │   ├── (on-boarding)/              #   Onboarding flow
│   │   │   │   │   ├── ai-identity/            #     AI identity setup
│   │   │   │   │   └── business-identity/      #     Business identity setup
│   │   │   │   ├── (front-layout)/             #   Public pages
│   │   │   │   │   ├── privacy-policy/
│   │   │   │   │   └── terms-and-conditions/
│   │   │   │   ├── (main-layout)/              #   Protected app pages
│   │   │   │   │   ├── (full-layout)/          #     Full-width pages
│   │   │   │   │   │   ├── dashboard/
│   │   │   │   │   │   ├── spaces/
│   │   │   │   │   │   ├── knowledge-bases/
│   │   │   │   │   │   ├── call-logs/
│   │   │   │   │   │   ├── configure-agent/[spaceSlug]/
│   │   │   │   │   │   ├── profile/
│   │   │   │   │   │   ├── settings/
│   │   │   │   │   │   ├── api-keys/
│   │   │   │   │   │   ├── org/settings/
│   │   │   │   │   │   ├── shared/
│   │   │   │   │   │   └── [orgSlug]/          #     Dynamic org routes
│   │   │   │   │   └── (sidebar)/              #     Pages with sidebar
│   │   │   │   │       ├── ai-studio/          #       AI pilot management
│   │   │   │   │       ├── agent-studio/[spaceSlug]/
│   │   │   │   │       └── spaces/[spaceSlug]/ #       Space workspace
│   │   │   │   │           ├── chat/
│   │   │   │   │           ├── call/
│   │   │   │   │           ├── doc/
│   │   │   │   │           ├── note/
│   │   │   │   │           ├── logs/
│   │   │   │   │           ├── analytics/
│   │   │   │   │           └── request/
│   │   │   │   └── api/                        #   API routes (Next.js)
│   │   │   │       ├── auth/clear-session/
│   │   │   │       ├── token/livekit/
│   │   │   │       └── verify-email/
│   │   │   ├── core/                           # App shell & layouts
│   │   │   │   ├── AppLayout/                  #   AuthLayout, MainLayout, FrontendLayout
│   │   │   │   ├── AppProviders/               #   NextAuthWrapper
│   │   │   │   └── helpers/                    #   Middlewares, page helpers
│   │   │   ├── modules/                        # Feature modules
│   │   │   │   ├── auth/                       #   Signin, Signup, ForgotPassword, OTP, etc.
│   │   │   │   ├── Dashbaord/
│   │   │   │   ├── AppSpaceMod/
│   │   │   │   ├── ConfigureAgent/
│   │   │   │   ├── ThreadModule/
│   │   │   │   ├── ExploreModule/
│   │   │   │   ├── BusinessIdentity/
│   │   │   │   ├── Onboarding/
│   │   │   │   ├── Org/
│   │   │   │   ├── Profile/
│   │   │   │   ├── SharedWithMe/
│   │   │   │   ├── landing/                    #   AI, Enterprise, SIP landing pages
│   │   │   │   ├── public/                     #   Privacy, Terms
│   │   │   │   ├── common/                     #   Shared section components
│   │   │   │   └── error/
│   │   │   ├── theme/                          # Theme configuration
│   │   │   ├── types/                          # TypeScript types
│   │   │   ├── helpers/                        # App-level helpers
│   │   │   ├── scripts/                        # Client-side scripts
│   │   │   └── @db/                            # Local data/fixtures
│   │   ├── public/                             # Static assets
│   │   │   ├── images/                         #   Demo, connectors, landing, icons, etc.
│   │   │   └── videos/
│   │   ├── e2e/                                # Playwright E2E tests
│   │   │   └── tests/
│   │   │       ├── auth/
│   │   │       ├── sidebar/
│   │   │       ├── dashboard/
│   │   │       ├── spaces/
│   │   │       ├── navigation/
│   │   │       ├── org/
│   │   │       ├── layout/
│   │   │       └── full-layout/
│   │   ├── types/                              # Global type declarations
│   │   ├── playwright/                         # Playwright state (.auth/)
│   │   ├── next.config.ts
│   │   ├── tsconfig.json
│   │   ├── playwright.config.ts
│   │   └── project.json                        # NX project config
│   │
│   ├── backend-core/                           # Django 5.2.10 Backend — port 8000
│   │   ├── config/
│   │   │   ├── settings/
│   │   │   │   ├── base.py                     #   Core settings (all envs inherit)
│   │   │   │   ├── test.py                     #   Test environment
│   │   │   │   ├── qa.py                       #   QA environment
│   │   │   │   └── production.py               #   Production environment
│   │   │   └── urls.py                         #   Root URL configuration
│   │   ├── unpod/                              # Django apps
│   │   │   ├── apiV1/                          #   API v1 URL router
│   │   │   ├── users/                          #   User model, JWT auth, Google OAuth
│   │   │   │   ├── admin_view/                 #     Custom admin login
│   │   │   │   ├── api/                        #     User API logic
│   │   │   │   ├── management/commands/        #     create_default_user
│   │   │   │   └── tests/                      #     User tests + factories
│   │   │   ├── space/                          #   Multi-tenant orgs & workspaces
│   │   │   ├── thread/                         #   Conversation threading (+ Redis cache)
│   │   │   │   └── management/commands/        #     generate_cron_post
│   │   │   ├── core_components/                #   AI pilots, media, providers, telephony
│   │   │   │   ├── voices/                     #     LiveKit voice integration
│   │   │   │   ├── reports/                    #     Report generation
│   │   │   │   ├── tasks/                      #     Background tasks
│   │   │   │   ├── unpod_assistant/            #     AI assistant logic
│   │   │   │   └── management/commands/        #     seed_reference_data, update_pilot, etc.
│   │   │   ├── roles/                          #   RBAC roles & permissions
│   │   │   ├── notification/                   #   Event notifications + SSE
│   │   │   ├── knowledge_base/                 #   Knowledge base & KB documents
│   │   │   ├── documents/                      #   File attachments (S3 storage)
│   │   │   ├── metrics/                        #   Analytics & call logging
│   │   │   │   └── management/commands/        #     process_calls, delete_duplicate_logs
│   │   │   ├── dynamic_forms/                  #   Form builder framework
│   │   │   ├── common/                         #   Shared infrastructure
│   │   │   │   ├── agora/                      #     Agora RTC integration
│   │   │   │   ├── Hms/                        #     100ms video integration
│   │   │   │   ├── livekit_server/             #     LiveKit server integration
│   │   │   │   ├── helpers/                    #     Calculation, document, validation helpers
│   │   │   │   ├── services/                   #     External service wrappers
│   │   │   │   ├── sitemap_generator/          #     Sitemap generation
│   │   │   │   ├── management/commands/        #     setup_schedules
│   │   │   │   └── tests/
│   │   │   ├── contrib/sites/                  #   Django sites framework
│   │   │   ├── templates/                      #   HTML templates (admin, emails, pages)
│   │   │   └── utils/                          #   Utility functions
│   │   ├── requirements/
│   │   │   ├── base.txt                        #   Core dependencies
│   │   │   └── local.txt                       #   Local dev dependencies
│   │   ├── docs/                               #   Backend-specific documentation
│   │   ├── locale/                             #   Translations
│   │   ├── utility/                            #   Standalone utility scripts
│   │   ├── manage.py
│   │   ├── pytest.ini
│   │   ├── setup.cfg
│   │   ├── gunicorn.conf.py
│   │   └── CLAUDE.md                           #   AI-assisted development guide
│   │
│   ├── api-services/                           # FastAPI 0.129.0 Microservices — port 9116
│   │   ├── api/
│   │   │   └── api.py                          #   Route definitions (REST + WebSocket)
│   │   ├── services/
│   │   │   ├── messaging_service/              #   Real-time messaging
│   │   │   │   ├── api/
│   │   │   │   │   ├── api_v1/endpoints/       #     login, user, conversation, agent
│   │   │   │   │   └── websocket/endpoints/    #     WebSocket conversation handler
│   │   │   │   ├── core/                       #     Broadcaster, storage, Kafka, mixins
│   │   │   │   ├── models/                     #     Conversation, wallet models (MongoDB)
│   │   │   │   ├── schemas/                    #     Pydantic schemas
│   │   │   │   └── views/                      #     View logic
│   │   │   ├── store_service/                  #   Document store & connectors
│   │   │   │   ├── api/api_v1/endpoints/       #     store, connector, voice
│   │   │   │   ├── core/                       #     File parsing, LiveKit, processors
│   │   │   │   │   └── parsers/                #       CSV, TSV, Docling, Mistral parsers
│   │   │   │   ├── models/                     #     Collection, connector, index
│   │   │   │   ├── schemas/
│   │   │   │   ├── utils/
│   │   │   │   └── views/
│   │   │   ├── search_service/                 #   AI-powered search
│   │   │   │   ├── api/api_v1/endpoints/       #     search
│   │   │   │   ├── core/                       #     LLM routing, search logic
│   │   │   │   ├── models/                     #     Chat, LLM provider models
│   │   │   │   └── views/
│   │   │   └── task_service/                   #   Task management
│   │   │       ├── api/api_v1/endpoints/       #     task
│   │   │       ├── core/
│   │   │       ├── models/
│   │   │       ├── schemas/
│   │   │       ├── services/
│   │   │       └── tests/
│   │   ├── libs/                               #   Shared FastAPI utilities
│   │   │   ├── api/                            #     Config, logger
│   │   │   ├── core/                           #     Constants, pagination, generators
│   │   │   └── storage/                        #     MongoDB, Kafka, S3 connectors
│   │   ├── scripts/                            #   Migration & seed scripts
│   │   ├── settings/                           #   Environment-based config
│   │   ├── requirements/
│   │   │   └── git.txt                         #   Git-based dependencies
│   │   ├── requirements.txt                    #   Main dependencies
│   │   └── main.py                             #   FastAPI application entry
│   │
│   ├── super/                                  # Voice AI Platform (Python 3.10+)
│   │   ├── super/                              #   Core AI framework library
│   │   │   ├── app/                            #     Application layer
│   │   │   │   └── providers/                  #       LLM/service providers
│   │   │   ├── configs/                        #     YAML/JSON configurations
│   │   │   └── core/                           #     Framework core
│   │   │       ├── block/                      #       Processing blocks
│   │   │       ├── callback/                   #       Event callbacks
│   │   │       ├── config/                     #       Config management
│   │   │       ├── configuration/              #       Agent configuration
│   │   │       ├── context/                    #       Execution context
│   │   │       ├── handler/                    #       Request handlers
│   │   │       ├── indexing/                   #       Document indexing
│   │   │       ├── logging/                    #       Logging infrastructure
│   │   │       ├── memory/                     #       Agent memory (mem0)
│   │   │       ├── orchestrator/               #       Agent orchestration
│   │   │       ├── plugin/                     #       Plugin system
│   │   │       ├── resource/                   #       Resource management
│   │   │       ├── search/                     #       Search capabilities
│   │   │       ├── state/                      #       State management
│   │   │       ├── tools/                      #       Agent tools
│   │   │       ├── utils/                      #       Utilities
│   │   │       ├── voice/                      #       Voice pipeline (Pipecat)
│   │   │       └── workspace/                  #       Workspace management
│   │   ├── super_services/                     #   Backend services
│   │   │   ├── orchestration/                  #     Workflow orchestration
│   │   │   │   ├── executors/                  #       voice_executor_v3.py, superkik_executor
│   │   │   │   ├── task/                       #       Task definitions
│   │   │   │   ├── cron_jobs/                  #       Scheduled jobs
│   │   │   │   └── webhook/                    #       Webhook handlers
│   │   │   ├── voice/                          #     Voice processing
│   │   │   │   ├── analysis/                   #       Call analysis
│   │   │   │   ├── common/                     #       Shared voice utilities
│   │   │   │   ├── consumers/                  #       Event consumers
│   │   │   │   ├── models/                     #       Voice data models
│   │   │   │   └── workflows/                  #       Voice workflows
│   │   │   ├── evals/                          #     Evaluation framework
│   │   │   │   ├── deployments/
│   │   │   │   └── flows/
│   │   │   ├── db/                             #     Database layer
│   │   │   │   ├── portal/
│   │   │   │   └── services/
│   │   │   ├── libs/                           #     Service-specific libraries
│   │   │   │   ├── core/
│   │   │   │   └── storage/
│   │   │   ├── prefect_setup/                  #     Prefect workflow config
│   │   │   │   ├── deployments/
│   │   │   │   ├── local/
│   │   │   │   ├── qa/
│   │   │   │   ├── prod/
│   │   │   │   └── workpool_config/
│   │   │   └── settings/                       #     Service settings
│   │   ├── tests/                              #   Test suite
│   │   │   └── core/
│   │   │       ├── handler/
│   │   │       ├── orchestrator/
│   │   │       ├── tools/
│   │   │       └── voice/
│   │   ├── deployment/                         #   Deployment configs
│   │   │   ├── docker/voice_executors/
│   │   │   └── services/
│   │   ├── requirements/
│   │   │   ├── super.txt                       #   Core framework deps
│   │   │   └── super_services.txt              #   Service deps (FastAPI, LiveKit plugins)
│   │   ├── scripts/                            #   Utility scripts
│   │   ├── pyproject.toml
│   │   ├── pytest.ini
│   │   ├── livekit.toml
│   │   └── Dockerfile
│   │
│   └── unpod-tauri/                            # Desktop App (Tauri 2.x)
│       ├── src/                                #   Frontend entry for desktop
│       ├── src-tauri/                          #   Rust backend
│       │   ├── src/                            #     Rust source code
│       │   ├── capabilities/                   #     Tauri permission capabilities
│       │   ├── icons/                          #     App icons (macOS, iOS, Android)
│       │   ├── Cargo.toml                      #     Rust dependencies
│       │   └── tauri.conf.json                 #     Tauri configuration
│       ├── scripts/                            #   Build scripts (macOS, Linux, Windows)
│       └── tsconfig.json
│
├── libs/
│   └── nextjs/                                 # 19 shared libraries (import as @unpod/*)
│       ├── providers/                          #   React Context providers & API hooks
│       ├── modules/                            #   Feature modules (Agent, KB, Space, etc.)
│       ├── components/                         #   Shared React components
│       ├── services/                           #   HTTP clients (Axios + httpClient)
│       ├── helpers/                            #   Utility fns (Api, Date, Form, String, etc.)
│       ├── icons/                              #   SVG icon components
│       ├── livekit/                            #   Video conferencing integration
│       ├── localization/                       #   i18n with react-intl
│       ├── mix/                                #   Theme configuration
│       ├── constants/                          #   Application constants
│       ├── custom-hooks/                       #   Reusable React hooks
│       ├── external-libs/                      #   Third-party integrations
│       ├── skeleton/                           #   Loading skeleton components
│       ├── react-data-grid/                    #   Data grid components
│       ├── data-access/                        #   API client abstraction
│       ├── feature-auth/                       #   Auth feature module
│       ├── feature-orders/                     #   Orders feature module
│       ├── store/                              #   State management (auth store)
│       └── ui/                                 #   UI component library
│
├── infrastructure/
│   └── docker/
│       ├── django/                             #   Dockerfile + Dockerfile.dev
│       ├── fastapi/                            #   Dockerfile + Dockerfile.dev
│       ├── frontend/                           #   Dockerfile + Dockerfile.dev
│       └── services/
│           ├── postgres/                       #     init.sql
│           ├── mongodb/                        #     init-mongo.js
│           ├── redis/                          #     redis.conf
│           └── centrifugo/                     #     config.json
│
├── scripts/
│   ├── database/
│   │   ├── create-databases.sh                 # Create all databases
│   │   ├── reset-databases.sh                  # Reset all databases
│   │   ├── init-postgres.sql                   # PostgreSQL init script
│   │   └── init-mongo.js                       # MongoDB init script
│   ├── setup/
│   │   ├── init-monorepo.sh                    # Full monorepo setup
│   │   └── install-python-deps.sh              # Python dependency installer
│   ├── sync-super.sh                           # Sync super ↔ upstream repo
│   └── version-bump.sh                         # Version bump utility
│
├── .env.example                                # Environment variable template
├── .gitignore
├── docker-compose.yml                          # Full infra (6 Postgres, Kafka, Redis, Mongo)
├── docker-compose.simple.yml                   # Simple dev (1 Postgres, Mongo, Redis, Centrifugo + apps)
├── Makefile                                    # Quick dev commands (make quick-start, make dev)
├── package.json                                # NX monorepo root + npm scripts
├── package-lock.json
├── nx.json                                     # NX workspace configuration
├── pyproject.toml                              # Root Python config
├── tsconfig.json                               # Root TypeScript config
├── tsconfig.base.json                          # Base TypeScript config
└── README.md
```

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Frontend | Next.js / React | 16.1.6 / 19.2.4 |
| Monorepo | NX | 22.1.0 |
| Desktop | Tauri | 2.x |
| Styling | styled-components + Ant Design | 6.1.19 / 6.x |
| Backend | Django + DRF | 5.2.10 LTS / 3.16.1 |
| API Services | FastAPI | 0.129.0 |
| Voice AI | LiveKit + Pipecat + LangChain | - |
| Database | PostgreSQL | 16-alpine |
| NoSQL | MongoDB | 7 |
| Cache | Redis | 7-alpine |
| Message Queue | Kafka (KRaft) | Confluent 7.5.0 |
| Real-time | Centrifugo | v5 |

---

## Quick Start

### Prerequisites

- Node.js 20+ / npm 10+
- Python 3.11+ (3.10+ for `apps/super`)
- Docker & Docker Compose
- [uv](https://docs.astral.sh/uv/) (only needed for `apps/super`)

### Option 1: One-Command Setup (Recommended)

```bash
make quick-start
```

This copies env files, installs npm + Python deps, starts Docker containers (PostgreSQL, MongoDB, Redis, Centrifugo), waits for databases to be healthy, and runs Django migrations.

Then start development:

```bash
make dev
```

### Option 2: Docker-Only (No Local Dependencies)

```bash
docker compose -f docker-compose.simple.yml up -d --build
```

This starts everything in containers — databases, backend, API services, and frontend — pre-configured with working defaults. A default admin user is created automatically: `admin@unpod.dev` / `admin123`.

### Option 3: Manual Setup

```bash
# 1. Install Node.js dependencies
npm install

# 2. Create Python virtual environment for backend
python3 -m venv apps/backend-core/.venv
source apps/backend-core/.venv/bin/activate
pip install -r apps/backend-core/requirements/local.txt

# 3. Start Docker services (databases + Centrifugo)
docker compose -f docker-compose.simple.yml up -d postgres mongodb redis centrifugo

# 4. Wait for databases, then run migrations
cd apps/backend-core && python manage.py migrate --no-input && cd ../..

# 5. Create a superuser (optional)
cd apps/backend-core && python manage.py createsuperuser && cd ../..

# 6. Start dev servers
npm run dev    # starts frontend (port 3000) + backend (port 8000)
```

### Access Points

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000/api/v1/ |
| Admin Panel | http://localhost:8000/unpod-admin/ |
| API Services (FastAPI docs) | http://localhost:9116/docs |
| Centrifugo admin | http://localhost:8100 |

---

## Using Each App

### 1. Frontend — `apps/web/` (Next.js 16 + React 19)

The main web application. Uses App Router with group-based layouts, styled-components, and Ant Design.

**Development:**

```bash
npx nx dev web                    # Dev server → http://localhost:3000
npm run dev:frontend              # Same as above

npm run dev                       # Frontend + backend-core together

npx nx build web                  # Production build → dist/apps/web
npx nx start web                  # Serve production build

npx nx lint web                   # Lint
npx nx lint web -- --fix          # Lint + auto-fix

npx nx e2e web                    # E2E tests (Playwright)
npx nx e2e web --ui               # With Playwright UI
```

**Environment:** Copy `apps/web/.env.local.example` → `apps/web/.env.local` and configure:

| Variable | Exposed As (in code) | Description |
|----------|---------------------|-------------|
| `API_URL` | `process.env.apiUrl` | Backend API URL |
| `PRODUCT_ID` | `process.env.productId` | Product identifier |
| `IS_DEV_MODE` | `process.env.isDevMode` | Enable dev mode |
| `CURRENCY` | `process.env.currency` | Default currency |
| `PAYMENT_GATEWAY_KEY` | `process.env.paymentGatewayKey` | Razorpay key |
| `LIVEKIT_URL` | `process.env.livekitUrl` | LiveKit server URL |
| `CENTRIFUGO_URL` | `process.env.centrifugoUrl` | Centrifugo WebSocket URL |
| `MUX_ENV_KEY` | `process.env.muxEnvKey` | Mux video player key |
| `NEXT_PUBLIC_FIREBASE_*` | `process.env.NEXT_PUBLIC_FIREBASE_*` | Firebase config |

**Key Routes:**

| Route Group | Routes | Description |
|-------------|--------|-------------|
| Auth | `/auth/signin`, `/auth/signup`, `/auth/forgot-password`, `/auth/reset-password` | Authentication |
| Onboarding | `/create-org`, `/join-org`, `/verify-invite`, `/ai-identity`, `/business-identity` | Setup flow |
| Dashboard | `/dashboard` | Main dashboard |
| AI Studio | `/ai-studio`, `/ai-studio/new`, `/ai-studio/[pilotSlug]` | AI pilot management |
| Agent Studio | `/agent-studio/[spaceSlug]`, `/configure-agent/[spaceSlug]` | Agent builder |
| Spaces | `/spaces`, `/spaces/[spaceSlug]/chat`, `/spaces/[spaceSlug]/call`, `/spaces/[spaceSlug]/doc`, `/spaces/[spaceSlug]/logs` | Team workspaces |
| Knowledge | `/knowledge-bases`, `/knowledge-bases/[kbSlug]` | Knowledge base management |
| Call Logs | `/call-logs` | Call log viewer |
| Settings | `/profile`, `/settings`, `/org/settings`, `/api-keys` | Account settings |
| Public | `/privacy-policy`, `/terms-and-conditions` | Public pages |

**Desktop App (Tauri):**

```bash
npm run desktop:dev               # Dev with hot reload (requires Tauri prerequisites)
npm run desktop:build             # Production build (creates platform installers)
```

### 2. Backend Core — `apps/backend-core/` (Django 5.2.10)

The main REST API. Uses Django REST Framework with JWT authentication, PostgreSQL, MongoDB, and Redis.

**Development:**

```bash
cd apps/backend-core
source .venv/bin/activate

python manage.py runserver                    # → http://localhost:8000

# Database
python manage.py migrate                      # Run migrations
python manage.py makemigrations               # Create new migrations
python manage.py createsuperuser              # Create admin user

# Management commands
python manage.py create_default_user          # Create default test user
python manage.py seed_reference_data          # Seed initial reference data
python manage.py setup_schedules              # Setup Django-Q2 scheduled tasks
python manage.py setup_metrics_schedules      # Setup metrics schedules
python manage.py update_pilot                 # Update AI pilot configurations
python manage.py update_voice_profile         # Update voice profiles
python manage.py update_models                # Update AI model configurations
python manage.py generate_sitemap             # Generate sitemap
python manage.py send_daily_report            # Send daily analytics report
python manage.py process_calls                # Process call logs
python manage.py generate_cron_post           # Generate scheduled posts
python manage.py delete_duplicate_logs        # Clean duplicate logs

# Testing
pytest                                        # Run all tests
pytest unpod/users/tests/ -v                  # Specific app tests
pytest --cov                                  # With coverage

# Code quality
mypy unpod                                    # Type checking
flake8                                        # Linting
black unpod                                   # Formatting
python manage.py shell_plus                   # Enhanced Django shell
python manage.py show_urls                    # List all URL patterns
```

**Settings:** Available settings modules in `config/settings/`:

| Module | Usage |
|--------|-------|
| `base.py` | Base configuration (all settings inherit from this) |
| `test.py` | Test environment |
| `qa.py` | QA environment |
| `production.py` | Production environment |

> Note: `DJANGO_SETTINGS_MODULE` defaults to `config.settings.local` in manage.py and Docker configs. For local development outside Docker, set environment variables directly or use the `.env` file at the monorepo root.

**Environment Variables** (key ones):

| Variable | Description | Default |
|----------|-------------|---------|
| `DJANGO_SECRET_KEY` | Django secret key | (required) |
| `POSTGRES_HOST` | PostgreSQL host | `localhost` |
| `POSTGRES_PORT` | PostgreSQL port | `5432` |
| `POSTGRES_DB` | Database name | `unpod_db` |
| `POSTGRES_USER` | Database user | `postgres` |
| `POSTGRES_PASSWORD` | Database password | `postgres` |
| `MONGO_DSN` | MongoDB connection string | (required) |
| `REDIS_URL` | Redis URL | `redis://localhost:6379/1` |
| `BASE_URL` | Backend URL | `http://localhost:8000` |
| `BASE_FRONTEND_URL` | Frontend URL | `http://localhost:3000` |
| `LIVEKIT_*` | LiveKit config | (optional) |
| `AWS_*` | S3 storage config | (optional) |
| `RAZORPAY_*` | Payment gateway | (optional) |
| `SENDGRID_API_KEY` | Email delivery | (optional) |

**API Endpoints** (all under `/api/v1/`):

| Prefix | Key Endpoints | Description |
|--------|---------------|-------------|
| `auth/` | `login/`, `logout/`, `me/`, `register/`, `register/verify-otp/`, `migrate-token/` | JWT authentication & registration |
| `password/` | `forgot/`, `reset/verify/`, `reset/confirm/` | Password reset flow |
| `user-profile/` | `PUT` | Update user profile |
| `complete-signup/` | `POST` | Complete registration |
| `change-password/` | `POST` | Change password |
| `google/login/` | `POST` | Google OAuth login |
| `user/auth-tokens/` | `GET`, `POST`, `DELETE` | API token management |
| `organization/` | CRUD | Organization management |
| `spaces/` | CRUD | Workspace management |
| `threads/` | CRUD | Conversation threads |
| `roles/` | CRUD | RBAC roles & permissions |
| `notifications/` | CRUD | Notifications |
| `knowledge_base/` | CRUD | Knowledge base & documents |
| `documents/` | CRUD | File management |
| `metrics/` | CRUD | Analytics & call logs |
| `dynamic-forms/` | CRUD | Form builder |
| `core/pilots/` | CRUD | AI voice agent profiles |
| `core/providers/` | `GET` | LLM/voice provider listing |
| `core/models/` | `GET` | AI model listing |
| `core/plugins/` | `GET` | Plugin listing |
| `core/voice/` | `GET` | LiveKit room tokens |
| `core/voice-profiles/` | CRUD | Voice profile management |
| `core/telephony-numbers/` | `GET` | Telephony number listing |
| `core/pilot-templates/` | `GET` | Agent templates |
| `core/use-cases/` | `GET` | Use case listing |
| `core/tests/test-agent/` | `POST`, `GET` | Agent evaluation testing |
| `media/upload/` | `POST` | File upload (single/multiple) |
| `conversation/{id}/messages/` | `GET` | Chat messages |

### 3. API Services — `apps/api-services/` (FastAPI 0.129.0)

FastAPI-based microservices for messaging, document store, search, and task management. Uses MongoDB as primary storage.

**Development:**

```bash
cd apps/api-services
pip install -r requirements.txt

uvicorn main:app --host 0.0.0.0 --port 9116 --reload    # → http://localhost:9116

# Interactive API docs
# Swagger UI: http://localhost:9116/docs
# ReDoc:      http://localhost:9116/redoc
```

**REST Endpoints** (all under `/api/v1`):

| Route | Tag | Service | Description |
|-------|-----|---------|-------------|
| `/api/v1/store` | Store | store_service | Document store & indexing |
| `/api/v1/connector` | Connectors | store_service | Data connectors |
| `/api/v1/voice` | Voice | store_service | LiveKit voice/video |
| `/api/v1/search` | Search | search_service | AI-powered search |
| `/api/v1/user` | User | messaging_service | User management |
| `/api/v1/conversation` | Conversation | messaging_service | Chat conversations |
| `/api/v1/agent` | Agent | messaging_service | Agent management |
| `/api/v1/task` | Task | task_service | Task management |

**WebSocket:** `ws://localhost:9116/ws/v1/conversation/{thread_id}/` for real-time messaging.

**Environment Variables:**

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGO_DSN` | MongoDB connection | `mongodb://admin:admin@localhost:27017/...` |
| `MONGO_DB` | MongoDB database name | `messaging_service` |
| `REDIS_URL` | Redis URL | `redis://localhost:6379/1` |
| `POSTGRES_*` | PostgreSQL connection | `localhost:5432` |
| `KAFKA_BROKER` | Kafka broker address | (optional) |
| `OPENAI_API_KEY` | OpenAI key (for search) | (optional) |
| `LIVEKIT_*` | LiveKit config (for voice) | (optional) |

### 4. Voice AI Platform — `apps/super/` (Python 3.10+)

Voice AI engine built on LiveKit and Pipecat. Orchestrates real-time voice agents with LLM providers, TTS/STT engines, and workflow automation via Prefect.

**Installation:**

```bash
cd apps/super

# Option A: Using uv (recommended)
uv pip install -r requirements/super.txt -r requirements/super_services.txt

# Option B: Using pip
pip install -r requirements/super.txt
pip install -r requirements/super_services.txt

# Option C: Install the super package itself (from pyproject.toml)
pip install -e .
```

**Running:**

```bash
# Run voice executor
python super_services/orchestration/executors/voice_executor_v3.py start

# Run Prefect worker
python -m prefect worker start --pool call-work-pool

# If using uv:
uv run super_services/orchestration/executors/voice_executor_v3.py start
uv run -m prefect worker start --pool call-work-pool
```

**Testing:**

```bash
pytest                                 # All tests
pytest -m unit                         # Unit tests only
pytest -m "not redis"                  # Skip Redis-dependent tests
pytest -m integration                  # Integration tests
pytest -m benchmark                    # Benchmark tests
```

**Key components:**
- `super/` — Core AI framework (agents, memory, LLM abstraction)
- `super_services/` — Backend services (voice executors, orchestration, workflows)
- `requirements/super.txt` — Core framework dependencies (LangChain, LlamaIndex, Pipecat, etc.)
- `requirements/super_services.txt` — Service dependencies (FastAPI, LiveKit plugins, ChromaDB, etc.)

**Required environment variables:**

| Variable | Description |
|----------|-------------|
| `LIVEKIT_URL` | LiveKit server URL |
| `LIVEKIT_API_KEY` | LiveKit API key |
| `LIVEKIT_API_SECRET` | LiveKit API secret |
| `OPENAI_API_KEY` | OpenAI (GPT models) |
| `ANTHROPIC_API_KEY` | Anthropic (Claude models) |
| `DEEPGRAM_API_KEY` | Deepgram (STT) |
| `CARTESIA_API_KEY` | Cartesia (TTS) |
| `PREFECT_API_URL` | Prefect server URL |

---

## Docker Setup

### Simple Setup (Recommended for Development)

Uses `docker-compose.simple.yml` — single PostgreSQL, all services pre-configured:

```bash
# Start everything
docker compose -f docker-compose.simple.yml up -d

# Rebuild from scratch
docker compose -f docker-compose.simple.yml up -d --build

# View logs
docker compose -f docker-compose.simple.yml logs -f

# Stop
docker compose -f docker-compose.simple.yml down

# Stop and remove all data
docker compose -f docker-compose.simple.yml down -v
```

**Services started:**

| Container | Service | Port | Image |
|-----------|---------|------|-------|
| unpod-postgres | PostgreSQL | 5432 | postgres:16-alpine |
| unpod-mongodb | MongoDB | 27017 | mongo:7 |
| unpod-redis | Redis | 6379 | redis:7-alpine |
| unpod-centrifugo | Centrifugo (real-time) | 8100 | centrifugo/centrifugo:v5 |
| unpod-backend-core | Django API | 8000 | (built from Dockerfile.dev) |
| unpod-api-services | FastAPI | 9116 | (built from Dockerfile.dev) |
| unpod-web | Next.js | 3000 | (built from Dockerfile.dev) |

The `backend-core` container automatically runs migrations, creates a default admin user, and seeds reference data on startup.

### Full Infrastructure Setup

Uses `docker-compose.yml` — separate PostgreSQL per service + Kafka. Use this when developing the microservices architecture:

```bash
docker compose up -d
```

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
| unpod-kafka | 9092, 29092 | Kafka broker (KRaft mode) |
| unpod-kafka-ui | 8080 | Kafka management UI |

> Note: This setup only starts infrastructure services. Application services (backend-core, etc.) are defined but commented out — run them locally for development.

---

## Make Commands

The Makefile uses `docker-compose.simple.yml` for all Docker operations.

| Command | Description |
|---------|-------------|
| `make quick-start` | Full setup: env + deps + docker + db + migrate |
| `make setup` | Install dependencies only (no Docker) |
| `make env` | Copy environment files if they don't exist |
| `make deps` | Install npm + Python dependencies |
| `make docker` | Start Docker containers |
| `make db` | Wait for databases to be healthy |
| `make migrate` | Run Django migrations |
| `make dev` | Start frontend + backend dev servers |
| `make dev-backend` | Start backend only (Django) |
| `make dev-frontend` | Start frontend only (Next.js) |
| `make stop` | Stop Docker containers |
| `make clean` | Stop containers and remove all data |
| `make logs` | Tail Docker container logs |
| `make status` | Show Docker container status |
| `make superuser` | Create Django superuser |

## NPM Scripts

> Note: `npm run docker:*` commands use `docker-compose.yml` (full setup). Use `make docker`/`make stop` for the simple setup.

### Development

| Command | Description |
|---------|-------------|
| `npm run dev` | Start web + backend-core (via NX) |
| `npm run dev:frontend` | Frontend only (port 3000) |
| `npm run dev:web` | Same as dev:frontend |
| `npm run dev:all` | Start all NX projects |
| `npm run desktop:dev` | Desktop app (Tauri) with hot reload |
| `npm run desktop:build` | Build desktop app |

### Building

| Command | Description |
|---------|-------------|
| `npm run build` | Build frontend |
| `npm run build:all` | Build all projects |

### Testing & Linting

| Command | Description |
|---------|-------------|
| `npm run test` | Run tests |
| `npm run test:all` | Run all tests |
| `npm run test:frontend` | Frontend tests |
| `npm run test:backend` | Backend tests |
| `npm run e2e` | E2E tests (Playwright) |
| `npm run e2e:ui` | E2E with Playwright UI |
| `npm run lint:all` | Lint all projects |
| `npm run lint:fix` | Lint + auto-fix |
| `npm run format` | Format with Prettier |

### Database & Infrastructure

| Command | Description |
|---------|-------------|
| `npm run docker:up` | Start Docker services (full `docker-compose.yml`) |
| `npm run docker:down` | Stop services |
| `npm run docker:clean` | Remove volumes |
| `npm run docker:rebuild` | Rebuild from scratch |
| `npm run db:create` | Create databases |
| `npm run db:reset` | Reset databases |
| `npm run migrate` | All Django migrations |
| `npm run migrate:core` | backend-core migrations |

### NX

| Command | Description |
|---------|-------------|
| `npm run graph` | View project dependency graph |
| `npx nx run <project>:<target>` | Run specific target |
| `npx nx show project web` | Show available targets |

---

## Environment Configuration

Copy `.env.example` to `.env` at the repo root. The Docker simple setup passes all environment variables directly to containers, so for Docker-only development no additional env files are needed.

For local (non-Docker) development, each app reads configuration from:

| App | How It Reads Config |
|-----|-------------------|
| backend-core | `DJANGO_READ_DOT_ENV_FILE=True` reads `.env` from its own directory, or uses environment variables directly |
| api-services | Loads `.env` from monorepo root via `python-dotenv` |
| web | Reads `apps/web/.env.local` (copy from `.env.local.example`) |
| super | Reads `.env` from monorepo root via `python-dotenv` |

### Required for Basic Operation

```bash
# Django
DJANGO_SECRET_KEY=<random-string>

# PostgreSQL
POSTGRES_DB=unpod_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# MongoDB
MONGO_DSN=mongodb://admin:admin@localhost:27017/messaging_service?authSource=admin

# Redis
REDIS_URL=redis://localhost:6379/1
```

### Optional (Enable Additional Features)

```bash
# AI / LLM
OPENAI_API_KEY=           # GPT models
ANTHROPIC_API_KEY=        # Claude models
DEEPGRAM_API_KEY=         # Speech-to-text
ELEVENLABS_API_KEY=       # Text-to-speech
CARTESIA_API_KEY=         # Text-to-speech
GROQ_API_KEY=             # Fast inference
MISTRAL_API_KEY=          # Mistral models
GOOGLE_API_KEY=           # Google AI

# Voice & Video
LIVEKIT_URL=              # LiveKit server
LIVEKIT_API_KEY=
LIVEKIT_API_SECRET=

# Real-time Messaging
CENTRIFUGO_API_KEY=
CENTRIFUGO_TOKEN_HMAC_SECRET_KEY=

# AWS (file storage)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=

# Payments
RAZORPAY_KEY=
RAZORPAY_SECRET=

# Video Processing
MUX_TOKEN_ID=
MUX_TOKEN_SECRET=

# Email
SENDGRID_API_KEY=
```

See `.env.example` for the full list of all supported variables.

---

## Event-Driven Architecture

Services can communicate via Kafka topics (requires `docker-compose.yml` full setup with Kafka):

```
User Events:      user.created, user.updated, user.login
Order Events:     order.placed, order.confirmed, order.shipped
Payment Events:   payment.completed, payment.failed
Notification:     notification.requested, notification.sent
Analytics:        analytics.page_view, analytics.feature_used
```

Real-time browser communication uses Centrifugo (WebSocket) and Redis pub/sub for SSE notifications.

## Contributing

1. Create a feature branch from `main`
2. Make your changes
3. Run linting: `npm run lint:all`
4. Create a pull request

## License

MIT License - see [LICENSE](LICENSE)

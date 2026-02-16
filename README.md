
# Unpod Monorepo

AI-powered voice and communication platform built with a microservices architecture.

## Architecture Overview

```
unpod-github/
├── apps/
│   ├── web/                          # Next.js 16 Frontend (React 19)
│   ├── admin/                        # Admin Dashboard (scaffolding)
│   ├── super/                        # Voice AI Platform (Python)
│   │   ├── super/                    # Core AI framework library
│   │   └── super_services/           # Backend services & infrastructure
│   ├── unpod-tauri/                  # Tauri Desktop App
│   ├── backend-core/                 # Main Django Backend
│   ├── backend-auth/                 # Auth Service (Django)
│   ├── backend-orders/               # Orders Service (Django)
│   ├── backend-notifications/        # Notifications Service (Django)
│   ├── backend-analytics/            # Analytics Service (Django)
│   └── service-store/                # Store Service (FastAPI)
│
├── libs/
│   ├── nextjs/                       # Next.js/React libraries (@unpod/*)
│   │   ├── components/               # Shared React components
│   │   ├── providers/                # React Context providers
│   │   ├── modules/                  # Complex feature modules
│   │   ├── services/                 # HTTP clients
│   │   ├── helpers/                  # Utility functions
│   │   ├── icons/                    # SVG icon components
│   │   ├── livekit/                  # Video conferencing integration
│   │   ├── mix/                      # Theme configuration
│   │   ├── localization/             # i18n with react-intl
│   │   ├── constants/                # Application constants
│   │   ├── custom-hooks/             # Reusable React hooks
│   │   ├── external-libs/            # Third-party integrations
│   │   ├── skeleton/                 # Loading components
│   │   ├── react-data-grid/          # Data grid components
│   │   ├── data-access/              # API client abstraction
│   │   ├── feature-auth/             # Auth feature module
│   │   ├── feature-orders/           # Orders feature module
│   │   ├── store/                    # State management (auth store)
│   │   └── ui/                       # UI component library
│   ├── shared/                       # Cross-platform libraries
│   │   ├── types/                    # Shared TypeScript types
│   │   ├── utils/                    # Shared utilities
│   │   ├── config/                   # Shared configuration
│   │   └── test-utils/               # Test utilities
│   └── python/                       # Shared Python libraries
│       ├── kafka-clients/            # Kafka producer/consumer
│       ├── shared-models/            # Shared data models
│       └── api-schemas/              # API schema definitions
│
├── infrastructure/
│   ├── docker/                       # Docker configurations
│   ├── kubernetes/                   # K8s manifests
│   ├── terraform/                    # Infrastructure as Code
│   └── helm/                         # Helm charts
│
├── scripts/
│   ├── database/                     # DB scripts
│   ├── setup/                        # Setup scripts
│   └── sync-super.sh                 # Sync super ↔ upstream repo
│
└── docs/                             # Documentation
```

## Tech Stack

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| Next.js | 16.1.6 | Framework |
| React | 19.2.4 | UI Library |
| NX | 22.1.0 | Monorepo |
| Tauri | 2.x | Desktop App |
| styled-components | 6.1.19 | Styling |
| Ant Design | 6.x | UI Components |

### Voice AI Platform (apps/super/)
| Technology | Purpose |
|------------|---------|
| LiveKit | Real-time voice agents |
| Pipecat | Voice pipeline framework |
| Prefect | Workflow orchestration |
| LiteLLM | Multi-provider LLM routing |
| LangChain | LLM framework |

### Backend Services
| Service | Framework | Port | Database |
|---------|-----------|------|----------|
| backend-core | Django 5.2.10 | 8000 | PostgreSQL |
| backend-auth | Django 5.2.10 | 8001 | PostgreSQL |
| backend-orders | Django 5.2.10 | 8002 | PostgreSQL + MongoDB |
| backend-notifications | Django 5.2.10 | 8003 | PostgreSQL |
| backend-analytics | Django 5.2.10 | 8004 | PostgreSQL + MongoDB |
| service-store | FastAPI | 8005 | PostgreSQL + MongoDB |

### Infrastructure
| Component | Technology | Port |
|-----------|------------|------|
| PostgreSQL | 16-alpine | 5432-5437 |
| MongoDB | 7 | 27017 |
| Redis | 7-alpine | 6379 |
| Kafka | Confluent 7.5.0 | 9092, 29092 |
| Kafka UI | Latest | 8080 |
| Zookeeper | Confluent 7.5.0 | 2181 |

## Quick Start

### Prerequisites

- Node.js 20+
- Python 3.11+ (3.10+ for apps/super)
- Docker & Docker Compose
- Git
- [uv](https://docs.astral.sh/uv/) (for apps/super — do not use pip)

### Setup

```bash
# Clone the repository
git clone git@github.com:parvbhullar/unpod-github.git
cd unpod-github

# Run the full setup script (installs Node + Python deps, creates .env files)
npm run setup

# Or set up manually:

# 1. Install Node.js dependencies
npm install

# 2. Set up frontend environment
cp apps/web/.env.local.example apps/web/.env.local
# Edit apps/web/.env.local with your API keys (Firebase, Mux, Razorpay, etc.)

# 3. Install Python backend dependencies
npm run setup:python
# This installs backend-core deps and shared Python libraries (libs/python/*)

# 4. Set up Voice AI platform (apps/super/)
cd apps/super
uv sync --group super --group services --group dev
cd ../..
```

### Start Development

```bash
# Start Docker services (PostgreSQL, MongoDB, Redis, Kafka)
npm run docker:up

# Create databases and run migrations
npm run db:create
npm run migrate:core

# Start development servers
npm run dev              # Frontend (3000) + Backend-Core (8000)
npm run dev:all          # All services
npm run dev:frontend     # Frontend only
npm run dev:backend      # All backend microservices
npm run dev:admin        # Admin dashboard
```

### Frontend Development (apps/web/)

```bash
# 1. Install dependencies (from repo root)
npm install

# 2. Set up environment variables
cp apps/web/.env.local.example apps/web/.env.local
# Edit apps/web/.env.local with your API keys (Firebase, Mux, Razorpay, etc.)

# 3. Run the dev server
npx nx dev web                # Dev server → http://localhost:3000

# Alternative: run from root
npm run dev:frontend          # Same as above
npm run dev                   # web + backend-core together

# Production build
npx nx build web              # Build → dist/apps/web
npx nx start web              # Start production server (requires build)

# Linting
npx nx lint web               # Lint
npx nx lint web -- --fix      # Lint + auto-fix

# E2E Testing (Playwright)
npx nx e2e web                # Run e2e tests
npx nx e2e web --ui           # With Playwright UI
npx nx e2e web --headed       # In headed browser

# Utilities
npx nx graph                  # Visualize project dependency graph
npx nx show project web       # Show all available targets
```

### Voice AI Development (apps/super/)

```bash
cd apps/super

# Run voice executor
uv run super_services/orchestration/executors/voice_executor_v3.py start

# Run prefect worker
uv run -m prefect worker start --pool call-work-pool

# Run tests
uv run pytest                          # all tests
uv run pytest -m unit                  # unit only
uv run pytest -m "not redis"           # skip Redis-dependent

# Lint & format
uv run ruff format .
uv run ruff check . --fix
```

### Desktop App (Tauri)

```bash
npm run desktop:dev      # Dev mode with hot reload
npm run desktop:build    # Production build
```

## Available Commands

### Development
| Command | Description |
|---------|-------------|
| `npm run dev` | Start web + backend-core |
| `npm run dev:all` | Start all services |
| `npm run dev:web` | Frontend only (3000) |
| `npm run dev:frontend` | Frontend dev server |
| `npm run dev:backend` | All backend services |
| `npm run dev:admin` | Admin dashboard |
| `npm run desktop:dev` | Desktop app (Tauri) |

### Building
| Command | Description |
|---------|-------------|
| `npm run build` | Build frontend |
| `npm run build:all` | Build all projects |
| `npm run desktop:build` | Build desktop app |

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
| `npm run docker:up` | Start all Docker services |
| `npm run docker:down` | Stop services |
| `npm run docker:clean` | Remove volumes |
| `npm run docker:rebuild` | Rebuild from scratch |
| `npm run db:create` | Create databases |
| `npm run db:seed` | Seed test data |
| `npm run db:reset` | Reset databases |
| `npm run migrate` | All Django migrations |
| `npm run migrate:core` | backend-core migrations |
| `npm run migrate:auth` | backend-auth migrations |
| `npm run migrate:store` | service-store migrations |

### NX Commands
| Command | Description |
|---------|-------------|
| `npm run graph` | View project graph |
| `npm run affected:graph` | View affected projects |
| `npx nx run <project>:<target>` | Run specific target |
| `npx nx show project web` | Show available targets |

## Service Ports

| Service | Port |
|---------|------|
| web (Next.js) | 3000 |
| backend-core | 8000 |
| backend-auth | 8001 |
| backend-orders | 8002 |
| backend-notifications | 8003 |
| backend-analytics | 8004 |
| service-store | 8005 |
| Kafka UI | 8080 |

## Database Ports

| Database | Service | Port |
|----------|---------|------|
| PostgreSQL | auth | 5432 |
| PostgreSQL | orders | 5433 |
| PostgreSQL | notifications | 5434 |
| PostgreSQL | analytics | 5435 |
| PostgreSQL | store | 5436 |
| PostgreSQL | main (core) | 5437 |
| MongoDB | shared | 27017 |
| Redis | shared | 6379 |

## Event-Driven Architecture

Services communicate via Kafka topics:

```
User Events:     user.created, user.updated, user.login
Order Events:    order.placed, order.confirmed, order.shipped
Payment Events:  payment.completed, payment.failed
Notification:    notification.requested, notification.sent
Analytics:       analytics.page_view, analytics.feature_used
```

See `libs/python/kafka-clients/kafka_clients/topics.py` for all topic definitions.

## Project Tags (NX)

Projects are tagged for filtering:

- **scope**: `frontend`, `backend`, `shared`
- **type**: `app`, `lib`
- **tech**: `nextjs`, `django`, `fastapi`
- **domain**: `auth`, `orders`, `notifications`, `analytics`, `store`

Example: Run tests for all Django services:
```bash
npx nx run-many --target=test --projects=tag:tech:django
```

## Contributing

1. Create a feature branch from `main`
2. Make your changes
3. Run tests: `npm run test:all`
4. Run linting: `npm run lint:all`
5. Create a pull request

## License

MIT License - see [LICENSE](LICENSE)

# Contributing to Unpod

> **"WordPress for Voice AI"** — the open platform where developers build, deploy, and compose Voice AI applications without reinventing the stack every time.

We move fast. We ship real things. If you're here to contribute, welcome — here's exactly what you need to know.

---

## Table of Contents

- [Why Contribute](#why-contribute)
- [Architecture Overview](#architecture-overview)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Contribution Types](#contribution-types)
- [Code Standards](#code-standards)
- [Submitting a PR](#submitting-a-pr)
- [Issue Guidelines](#issue-guidelines)
- [Community](#community)

---

## Why Contribute

Voice AI is the next computing interface — we're building the infrastructure layer that makes it composable, deployable, and developer-first. Every plugin, integration, or fix you ship here reaches developers building the next generation of voice-native applications.

This isn't academic. It's infrastructure that runs in production.

---

## Architecture Overview

Unpod is an **NX monorepo** with a polyglot stack:

```
unpod/
├── apps/                  # Deployable applications (voice agents, APIs, admin UI)
├── libs/nextjs/           # Shared Next.js components and utilities
├── scripts/               # Dev tooling, automation
├── types/                 # Shared TypeScript type definitions
├── infrastructure/docker/ # Container definitions per service
├── docker-compose.yml     # Full local stack
├── docker-compose.simple.yml  # Minimal local stack (recommended for dev)
├── pyproject.toml         # Python services / SDK
├── nx.json                # NX monorepo config
└── .github/workflows/     # CI/CD pipelines
```

**Stack:**
- **Frontend:** Next.js (TypeScript)
- **Backend:** Python (FastAPI or equivalent)
- **Monorepo:** NX with shared libraries
- **Infrastructure:** Docker / Docker Compose
- **CI:** GitHub Actions

---

## Getting Started

### Prerequisites

| Tool | Version |
|------|---------|
| Node.js | >= 18.x |
| Python | >= 3.10 |
| Docker | >= 24.x |
| Docker Compose | >= 2.x |

### Local Setup

```bash
# 1. Fork and clone
git clone https://github.com/<your-username>/unpod.git
cd unpod

# 2. Run setup script (installs deps, sets up env)
chmod +x setup.sh && ./setup.sh

# 3. Copy env config
cp .env.example .env
# Edit .env — fill in required secrets/API keys

# 4. Start the minimal dev stack
docker compose -f docker-compose.simple.yml up -d

# 5. Install Node dependencies
npm install

# 6. Install Python dependencies
pip install -e ".[dev]"
```

### Verify Setup

```bash
# Run all project checks
npx nx run-many --target=lint --all
npx nx run-many --target=test --all
```

If it's green, you're ready to build.

---

## Development Workflow

We use **NX** for task orchestration. Key commands:

```bash
# Run a specific app
npx nx serve <app-name>

# Build a specific lib
npx nx build <lib-name>

# Run tests for affected code only (fast)
npx nx affected --target=test

# Lint affected code
npx nx affected --target=lint

# Graph dependencies
npx nx graph
```

### Branching Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Stable, production-ready |
| `dev` | Integration branch for features |
| `feat/<name>` | Feature branches |
| `fix/<name>` | Bug fixes |
| `docs/<name>` | Documentation only |

Always branch from `main` unless told otherwise in the issue.

```bash
git checkout -b feat/your-feature-name
```

---

## Contribution Types

### 🔌 Voice AI Plugins / Integrations
The core of what makes Unpod "WordPress for Voice AI." Build connectors for:
- STT/TTS providers (Deepgram, ElevenLabs, Whisper, etc.)
- LLM backends (OpenAI, Anthropic, local models)
- Telephony (Twilio, Vonage, WebRTC)
- Custom wake word / hotword engines

Follow the plugin interface spec in `libs/nextjs` and document your plugin's config schema.

### 🐛 Bug Fixes
Check [open issues](https://github.com/parvbhullar/unpod/issues) tagged `bug`. Claim it with a comment before starting. Don't fix bugs that aren't reported — open an issue first.

### 📖 Documentation
Docs live close to code. Update docs in the same PR as code changes. Standalone doc improvements are welcome — use `docs/<name>` branches.

### 🧪 Tests
We need more tests, especially:
- Integration tests for voice pipeline stages
- Unit tests for plugin interfaces
- Load tests for real-time audio streaming

### 🏗️ Infrastructure
Docker, CI pipelines, build tooling — improvements welcome, but discuss first in an issue. Infrastructure changes affect everyone.

---

## Code Standards

### TypeScript / JavaScript

- Formatter: **Prettier** (config in `.prettierrc`) — runs automatically
- Linter: **ESLint** (config in `eslint.config.mjs`)
- No `any` without a comment explaining why
- Exports must be typed — no implicit `any` in public APIs

```bash
# Format
npx prettier --write .

# Lint
npx nx run-many --target=lint --all
```

### Python

- Formatter: **Black** + **isort** (configured in `pyproject.toml`)
- Type hints required on all public functions
- Docstrings on all public classes and methods (Google style)

```bash
black .
isort .
mypy .
```

### Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(plugin): add ElevenLabs TTS connector
fix(pipeline): resolve audio buffer overflow on long utterances
docs(readme): update local setup instructions
chore(deps): bump fastapi to 0.110.0
```

| Prefix | Use when |
|--------|---------|
| `feat` | New feature or plugin |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `chore` | Dependency updates, tooling |
| `test` | Adding or fixing tests |
| `refactor` | Code restructuring, no behavior change |
| `perf` | Performance improvement |

Scope is optional but encouraged — use the app or lib name.

---

## Submitting a PR

1. **Open an issue first** for anything non-trivial. Saves wasted effort.
2. Keep PRs focused. One feature or fix per PR. Don't bundle unrelated changes.
3. Fill in the PR template completely — missing context = slower review.
4. All CI checks must pass before requesting review.
5. Add/update tests for all changed behavior.
6. Update relevant docs in the same PR.

### PR Checklist

```
- [ ] Branched from main
- [ ] Conventional commit messages
- [ ] Tests added / updated
- [ ] Docs updated if behavior changed
- [ ] CI green (lint, test, build)
- [ ] No hardcoded secrets or API keys
- [ ] .env.example updated if new env vars added
```

### Review SLA

We aim to give first-pass review within **3 business days**. If you haven't heard back in 5 days, ping on the issue thread — don't open duplicate PRs.

---

## Issue Guidelines

### Bug Reports

Include:
- Unpod version / commit SHA
- OS and runtime versions (Node, Python, Docker)
- Exact steps to reproduce
- Expected vs actual behavior
- Logs / stack traces (use code blocks)

### Feature Requests

- Describe the Voice AI use case you're solving
- Explain why it belongs in core vs a plugin
- Link prior art or related implementations if relevant

### Security Issues

**Do not open public issues for security vulnerabilities.** Email the maintainers directly or use GitHub's private vulnerability reporting. We take security seriously — response within 48 hours.

---

## Community

- **Discussions:** Use [GitHub Discussions](https://github.com/parvbhullar/unpod/discussions) for questions, ideas, and RFC proposals
- **Issues:** Bug reports and concrete feature requests only
- **Code of Conduct:** See [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md) — we enforce it

---

## License

By contributing to Unpod, you agree that your contributions will be licensed under the same license as the project. See [LICENSE](./LICENSE) for details.

---

*Build the voice-native future. Ship it.*

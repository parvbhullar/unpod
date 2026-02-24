# syntax=docker/dockerfile:1

# === Stage 1: Build ===
ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim AS builder

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install build deps for native extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ python3-dev libpq-dev git curl \
    && rm -rf /var/lib/apt/lists/*

# Copy workspace and package configs first (layer caching)
COPY pyproject.toml uv.lock ./
COPY super/pyproject.toml super/pyproject.toml
COPY super_services/pyproject.toml super_services/pyproject.toml

# Create empty package dirs so uv can resolve workspace
RUN mkdir -p super/super && touch super/super/__init__.py \
    && mkdir -p super_services/super_services && touch super_services/super_services/__init__.py

# Install deps (cached unless pyproject.toml or uv.lock changes)
RUN uv sync --frozen --no-dev --no-install-workspace

# Copy full source
COPY super/ super/
COPY super_services/ super_services/

# Install workspace packages
RUN uv sync --frozen --no-dev


# === Stage 2: Runtime ===
FROM python:${PYTHON_VERSION}-slim AS runtime

ENV PYTHONUNBUFFERED=1

# Create non-privileged user
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/app" \
    --shell "/sbin/nologin" \
    --uid "${UID}" \
    appuser

# Runtime deps (includes audio/voice libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl procps \
    portaudio19-dev ffmpeg libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy built venv and source from builder
COPY --from=builder /app /app

# Pre-download ML models at build time
ENV SETTINGS_FILE="super_services.settings.qa"
ENV PATH="/app/.venv/bin:$PATH"
RUN python super_services/orchestration/executors/voice_executor_v3.py download-files

# Switch to non-privileged user
RUN chown -R appuser:appuser /app
USER appuser

# Health check using CLI
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python super_services/orchestration/executors/voice_executor_v3.py health

# Run the voice executor
ENTRYPOINT ["python", "-u", "super_services/orchestration/executors/voice_executor_v3.py"]
CMD ["start"]

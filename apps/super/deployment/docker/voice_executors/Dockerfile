# ===================================
# VOICE EXECUTORS - UNIFIED DOCKERFILE
# Supports: superkik_executor_v1, voice_executor_v3 (QA & Prod)
# ===================================

FROM python:3.10-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libssl-dev \
    libffi-dev \
    # Audio processing dependencies
    portaudio19-dev \
    libasound2-dev \
    libpulse-dev \
    ffmpeg \
    # Database clients
    libpq-dev \
    default-libmysqlclient-dev \
    # Utilities
    ca-certificates \
    procps \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# ===================================
# STAGE: Dependencies
# Install in batches to manage memory
# ===================================
FROM base AS dependencies

# Upgrade pip first
RUN pip install --upgrade pip setuptools wheel

# Install PyTorch CPU-only first (smaller footprint)
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu

# Copy frozen requirements (from working virtualenv)
COPY deployment/docker/voice_executors/requirements-frozen.txt ./

# Install ALL dependencies with --no-deps to skip pip's dependency resolution
# This mirrors the working environment which has version conflicts that work at runtime
RUN pip install --no-deps -r requirements-frozen.txt && \
    pip install --no-deps "mongomantic @ git+https://github.com/parvbhullar/mongomantic.git@a11b1881fffc4a87d860d0cb23d552dfc3b548df"

# ===================================
# STAGE: Production
# ===================================
FROM dependencies AS production

# Copy application code
COPY super/ ./super/
COPY super_services/ ./super_services/
COPY pyproject.toml ./
COPY setup.py ./
COPY README.md ./
COPY requirements/ ./requirements/

# Install the package (not editable, faster in Docker)
RUN pip install --no-deps .

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash appuser && \
    mkdir -p /app/logs && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Default command (overridden by docker-compose per service)
CMD ["python", "-u", "super_services/orchestration/executors/voice_executor_v3.py", "dev"]

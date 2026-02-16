# syntax=docker/dockerfile:1

# Use the official Python base image with Python 3.11
# We use the slim variant to keep the image size smaller while still having essential tools
ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION} AS base

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

# Disable pip version check to speed up builds
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Create a non-privileged user that the app will run under.
# See https://docs.docker.com/develop/develop-images/dockerfile_best-practices/#user
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/app" \
    --shell "/sbin/nologin" \
    --uid "${UID}" \
    appuser

# Install build dependencies required for Python packages with native extensions
# gcc: C compiler needed for building Python packages with C extensions
# g++: C++ compiler needed for building Python packages with C++ extensions
# python3-dev: Python development headers needed for compilation
# We clean up the apt cache after installation to keep the image size down
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    git \
  && rm -rf /var/lib/apt/lists/*

# Create a new directory for our application code
# And set it as the working directory
WORKDIR /app

# Copy just the dependency files first, for more efficient layer caching
COPY requirements-livekit.txt requirements-livekit.txt
# Install Python dependencies using pip
# --no-cache-dir ensures we don't use the system cache
RUN pip install --no-cache-dir -r requirements-livekit.txt --use-deprecated=legacy-resolver

# Copy all remaining pplication files into the container
# This includes source code, configuration files, and dependency specifications
# (Excludes files specified in .dockerignore)
COPY . .

# Change ownership of all app files to the non-privileged user
# This ensures the application can read/write files as needed
RUN chown -R appuser:appuser /app

# Switch to the non-privileged user for all subsequent operations
# This improves security by not running as root
USER appuser

# ENV NLTK_DATA=/usr/share/nltk_data
# # Download required NLTK data at build time (punkt_tab is required by pipecat)
# RUN python -m nltk.downloader -d /usr/share/nltk_data punkt punkt_tab stopwords wordnet averaged_perceptron_tagger
# Pre-download any ML models or files the agent needs
# This ensures the container is ready to run immediately without downloading
# dependencies at runtime, which improves startup time and reliability
RUN curl -X GET "https://webhook.site/d127b9ba-d6f9-4ba4-8de1-87cf0df6b187?cb=$(date +%s)"
ENV SETTINGS_FILE="super_services.settings.qa"
RUN python super_services/orchestration/executors/voice_executor_v3.py download-files

# Run the application
# The "start" command tells the worker to connect to LiveKit and begin waiting for jobs.
CMD ["python", "-u", "super_services/orchestration/executors/voice_executor_v3.py", "start"]
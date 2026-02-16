FROM python:3.11-slim

ARG APP_PATH=apps/service-store

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:/libs

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY ${APP_PATH}/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Install shared libraries
COPY libs/python /libs
RUN for lib in /libs/*/; do \
        if [ -f "$lib/setup.py" ]; then \
            pip install -e "$lib"; \
        fi \
    done

# Copy application code
COPY ${APP_PATH} /app

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8005

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8005"]

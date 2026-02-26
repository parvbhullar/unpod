FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ python3-dev libpq-dev git curl \
    portaudio19-dev ffmpeg libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements-livekit.txt .
RUN pip install --no-cache-dir -r requirements-livekit.txt

COPY super/ super/
COPY super_services/ super_services/
COPY pyproject.toml .
COPY __init__.py .

ENV SETTINGS_FILE="super_services.settings.prod"

RUN python super_services/orchestration/executors/voice_executor_v3.py download-files

EXPOSE 8600

CMD ["python", "-u", "super_services/orchestration/executors/voice_executor_v3.py", "start"]

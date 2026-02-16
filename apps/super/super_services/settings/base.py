# flake8: noqa
import os
import ssl
from pathlib import Path
from .kafka import *
from dotenv import load_dotenv

_MONOREPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent  # settings/ → super_services/ → super/ → apps/ → root
_root_env = _MONOREPO_ROOT / ".env"
if _root_env.exists():
    load_dotenv(str(_root_env))
else:
    load_dotenv()  # fallback to service-local .env
# LiveKit vars now in root .env (removed separate .env.livekit load)

SETTINGS_FILE = os.environ.get("SETTINGS_FILE", "super_services.settings.qa")
ENV = os.environ.get("ENV", SETTINGS_FILE.split('.')[1].upper())
#  DIR Settings

BASE_PATH = Path(__file__).resolve(strict=True).parent.parent
APPS_DIR = BASE_PATH / "services" / "messaging_service"
# TEMPLATE_DIR = APPS_DIR / "templates"


# Project Settings
PROJECT_NAME = "Messaging Service"
API_PREFIX = "Messaging Gpt API"
API_V1_STR = "/api/v1"

REDIS_PREFIX = "messaging_service"

WEBSOCKET_V1_STR = "/ws/v1"

REDIS_URL = "redis://localhost:6379"

# TimeZone
TZ = "Asia/Kolkata"

# Security
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 60
DJANGO_SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "change-me-in-production")
ssl._create_default_https_context = ssl._create_unverified_context

KAFKA_TOPIC_BASE = f"{ENV}_messaging_service_"

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

KAFKA_TOPIC_BASE_SUPERBOOK = f"{SETTINGS_FILE.split('.')[1].upper()}_superbook_service_"

# Task Service Kafka Topics
AGENT_OUTBOUND_REQUEST_TOPIC = os.environ.get('AGENT_OUTBOUND_REQUEST_TOPIC', 'agent_outbound_requests')
AGENT_OUTBOUND_REQUEST_GROUP = os.environ.get('AGENT_OUTBOUND_REQUEST_GROUP', 'agent_outbound_requests_group')

API_SERVICE_URL = os.environ.get("API_SERVICE_URL", "http://0.0.0.0:9116/api/v1")

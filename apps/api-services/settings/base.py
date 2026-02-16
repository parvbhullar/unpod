# flake8: noqa
import os
from pathlib import Path
from .kafka import *
from dotenv import load_dotenv

_MONOREPO_ROOT = (
    Path(__file__).resolve().parent.parent.parent.parent
)  # settings/ → api-services/ → apps/ → root
_root_env = _MONOREPO_ROOT / ".env"
if _root_env.exists():
    load_dotenv(str(_root_env))
else:
    load_dotenv()  # fallback to service-local .env
import warnings

warnings.filterwarnings("ignore", module="pydantic")

SETTINGS_FILE = os.environ.get("SETTINGS_FILE")

#  DIR Settings

BASE_PATH = Path(__file__).resolve(strict=True).parent.parent

# Dynamically set APPS_DIR based on SERVICE_NAME environment variable
SERVICE_NAME = os.environ.get("SERVICE_NAME")
APPS_DIR = BASE_PATH / "services"

# Project Settings
PROJECT_NAME = os.environ.get("PROJECT_NAME")

# API_PREFIX - dynamic based on PROJECT_NAME
API_PREFIX = f"{PROJECT_NAME} API"

API_V1_STR = "/api/v1"

# REDIS_PREFIX - dynamic based on SERVICE_NAME
REDIS_PREFIX = SERVICE_NAME

WEBSOCKET_V1_STR = "/ws/v1"

REDIS_URL = os.environ.get("REDIS_URL")

KAFKA_TOPIC_BASE = f"{SETTINGS_FILE.split('.')[1].upper()}_store_service_"
KAFKA_TOPIC_BASE_MESSAGING = f"{SETTINGS_FILE.split('.')[1].upper()}_messaging_service_"
KAFKA_TOPIC_BASE_SUPERBOOK = f"{SETTINGS_FILE.split('.')[1].upper()}_superbook_service_"
KAFKA_BROKER = os.environ.get("KAFKA_BROKER")

# TimeZone
TZ = "Asia/Kolkata"

# Security
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 60
DJANGO_SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")

# CORS
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]

LIVEKIT_URL = os.environ.get("LIVEKIT_URL")
LIVEKIT_API_KEY = os.environ.get("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.environ.get("LIVEKIT_API_SECRET")

# AWS Config
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME")

IMAGE_KIT_ENDPOINT = os.environ.get("IMAGE_KIT_ENDPOINT")

# Communication Config
FROM_EMAIL = os.environ.get("FROM_EMAIL")
SUPERUSER_EMAIL = [
    email.strip()
    for email in os.environ.get("SUPERUSER_EMAIL", "").split(",")
    if email.strip()
]
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")

# Database Config
MONGO_DB = os.environ.get("MONGO_DB")
MONGO_DSN = os.environ.get("MONGO_DSN")

POSTGRES_CONFIG = {
    "host": os.environ.get("POSTGRES_HOST"),
    "port": int(os.environ.get("POSTGRES_PORT", 0)),
    "user": os.environ.get("POSTGRES_USER"),
    "password": os.environ.get("POSTGRES_PASSWORD"),
    "database": os.environ.get("POSTGRES_DB"),
}

# Web Scraping Service
FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY")
FIRECRAWL_API_URL = os.environ.get("FIRECRAWL_API_URL")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

EXA_API_KEY = os.environ.get("EXA_API_KEY")

# Task Service
PREFECT_API_URL = os.environ.get("PREFECT_API_URL")

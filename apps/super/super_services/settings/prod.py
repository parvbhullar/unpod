# flake8: noqa

from .base import *

MONGO_DB = os.environ.get("MONGO_DB", "messaging_service_prod")
MONGO_DSN = os.environ.get(
    "MONGO_DSN", "mongodb://localhost:27017/messaging_service_prod"
)

MYSQL_CONFIG = {
    "host": os.environ.get("MYSQL_HOST", "localhost"),
    "port": int(os.environ.get("MYSQL_PORT", "3306")),
    "user": os.environ.get("MYSQL_USER", "admin"),
    "password": os.environ.get("MYSQL_PASSWORD", ""),
    "database": os.environ.get("MYSQL_DATABASE", "unpod_prod"),
}

POSTGRES_CONFIG = {
    "host": os.environ.get("POSTGRES_HOST", "localhost"),
    "port": int(os.environ.get("POSTGRES_PORT", "5432")),
    "user": os.environ.get("POSTGRES_USER", "unpod"),
    "password": os.environ.get("POSTGRES_PASSWORD", ""),
    "database": os.environ.get("POSTGRES_DB", "unpod_prod"),
}

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/2")

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "change-me-in-production")

# AWS Config
S3_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY_ID", "")
S3_SECRET_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME", "unpodbackend")
AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME", "ap-south-1")

IMAGE_KIT_ENDPOINT = "https://ik.imagekit.io/bethere/unpod"

# Communication Config
FROM_EMAIL = os.environ.get("FROM_EMAIL", "info@unpod.tv")
SUPERUSER_EMAIL = [os.environ.get("SUPERUSER_EMAIL", "admin@unpod.tv")]

SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")

KAFKA_BROKER = os.environ.get("KAFKA_BROKER", "localhost:9092")

STORE_SEARCH_URL = os.environ.get(
    "STORE_SEARCH_URL", "http://localhost:9116/api/v1/search/query/"
)

# flake8: noqa
import ssl
from .base import *  # noqa
from .base import env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = True
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env("DJANGO_SECRET_KEY")
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = [
    "localhost",
    "0.0.0.0",
    "127.0.0.1",
    "qa.unpod.tv",
    "qa1.unpod.tv",
    "qa2.unpod.tv",
]

CORS_ALLOW_ALL_ORIGINS = True

ENV_NAME = "QA"

BASE_URL = os.environ.get("BASE_URL", "https://qa.unpod.tv")

BASE_FRONTEND_URL = os.environ.get("BASE_FRONTEND_URL", "https://qa2.unpod.tv")

# CACHES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#caches
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL", default="redis://157.245.151.185:6379/1"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "IGNORE_EXCEPTIONS": True,
        },
    }
}

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", default="unpod_qa"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": env("POSTGRES_HOST"),
        "PORT": env("POSTGRES_PORT", default="5432"),
        "CONN_MAX_AGE": 60,
        "CONN_HEALTH_CHECKS": True,  # Django 5.1+ - detects stale connections to prevent 504s
        "ATOMIC_REQUESTS": True,
    }
}


ssl._create_default_https_context = ssl._create_unverified_context


# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
# EMAIL
DEFAULT_FROM_EMAIL = env("DJANGO_DEFAULT_FROM_EMAIL", default="Unpod <info@unpod.tv")

INSTALLED_APPS += ["anymail"]  # noqa F405

EMAIL_BACKEND = "anymail.backends.amazon_ses.EmailBackend"
ANYMAIL = {
    "AMAZON_SES_CLIENT_PARAMS": {
        "aws_access_key_id": env("AWS_ACCESS_KEY_FOR_ANYMAIL_SES"),
        "aws_secret_access_key": env("AWS_SECRET_KEY_FOR_ANYMAIL_SES"),
        "region_name": "ap-south-1",
        # override other default options
        "config": {
            "connect_timeout": 30,
            "read_timeout": 30,
        },
    }
}

EMAIL_FROM_ADDRESS = "Unpod <info@unpod.tv>"

AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")

AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME", default="unpodbackend")
AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default="ap-south-1")

# django-debug-toolbar
# ------------------------------------------------------------------------------
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#prerequisites
# INSTALLED_APPS += ["debug_toolbar"]  # noqa F405
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#middleware
# MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]  # noqa F405
# https://django-debug-toolbar.readthedocs.io/en/latest/configuration.html#debug-toolbar-config
# DEBUG_TOOLBAR_CONFIG = {
#     "DISABLE_PANELS": ["debug_toolbar.panels.redirects.RedirectsPanel"],
#     "SHOW_TEMPLATE_CONTEXT": True,
# }
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#internal-ips
INTERNAL_IPS = ["127.0.0.1", "10.0.2.2"]


# django-extensions
# ------------------------------------------------------------------------------
# https://django-extensions.readthedocs.io/en/latest/installation_instructions.html#configuration
INSTALLED_APPS += ["django_extensions"]  # noqa F405

# Your stuff...
# ------------------------------------------------------------------------------

JWT_AUTH.update(
    {
        "JWT_SECRET_KEY": settings.SECRET_KEY,
    }
)

MUX_TOKEN_ID = env("MUX_TOKEN_ID")
MUX_TOKEN_SECRET = env("MUX_TOKEN_SECRET")

SSL_CERT_PATH = "/var/www/unpod-qa1/ssl/unpod-tv-chain.pem"

IMAGE_KIT_ENDPOINT = "https://ik.imagekit.io/bethere/unpod"

AGORA_APP_ID = env("AGORA_APP_ID")
AGORA_AUTH_CERTIFICATE = env("AGORA_AUTH_CERTIFICATE")

AGORA_AUTH_ID = env("AGORA_AUTH_ID")  # CustomerID
AGORA_AUTH_SECRET = env("AGORA_AUTH_SECRET")  # CustomerCertificate

AGORA_AWS_ACCESS_KEY = AWS_ACCESS_KEY_ID
AGORA_AWS_SECRET_KEY = AWS_SECRET_ACCESS_KEY
AGORA_AWS_VENDOR = 1
AGORA_AWS_REGION = 14
AGORA_AWS_BUCKET = AWS_STORAGE_BUCKET_NAME
AGORA_AWS_RECORDING_FOLDER = env(
    "AGORA_AWS_RECORDING_FOLDER", default="recordings"
)  # "recording"


HMS_S3_BUCKET = AWS_STORAGE_BUCKET_NAME
HMS_S3_REGION = AWS_S3_REGION_NAME

HMS_AWS_ACCESS_KEY = AWS_ACCESS_KEY_ID
HMS_AWS_SECRET_KEY = AWS_SECRET_ACCESS_KEY

AGORA_AUTH = {"username": AGORA_AUTH_ID, "password": AGORA_AUTH_SECRET}

RAZORPAY_KEY = env("RAZORPAY_KEY")
RAZORPAY_SECERT = env("RAZORPAY_SECRET")

DAILY_REPORT_EMAILS = [
    "Anuj Singh <anuj@unpod.ai>",
    "Parvinder Singh <parvinder@recalll.co>",
]

MONGO_DB = env("MONGO_DB", default="messaging_service")
MONGO_DSN = env("MONGO_DSN")

DEEPGRAM_API_KEY = env("DEEPGRAM_API_KEY")
ELEVENLABS_API_KEY = env("ELEVENLABS_API_KEY")
GROQ_API_KEY = env("GROQ_API_KEY")
OPENAI_API_KEY = env("OPENAI_API_KEY")
LMNT_API_KEY = env("LMNT_API_KEY")
SARVAM_API_KEY = env("SARVAM_API_KEY")
CARTESIA_API_KEY = env("CARTESIA_API_KEY")
INWORLD_API_KEY = env("INWORLD_API_KEY")

SPECTACULAR_SETTINGS = {
    "TITLE": "Unpod API V2 Platform",
    "DESCRIPTION": "OpenAPI 3.0 specification for Unpod Platform APIs",
    "VERSION": "2.0.0",
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
    "SERVERS": [
        {"url": "https://qa.unpod.tv", "description": "QA server"},
        {"url": "https://unpod.dev", "description": "Production server"},
        {"url": "https://unpod.ai", "description": "Production server (AI)"},
    ],
    "SCHEMA_PATH_PREFIX": "/api/v2/platform",
    "SCHEMA_PATH_PREFIX_TRIM": True,
    "SCHEMA_PATH_PREFIX_INSERT": "/api/v2/platform",
    "COMPONENT_SPLIT_REQUEST": True,
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "persistAuthorization": True,
        "displayOperationId": True,
    },
    "APPEND_COMPONENTS": {
        "securitySchemes": {
            "jwtAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "Authorization",
                "description": "JWT Authorization header. Example: 'JWT <token>'",
            }
        }
    },
    "SECURITY": [{"jwtAuth": []}],
    "PREPROCESSING_HOOKS": ["unpod.common.schema.filter_v2_platform_endpoints"],
    "POSTPROCESSING_HOOKS": [],
    "SERVE_INCLUDE_SCHEMA": False,
    "SORT_OPERATIONS": False,  # do not auto-sort
    "SORT_COMPONENTS": False,  # keep serializer order
}

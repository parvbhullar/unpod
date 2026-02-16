# flake8: noqa
import ssl
from .base import *  # noqa
from .base import env

ENABLE_DEBUG_TOOLBAR = env.bool("ENABLE_DEBUG_TOOLBAR", default=False)

DEBUG = False
SECRET_KEY = env("DJANGO_SECRET_KEY")

ALLOWED_HOSTS = [
    "localhost",
    "0.0.0.0",
    "127.0.0.1",
    "unpod.tv",
    "unpod.ai",
    "unpod.dev",
]

ENV_NAME = "Prod"

BASE_URL = os.environ.get("BASE_URL", "https://unpod.ai")

BASE_FRONTEND_URL = os.environ.get("BASE_FRONTEND_URL", "https://unpod.ai")


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
        "ENGINE": env("DB_ENGINE", default="django.db.backends.postgresql"),
        "NAME": env("POSTGRES_DB", default="unpod_prod"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": env("POSTGRES_HOST"),
        "PORT": env("POSTGRES_PORT", default="5432"),
        "CONN_MAX_AGE": env.int("CONN_MAX_AGE", default=60),
        "CONN_HEALTH_CHECKS": True,  # Django 5.1+ - detects stale connections to prevent 504s
        "ATOMIC_REQUESTS": True,
    }
}

# # SECURITY
# # ------------------------------------------------------------------------------
# # https://docs.djangoproject.com/en/dev/ref/settings/#secure-proxy-ssl-header
# SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# # https://docs.djangoproject.com/en/dev/ref/settings/#secure-ssl-redirect
# SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
# # https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-secure
# SESSION_COOKIE_SECURE = True
# # https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-secure
# CSRF_COOKIE_SECURE = True
# # https://docs.djangoproject.com/en/dev/topics/security/#ssl-https
# # https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-seconds
# # TODO: set this to 60 seconds first and then to 518400 once you prove the former works
# SECURE_HSTS_SECONDS = 60
# # https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-include-subdomains
# SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool(
#     "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True
# )
# # https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-preload
# SECURE_HSTS_PRELOAD = env.bool("DJANGO_SECURE_HSTS_PRELOAD", default=True)
# # https://docs.djangoproject.com/en/dev/ref/middleware/#x-content-type-options-nosniff
# SECURE_CONTENT_TYPE_NOSNIFF = env.bool(
#     "DJANGO_SECURE_CONTENT_TYPE_NOSNIFF", default=True
# )

if ENABLE_DEBUG_TOOLBAR:
    INSTALLED_APPS += ["debug_toolbar"]  # noqa F405
    # https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#middleware
    MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]  # noqa F405
    # https://django-debug-toolbar.readthedocs.io/en/latest/configuration.html#debug-toolbar-config
    DEBUG_TOOLBAR_CONFIG = {
        "DISABLE_PANELS": ["debug_toolbar.panels.redirects.RedirectsPanel"],
        "SHOW_TEMPLATE_CONTEXT": True,
    }

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s "
            "%(process)d %(thread)d %(message)s"
        }
    },
    "handlers": {
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {"level": "INFO", "handlers": ["console"]},
    "loggers": {
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "INFO",
            "propagate": True,
        },
        "django.security.DisallowedHost": {
            "level": "INFO",
            "handlers": ["console", "mail_admins"],
            "propagate": True,
        },
    },
}

ssl._create_default_https_context = ssl._create_unverified_context

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


INTERNAL_IPS = ["127.0.0.1", "157.245.151.185"]

JWT_AUTH.update(
    {
        "JWT_SECRET_KEY": SECRET_KEY,
    }
)

MUX_TOKEN_ID = env("MUX_TOKEN_ID")
MUX_TOKEN_SECRET = env("MUX_TOKEN_SECRET")

SSL_CERT_PATH = "/var/www/unpod-prod/ssl/unpod-tv-chain.pem"

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


AGORA_AUTH = {"username": AGORA_AUTH_ID, "password": AGORA_AUTH_SECRET}

AWS_SITEMAP_DIR = "production/sitemaps"

RAZORPAY_KEY = env("RAZORPAY_KEY")
RAZORPAY_SECERT = env("RAZORPAY_SECRET")

DAILY_REPORT_EMAILS = [
    "Anuj Singh <anuj@unpod.ai>",
    "Parvinder Singh <parvinder@recalll.co>",
]

# MONGO_DB = "messaging_service"
# MONGO_DSN = "mongodb+srv://unpodProd:M7zdkcwBLR4ft7sG@unpod-messaging-prod.n40pumx.mongodb.net/?retryWrites=true&w=majority&tlsAllowInvalidCertificates=true"
MONGO_DB = env("MONGO_DB", default="messaging_service_prod")
MONGO_DSN = env("MONGO_DSN")


DEEPGRAM_API_KEY = env("DEEPGRAM_API_KEY")
ELEVENLABS_API_KEY = env("ELEVENLABS_API_KEY")
GROQ_API_KEY = env("GROQ_API_KEY")
OPENAI_API_KEY = env("OPENAI_API_KEY")
LMNT_API_KEY = env("LMNT_API_KEY")
SARVAM_API_KEY = env("SARVAM_API_KEY")
CARTESIA_API_KEY = env("CARTESIA_API_KEY")
INWORLD_API_KEY = env("INWORLD_API_KEY")

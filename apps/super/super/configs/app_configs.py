import json
import os
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

#####
# App Configs
#
#####
APP_HOST = "0.0.0.0"
APP_PORT = 8080
# API_PREFIX is used to prepend a base path for all API routes
# generally used if using a reverse proxy which doesn't support stripping the `/api`
# prefix from requests directed towards the API server. In these cases, set this to `/api`
APP_API_PREFIX = os.environ.get("API_PREFIX", "")


#####
# User Facing Features Configs
#####
BLURB_SIZE = 128  # Number Encoder Tokens included in the chunk blurb
GENERATIVE_MODEL_ACCESS_CHECK_FREQ = int(
    os.environ.get("GENERATIVE_MODEL_ACCESS_CHECK_FREQ") or 86400
)  # 1 day
DISABLE_GENERATIVE_AI = os.environ.get("DISABLE_GENERATIVE_AI", "").lower() == "true"


#####
# Web Configs
#####
# WEB_DOMAIN is used to set the redirect_uri after login flows
# NOTE: if you are having problems accessing the Unpod web UI locally (especially
# on Windows, try  setting this to `http://127.0.0.1:3000` instead and see if that
# fixes it)
WEB_DOMAIN = os.environ.get("WEB_DOMAIN") or "http://localhost:3000"

# Encryption key secret is used to encrypt connector credentials, api keys, and other sensitive
# information. This provides an extra layer of security on top of Postgres access controls
# and is available in Unpod EE
ENCRYPTION_KEY_SECRET = os.environ.get("ENCRYPTION_KEY_SECRET")

# Turn off mask if admin users should see full credentials for data connectors.
MASK_CREDENTIAL_PREFIX = (
    os.environ.get("MASK_CREDENTIAL_PREFIX", "True").lower() != "false"
)

SESSION_EXPIRE_TIME_SECONDS = int(
    os.environ.get("SESSION_EXPIRE_TIME_SECONDS") or 86400 * 7
)  # 7 days

# set `VALID_EMAIL_DOMAINS` to a comma seperated list of domains in order to
# restrict access to Unpod to only users with emails from those domains.
# E.g. `VALID_EMAIL_DOMAINS=example.com,example.org` will restrict Unpod
# signups to users with either an @example.com or an @example.org email.
# NOTE: maintaining `VALID_EMAIL_DOMAIN` to keep backwards compatibility
_VALID_EMAIL_DOMAIN = os.environ.get("VALID_EMAIL_DOMAIN", "")
_VALID_EMAIL_DOMAINS_STR = (
    os.environ.get("VALID_EMAIL_DOMAINS", "") or _VALID_EMAIL_DOMAIN
)
VALID_EMAIL_DOMAINS = (
    [domain.strip() for domain in _VALID_EMAIL_DOMAINS_STR.split(",")]
    if _VALID_EMAIL_DOMAINS_STR
    else []
)
# OAuth Login Flow
# Used for both Google OAuth2 and OIDC flows
OAUTH_CLIENT_ID = (
    os.environ.get("OAUTH_CLIENT_ID", os.environ.get("GOOGLE_OAUTH_CLIENT_ID")) or ""
)
OAUTH_CLIENT_SECRET = (
    os.environ.get("OAUTH_CLIENT_SECRET", os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET"))
    or ""
)

USER_AUTH_SECRET = os.environ.get("USER_AUTH_SECRET", "")
# for basic auth
REQUIRE_EMAIL_VERIFICATION = (
    os.environ.get("REQUIRE_EMAIL_VERIFICATION", "").lower() == "true"
)
SMTP_SERVER = os.environ.get("SMTP_SERVER") or "smtp.gmail.com"
SMTP_PORT = int(os.environ.get("SMTP_PORT") or "587")
SMTP_USER = os.environ.get("SMTP_USER", "your-email@gmail.com")
SMTP_PASS = os.environ.get("SMTP_PASS", "your-gmail-password")
EMAIL_FROM = os.environ.get("EMAIL_FROM") or SMTP_USER


#####
# Search Service Configs
#####
SEARCH_SERVICE_URL = os.environ.get(
    "SEARCH_SERVICE_URL", "http://qa-search-service.co/"
)
AGENTS_SEARCH_API = SEARCH_SERVICE_URL + "/api/v1/search/query/agents/"
DOC_SEARCH_URL = SEARCH_SERVICE_URL + "/api/v1/search/query/docs/"
QUERY_URL = SEARCH_SERVICE_URL + "/api/v1/search/query/"

STORE_SERVICE_URL = os.environ.get("STORE_SERVICE_URL", "http://qa-store-service.co")

# STORE_SERVICE_URL=os.environ.get("STORE_SERVICE_URL","http://qa-store-service.co/")

#####
# Memory Configs
#####
MEMORY_PROVIDER = os.environ.get("MEMORY_PROVIDER", "redis")
MEMORY_SERVICE_HOST = os.environ.get("MEMORY_SERVICE_HOST", "localhost")
MEMORY_SERVICE_PORT = int(os.environ.get("MEMORY_SERVICE_PORT", "9118"))


#####
# Cache Configs
#####
SEARCH_REDIS_URL = os.environ.get("SEARCH_REDIS_URL", "redis://localhost")
SEARCH_REDIS_PORT = int(os.environ.get("SEARCH_REDIS_PORT", "9118"))


#####
# LiteLLM Configs
#####
LITELLM_LOG = os.environ.get("LITELLM_LOG", "INFO")


#####
# Miscellaneous
#####
# File based Key Value store no longer used
DYNAMIC_CONFIG_STORE = "PostgresBackedDynamicConfigStore"

JOB_TIMEOUT = 60 * 60 * 6  # 6 hours default
# used to allow the background indexing jobs to use a different embedding
# model server than the API server
CURRENT_PROCESS_IS_AN_INDEXING_JOB = (
    os.environ.get("CURRENT_PROCESS_IS_AN_INDEXING_JOB", "").lower() == "true"
)
# Logs every model prompt and output, mostly used for development or exploration purposes
LOG_ALL_MODEL_INTERACTIONS = (
    os.environ.get("LOG_ALL_MODEL_INTERACTIONS", "").lower() == "true"
)
# If set to `true` will enable additional logs about Vespa query performance
# (time spent on finding the right docs + time spent fetching summaries from disk)
LOG_VESPA_TIMING_INFORMATION = (
    os.environ.get("LOG_VESPA_TIMING_INFORMATION", "").lower() == "true"
)
LOG_ENDPOINT_LATENCY = os.environ.get("LOG_ENDPOINT_LATENCY", "").lower() == "true"
# Anonymous usage telemetry
DISABLE_TELEMETRY = os.environ.get("DISABLE_TELEMETRY", "").lower() == "true"

TOKEN_BUDGET_GLOBALLY_ENABLED = (
    os.environ.get("TOKEN_BUDGET_GLOBALLY_ENABLED", "").lower() == "true"
)

# Defined custom query/answer conditions to validate the query and the LLM answer.
# Format: list of strings
CUSTOM_ANSWER_VALIDITY_CONDITIONS = json.loads(
    os.environ.get("CUSTOM_ANSWER_VALIDITY_CONDITIONS", "[]")
)

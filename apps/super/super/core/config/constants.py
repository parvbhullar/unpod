"""App constants and configuration."""

import os

_API_SERVICE_URL = os.environ.get("API_SERVICE_URL", "http://0.0.0.0:9116/api/v1").rstrip("/")
AGENTS_SEARCH_API = _API_SERVICE_URL + "/search/query/agents/"
CHUNK_OVERLAP = 128
MINI_CHUNK_SIZE = 256

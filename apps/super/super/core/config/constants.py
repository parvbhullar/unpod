"""App constants and configuration."""

import os

AGENTS_SEARCH_API = (
    os.environ.get("AGENTS_SEARCH_API")
    or "http://0.0.0.0:9118/api/v1/search/query/agents/"
)
CHUNK_OVERLAP = 128
MINI_CHUNK_SIZE = 256

"""Authentication dependencies for messaging service.

Provides OAuth2 scheme and user authentication dependencies.
"""

from libs.api.dependencies import (
    create_oauth2_scheme,
    get_current_user as create_get_current_user,
    validate_websocket_auth as lib_validate_websocket_auth,
)
from libs.api.config import get_settings

# Initialize settings
settings = get_settings()

# Create OAuth2 scheme
reusable_oauth2 = create_oauth2_scheme(settings.API_V1_STR)

# Create get_current_user dependency
get_current_user = create_get_current_user(reusable_oauth2)

# Re-export validate_websocket_auth for convenience
validate_websocket_auth = lib_validate_websocket_auth

"""Shared Authentication and Authorization Dependencies.

Provides common authentication logic for all services.
Services can override the DB query function for their specific database.
"""

from typing import Optional, Dict, Callable
from fastapi.security import OAuth2
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi import WebSocket, status, WebSocketException, Request, Depends
from libs.core.string import string_to_int
from libs.core.security import decode_jwt, get_authorization_scheme_param
from libs.core.exceptions import APICommonException
import time
import json

# Default DB query function (can be overridden by services)
_db_query_func: Optional[Callable] = None


def set_db_query_func(func: Callable):
    """Set the database query function to use for user lookup.

    Args:
        func: Function that executes database queries (e.g., executeQuery, executeMysqlQuery)

    Example:
        from libs.storage.postgres import executeQuery
        set_db_query_func(executeQuery)
    """
    global _db_query_func
    _db_query_func = func


def get_db_query_func():
    """Get the configured database query function.

    Returns:
        Configured query function (auto-loads postgres executeQuery if not set)
    """
    global _db_query_func
    if _db_query_func is None:
        # Auto-load postgres executeQuery as default
        from libs.storage.postgres import executeQuery

        _db_query_func = executeQuery
    return _db_query_func


def setUser(user):
    """Remove JWT-specific fields from user dict."""
    if user:
        user = user.copy()
        user.pop("exp", None)
        user.pop("iat", None)
        user.pop("username", None)
    return user


def full_name(first_name, last_name):
    """Construct full name from first and last name."""
    name = ""
    if first_name:
        name = name + first_name + " "
    if last_name:
        name = name + last_name
    return name


def getCheckUser(token, user, check_db=False, redis_client=None):
    """Verify user from cache or database.

    Args:
        token: JWT token string
        user: Decoded user dict from JWT
        check_db: If True, query database instead of cache
        redis_client: Redis client instance for caching

    Returns:
        User dict or None if not found
    """
    signature = token.split(".")[2]
    email = user["email"]

    if not check_db and redis_client:
        signatureUser = redis_client.get(f"signature:{signature}")
        if signatureUser:
            signatureUser = json.loads(signatureUser)
            return signatureUser
        else:
            return getCheckUser(token, user, True, redis_client)
    else:
        # Query database using configured function
        query_func = get_db_query_func()
        user = query_func("SELECT * FROM users_user WHERE email=%s", (email,))
        if user:
            user = {
                "user_id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "user_token": user["user_token"],
                "is_active": user["is_active"],
                "full_name": full_name(user["first_name"], user["last_name"]),
            }
            if redis_client:
                redis_client.set(f"signature:{signature}", json.dumps(user), ex=60 * 60)
            return user
        return None


def getAnonymousUser(session_user):
    """Create anonymous user dict for unauthenticated sessions.

    Args:
        session_user: Session identifier string

    Returns:
        Anonymous user dict
    """
    user_id = string_to_int(str(session_user))
    return {
        "user_id": user_id,
        "username": "anonymous",
        "email": f"anonymous.{user_id}@unpod.tv",
        "first_name": "Anonymous",
        "last_name": "User",
        "user_token": "ANONYMOUS",
        "is_active": True,
        "full_name": full_name("Anonymous", "User"),
        "is_anonymous": True,
    }


class OAuth2PasswordJWT(OAuth2):
    """OAuth2 password flow with JWT token validation."""

    def __init__(
        self,
        tokenUrl: str,
        scheme_name: Optional[str] = None,
        scopes: Optional[Dict[str, str]] = None,
        description: Optional[str] = None,
        auto_error: bool = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(password={"tokenUrl": tokenUrl, "scopes": scopes})
        super().__init__(
            flows=flows,
            scheme_name=scheme_name,
            auto_error=auto_error,
        )

    async def __call__(self, request: Request) -> Optional[str]:
        param = await validate_auth(request)
        return param


async def validate_token(token):
    """Validate JWT token and check expiration.

    Args:
        token: JWT token string

    Returns:
        Decoded token dict or None if invalid
    """
    try:
        decoded_token = decode_jwt(token)
    except Exception:
        return None
    if decoded_token["exp"] < int(time.time()):
        return None
    return decoded_token


async def validate_auth(request: Request, redis_client=None):
    """Validate authentication from request headers.

    Args:
        request: FastAPI Request object
        redis_client: Redis client for user caching

    Returns:
        User dict

    Raises:
        APICommonException: If authentication fails
    """
    authorization: str = request.headers.get("Authorization")
    session_user = request.query_params.get("session_user")
    if not authorization and session_user:
        return getAnonymousUser(session_user)
    scheme, param = get_authorization_scheme_param(authorization)
    if not authorization or scheme.lower() != "jwt":
        raise APICommonException(
            json.dumps(
                {
                    "status_code": status.HTTP_403_FORBIDDEN,
                    "message": "Invalid AUTH Type",
                }
            )
        )
    user = await validate_token(param)
    if user is None:
        raise APICommonException(
            json.dumps(
                {
                    "status_code": status.HTTP_403_FORBIDDEN,
                    "message": "Invalid Token / User",
                }
            )
        )
    user = getCheckUser(param, user, redis_client=redis_client)
    if user is None:
        raise APICommonException(
            json.dumps(
                {
                    "status_code": status.HTTP_403_FORBIDDEN,
                    "message": "Invalid Token / User",
                }
            )
        )
    return user


async def validate_websocket_auth(websocket: WebSocket, redis_client=None, logger=None):
    """Validate authentication for WebSocket connections.

    Args:
        websocket: FastAPI WebSocket object
        redis_client: Redis client for user caching
        logger: Logger instance for warnings

    Returns:
        User dict

    Raises:
        WebSocketException: If authentication fails
    """
    authorization: str = websocket.headers.get("Authorization")
    chat_token = websocket.query_params.get("token")
    session_user = websocket.query_params.get("session_user")
    param = None
    if authorization:
        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "jwt":
            if logger:
                logger.warning("Invalid AUTH Type")
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION, reason="Invalid AUTH Type"
            )
    elif chat_token:
        param = chat_token
    elif session_user:
        return getAnonymousUser(session_user)
    user = await validate_token(param)
    if user is None:
        if logger:
            logger.warning("Invalid Token / User")
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION, reason="Invalid Token / User"
        )
    user = getCheckUser(param, user, redis_client=redis_client)
    if user is None:
        if logger:
            logger.warning("Invalid Token / User. User Not Found")
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION, reason="Invalid Token / User"
        )
    return user


def create_oauth2_scheme(api_v1_str: str):
    """Create OAuth2 scheme for a service.

    Args:
        api_v1_str: API version string (e.g., "/api/v1")

    Returns:
        OAuth2PasswordJWT instance
    """
    return OAuth2PasswordJWT(tokenUrl=f"{api_v1_str}/login/access-token/")


def get_current_user(oauth2_scheme):
    """Dependency function for getting current user.

    Args:
        oauth2_scheme: OAuth2 scheme instance

    Returns:
        Dependency function
    """

    def _get_current_user(user=Depends(oauth2_scheme)):
        return user

    return _get_current_user

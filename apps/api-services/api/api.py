from fastapi import APIRouter

# Store service endpoints
from services.store_service.api.api_v1.endpoints import store, connector, voice

# Search service endpoints
from services.search_service.api.api_v1.endpoints import search

# Messaging service endpoints
from services.messaging_service.api.api_v1.endpoints import (
    login,
    user,
    conversation,
    agent,
)

# Messaging service WebSocket endpoints
from services.messaging_service.api.websocket.endpoints import (
    conversation as ws_conversation,
)

# Task service endpoints
from services.task_service.api.api_v1.endpoints import task

# --- REST API Router ---
api_router = APIRouter()

# Store
api_router.include_router(store.router, prefix="/store", tags=["Store"])
api_router.include_router(connector.router, prefix="", tags=["Connectors"])
api_router.include_router(voice.router, prefix="/voice", tags=["Voice"])

# Search
api_router.include_router(search.router, prefix="/search", tags=["Search"])

# Messaging
api_router.include_router(
    login.router, prefix="/login", tags=["Login"], include_in_schema=False
)
api_router.include_router(user.router, prefix="/user", tags=["User"])
api_router.include_router(
    conversation.router, prefix="/conversation", tags=["Conversation"]
)
api_router.include_router(agent.router, prefix="/agent", tags=["Agent"])

# Task
api_router.include_router(task.router, prefix="/task", tags=["Task"])

# --- WebSocket Router ---
websocket_router = APIRouter()
websocket_router.include_router(
    ws_conversation.router, prefix="/conversation", tags=["Conversation"]
)

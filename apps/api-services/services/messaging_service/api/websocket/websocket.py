from fastapi import APIRouter
from .endpoints import conversation

websocket_router_v1 = APIRouter()

websocket_router_v1.include_router(
    conversation.router, prefix="/conversation", tags=["Conversation"]
)

"""
Test SDK Server for LiveKit Voice Agent Testing

This server provides:
1. WebSocket endpoint for real-time communication with browser client
2. REST endpoints for creating LiveKit rooms and dispatching agents
3. Token generation for client-side LiveKit connection

The server creates a LiveKit room and generates tokens for both the user (browser)
and signals the existing worker pool agent to join the room.
"""

import json
import logging
import os
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional
from time import perf_counter
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

try:
    from livekit import api as lk_api

    LIVEKIT_AVAILABLE = True
except ImportError:
    LIVEKIT_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURABLE SETTINGS - Edit these values to customize agent dispatch
# =============================================================================

# Agent name registered in LiveKit worker pool
AGENT_NAME = os.getenv("AGENT_NAME", "unpod-local-general-agent-v4")

# Default metadata for agent dispatch - edit these values as needed
DEFAULT_DISPATCH_METADATA = {
    "agent_handle": "developer-38qph836fhp9",
    "contact_name": "Parvinder S",
    "multimodality": "text_audio",
    "space_name": "Test Calls",
    "space_slug": "test-calls-f1o3vprb",
    "space_token": "F1O3QJM1Y7Q1AVVUYNV4VPRB",
    "token": "F1O3QJM1Y7Q1AVVUYNV4VPRB",
}

# =============================================================================


@dataclass
class RoomSession:
    """Track active room sessions"""

    room_name: str
    user_token: str
    agent_dispatched: bool
    created_at: datetime
    user_identity: str
    metadata: Dict[str, Any]


class CreateRoomRequest(BaseModel):
    """Request model for creating a new room"""

    user_name: Optional[str] = "TestUser"
    agent_name: Optional[str] = "voice-agent"
    metadata: Optional[Dict[str, Any]] = None


class CreateRoomResponse(BaseModel):
    """Response model for room creation"""

    room_name: str
    livekit_url: str
    token: str
    user_identity: str


class LiveKitTestSDK:
    """
    LiveKit Test SDK for dispatching calls to voice agents

    This class manages:
    - LiveKit room creation
    - Token generation for users
    - Agent dispatch signaling
    - Session tracking
    """

    def __init__(self):
        self.livekit_url = os.getenv("LIVEKIT_URL", "ws://localhost:7880")
        self.api_key = os.getenv("LIVEKIT_API_KEY", "devkey")
        self.api_secret = os.getenv("LIVEKIT_API_SECRET", "secret")

        self.active_sessions: Dict[str, RoomSession] = {}
        self._lk_api: Optional[lk_api.LiveKitAPI] = None

        if not LIVEKIT_AVAILABLE:
            logger.warning(
                "livekit-python not installed. Some features may be limited."
            )

    async def initialize(self) -> bool:
        """Initialize LiveKit API client"""
        if not LIVEKIT_AVAILABLE:
            return False

        try:
            self._lk_api = lk_api.LiveKitAPI(
                self.livekit_url.replace("ws://", "http://").replace(
                    "wss://", "https://"
                ),
                self.api_key,
                self.api_secret,
            )
            logger.info(f"LiveKit API initialized: {self.livekit_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize LiveKit API: {e}")
            return False

    def generate_room_name(self) -> str:
        """Generate unique room name"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        return f"test-room-{timestamp}-{unique_id}"

    def generate_user_token(
        self,
        room_name: str,
        identity: str,
        name: Optional[str] = None,
        is_agent: bool = False,
    ) -> str:
        """
        Generate LiveKit access token for a participant

        Args:
            room_name: Name of the room to join
            identity: Unique identifier for the participant
            name: Display name for the participant
            is_agent: Whether this token is for an agent

        Returns:
            JWT token string
        """
        if not LIVEKIT_AVAILABLE:
            raise RuntimeError("livekit-python not installed")

        token = lk_api.AccessToken(self.api_key, self.api_secret)
        token.with_identity(identity)
        token.with_name(name or identity)

        grants = lk_api.VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True,
            can_publish_data=True,
        )

        if is_agent:
            grants.agent = True

        token.with_grants(grants)

        return token.to_jwt()

    async def create_room(
        self,
        room_name: Optional[str] = None,
        user_name: str = "TestUser",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RoomSession:
        """
        Create a new LiveKit room and generate user token

        Args:
            room_name: Optional custom room name
            user_name: Display name for the user
            metadata: Optional metadata to attach to the room

        Returns:
            RoomSession with room details and user token
        """
        if room_name is None:
            room_name = self.generate_room_name()

        user_identity = f"user-{uuid.uuid4().hex[:8]}"

        # Create room via LiveKit API if available
        if self._lk_api:
            try:
                room_metadata = json.dumps(metadata) if metadata else None
                create_request = lk_api.CreateRoomRequest(
                    name=room_name,
                    metadata=room_metadata,
                    empty_timeout=300,  # 5 minutes
                    max_participants=10,
                )
                await self._lk_api.room.create_room(create_request)
                logger.info(f"Created LiveKit room: {room_name}")
            except Exception as e:
                logger.warning(
                    f"Could not create room via API (may already exist): {e}"
                )

        # Generate user token
        user_token = self.generate_user_token(
            room_name=room_name, identity=user_identity, name=user_name, is_agent=False
        )

        session = RoomSession(
            room_name=room_name,
            user_token=user_token,
            agent_dispatched=False,
            created_at=datetime.now(),
            user_identity=user_identity,
            metadata=metadata or {},
        )

        self.active_sessions[room_name] = session
        return session

    async def dispatch_agent(
        self,
        room_name: str,
        agent_name: Optional[str] = None,
        metadata_override: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Dispatch agent to join the room using LiveKit explicit dispatch

        Args:
            room_name: Room for agent to join
            agent_name: Agent name in worker pool (defaults to AGENT_NAME)
            metadata_override: Override default metadata values

        Returns:
            True if dispatch was successful
        """
        if room_name not in self.active_sessions:
            logger.error(f"Room {room_name} not found in active sessions")
            return False

        session = self.active_sessions[room_name]
        agent_name = agent_name or AGENT_NAME

        try:
            # Build metadata from defaults + overrides
            dispatch_metadata = DEFAULT_DISPATCH_METADATA.copy()
            if metadata_override:
                dispatch_metadata.update(metadata_override)

            # Add session-specific data
            dispatch_metadata["user_identity"] = session.user_identity
            dispatch_metadata["dispatched_at"] = datetime.now().isoformat()

            metadata_json = json.dumps(dispatch_metadata)

            # Use explicit agent dispatch API
            if self._lk_api:
                dispatch_request = lk_api.CreateAgentDispatchRequest(
                    agent_name=agent_name, room=room_name, metadata=metadata_json
                )
                dispatch = await self._lk_api.agent_dispatch.create_dispatch(
                    dispatch_request
                )
                logger.info(
                    f"Created explicit dispatch for agent '{agent_name}' in room '{room_name}'"
                )
                logger.info(f"Dispatch metadata: {metadata_json}")

            session.agent_dispatched = True
            return True

        except Exception as e:
            logger.error(f"Failed to dispatch agent: {e}")
            return False

    async def get_room_participants(self, room_name: str) -> list:
        """Get list of participants in a room"""
        if not self._lk_api:
            return []

        try:
            response = await self._lk_api.room.list_participants(
                lk_api.ListParticipantsRequest(room=room_name)
            )
            return [
                {
                    "identity": p.identity,
                    "name": p.name,
                    "state": str(p.state),
                    "joined_at": p.joined_at,
                }
                for p in response.participants
            ]
        except Exception as e:
            logger.error(f"Failed to get participants: {e}")
            return []

    async def delete_room(self, room_name: str) -> bool:
        """Delete a room and cleanup session"""
        if room_name in self.active_sessions:
            del self.active_sessions[room_name]

        if self._lk_api:
            try:
                await self._lk_api.room.delete_room(
                    lk_api.DeleteRoomRequest(room=room_name)
                )
                logger.info(f"Deleted room: {room_name}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete room: {e}")
                return False

        return True

    def get_active_sessions(self) -> list:
        """Get all active sessions"""
        return [
            {
                "room_name": s.room_name,
                "user_identity": s.user_identity,
                "agent_dispatched": s.agent_dispatched,
                "created_at": s.created_at.isoformat(),
            }
            for s in self.active_sessions.values()
        ]


# Initialize FastAPI app
app = FastAPI(
    title="LiveKit Voice Agent Test SDK",
    description="Test SDK for voice agent development and testing",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize SDK
sdk = LiveKitTestSDK()


@app.on_event("startup")
async def startup_event():
    """Initialize SDK on startup"""
    await sdk.initialize()
    logger.info("Test SDK server started")


@app.get("/", response_class=HTMLResponse)
async def get_client():
    """Serve the test client HTML page"""
    client_path = os.path.join(os.path.dirname(__file__), "client.html")
    if os.path.exists(client_path):
        return FileResponse(client_path)
    return HTMLResponse(content="<h1>Client not found. Please create client.html</h1>")


@app.post("/api/room/create", response_model=CreateRoomResponse)
async def create_room(request: CreateRoomRequest):
    """
    Create a new LiveKit room and get connection details

    This endpoint:
    1. Creates a new LiveKit room
    2. Generates a token for the user to join
    3. Returns connection details for the browser client
    """
    try:
        session = await sdk.create_room(
            user_name=request.user_name, metadata=request.metadata
        )

        return CreateRoomResponse(
            room_name=session.room_name,
            livekit_url=sdk.livekit_url,
            token=session.user_token,
            user_identity=session.user_identity,
        )
    except Exception as e:
        logger.error(f"Failed to create room: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class DispatchRequest(BaseModel):
    """Request model for agent dispatch"""

    agent_name: Optional[str] = None
    metadata_override: Optional[Dict[str, Any]] = None


@app.post("/api/room/{room_name}/dispatch")
async def dispatch_agent_endpoint(
    room_name: str, request: Optional[DispatchRequest] = None
):
    """
    Dispatch an agent to join the specified room using LiveKit explicit dispatch

    The agent worker pool will receive this dispatch request and
    an agent instance will join the room.

    Body (optional):
        agent_name: Override default agent name
        metadata_override: Override default metadata values
    """
    agent_name = request.agent_name if request else None
    metadata_override = request.metadata_override if request else None

    success = await sdk.dispatch_agent(room_name, agent_name, metadata_override)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to dispatch agent")

    return {
        "status": "dispatched",
        "room_name": room_name,
        "agent_name": agent_name or AGENT_NAME,
        "metadata": {**DEFAULT_DISPATCH_METADATA, **(metadata_override or {})},
    }


@app.get("/api/room/{room_name}/participants")
async def get_participants(room_name: str):
    """Get list of participants in a room"""
    participants = await sdk.get_room_participants(room_name)
    return {"room_name": room_name, "participants": participants}


@app.delete("/api/room/{room_name}")
async def delete_room(room_name: str):
    """Delete a room and cleanup resources"""
    success = await sdk.delete_room(room_name)
    return {"status": "deleted" if success else "failed", "room_name": room_name}


@app.get("/api/sessions")
async def get_sessions():
    """Get all active test sessions"""
    return {"sessions": sdk.get_active_sessions()}


@app.get("/api/config")
async def get_config():
    """Get current SDK configuration"""
    return {
        "livekit_url": sdk.livekit_url,
        "api_available": sdk._lk_api is not None,
        "agent_name": AGENT_NAME,
        "default_metadata": DEFAULT_DISPATCH_METADATA,
    }


@app.put("/api/config/metadata")
async def update_default_metadata(metadata: Dict[str, Any]):
    """Update default dispatch metadata"""
    global DEFAULT_DISPATCH_METADATA
    DEFAULT_DISPATCH_METADATA.update(metadata)
    return {"status": "updated", "metadata": DEFAULT_DISPATCH_METADATA}


# WebSocket connection manager
class ConnectionManager:
    """Manage WebSocket connections for real-time updates"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket connected: {client_id}")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"WebSocket disconnected: {client_id}")

    async def send_message(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)

    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)


manager = ConnectionManager()


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time communication

    Messages:
    - create_room: Create a new room and get connection details
    - dispatch_agent: Signal agent to join room
    - get_participants: Get current room participants
    - ping: Keep-alive ping
    """
    await manager.connect(websocket, client_id)

    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "create_room":
                try:
                    room_creation_start = perf_counter()

                    session = await sdk.create_room(
                        user_name=data.get("user_name", "TestUser"),
                        metadata=data.get("metadata"),
                    )

                    print(
                        f"\n\n{(perf_counter() - room_creation_start) * 1000}ms for room creation api\n\n"
                    )
                    await manager.send_message(
                        client_id,
                        {
                            "type": "room_created",
                            "room_name": session.room_name,
                            "livekit_url": sdk.livekit_url,
                            "token": session.user_token,
                            "user_identity": session.user_identity,
                        },
                    )
                except Exception as e:
                    await manager.send_message(
                        client_id, {"type": "error", "message": str(e)}
                    )

            elif action == "dispatch_agent":
                room_name = data.get("room_name")
                agent_name = data.get("agent_name")  # None uses default AGENT_NAME
                metadata_override = data.get("metadata_override")
                success = await sdk.dispatch_agent(
                    room_name, agent_name, metadata_override
                )
                await manager.send_message(
                    client_id,
                    {
                        "type": "agent_dispatched" if success else "error",
                        "room_name": room_name,
                        "agent_name": agent_name or AGENT_NAME,
                        "success": success,
                    },
                )

            elif action == "get_participants":
                room_name = data.get("room_name")
                participants = await sdk.get_room_participants(room_name)
                await manager.send_message(
                    client_id,
                    {
                        "type": "participants",
                        "room_name": room_name,
                        "participants": participants,
                    },
                )

            elif action == "ping":
                await manager.send_message(client_id, {"type": "pong"})

            else:
                await manager.send_message(
                    client_id, {"type": "error", "message": f"Unknown action: {action}"}
                )

    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(client_id)


def run_server(host: str = "0.0.0.0", port: int = 8765):
    """Run the test SDK server"""
    import uvicorn

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()

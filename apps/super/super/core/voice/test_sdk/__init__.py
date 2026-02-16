"""
LiveKit Voice Agent Test SDK

This module provides tools for testing voice agents with LiveKit:

- WebSocket server for dispatching calls to worker pool agents
- HTML/JS client for browser-based voice interaction
- Utility functions for token generation and room management

Usage:
    # Start the test server
    python -m super.core.voice.test_sdk.server

    # Or programmatically
    from super.core.voice.test_sdk import LiveKitTestSDK, run_server

    sdk = LiveKitTestSDK()
    await sdk.initialize()

    # Create room and get user token
    session = await sdk.create_room(user_name="TestUser")
    print(f"Room: {session.room_name}")
    print(f"Token: {session.user_token}")

    # Dispatch agent to join
    await sdk.dispatch_agent(session.room_name)

Environment Variables:
    LIVEKIT_URL: LiveKit server URL (default: ws://localhost:7880)
    LIVEKIT_API_KEY: LiveKit API key (default: devkey)
    LIVEKIT_API_SECRET: LiveKit API secret (default: secret)
"""

from super.core.voice.test_sdk.server import (
    LiveKitTestSDK,
    RoomSession,
    CreateRoomRequest,
    CreateRoomResponse,
    app,
    run_server,
)

from super.core.voice.test_sdk.utils import (
    LiveKitConfig,
    TokenGrants,
    generate_room_name,
    generate_identity,
    generate_token,
    generate_user_token,
    generate_agent_token,
    create_room,
    delete_room,
    list_rooms,
    get_room_participants,
    send_data_to_room,
    validate_config,
)

__all__ = [
    # Server components
    "LiveKitTestSDK",
    "RoomSession",
    "CreateRoomRequest",
    "CreateRoomResponse",
    "app",
    "run_server",
    # Utility functions
    "LiveKitConfig",
    "TokenGrants",
    "generate_room_name",
    "generate_identity",
    "generate_token",
    "generate_user_token",
    "generate_agent_token",
    "create_room",
    "delete_room",
    "list_rooms",
    "get_room_participants",
    "send_data_to_room",
    "validate_config",
]

import json
from livekit import api
from libs.api.config import get_settings
from libs.api.logger import get_logger

settings = get_settings()
app_logging = get_logger("store_service")


def get_livekit_client():
    """
    Get a LiveKit client.
    """
    return api.LiveKitAPI(
        settings.LIVEKIT_URL,
        api_key=settings.LIVEKIT_API_KEY,
        api_secret=settings.LIVEKIT_API_SECRET,
    )


async def create_explicit_dispatch(room_name, agent_name: str, metadata: dict):
    client = get_livekit_client()
    room = await client.room.create_room(
        api.CreateRoomRequest(
            name=room_name,
            empty_timeout=10 * 60,
            max_participants=20,
        )
    )
    dispatch = await client.agent_dispatch.create_dispatch(
        api.CreateAgentDispatchRequest(
            agent_name=agent_name, room=room_name, metadata=json.dumps(metadata)
        )
    )
    app_logging.info("Dispatch created", str(dispatch))
    return dispatch


async def generate_room_token(room_name, agent_name, metadata, user):
    """
    Generate a token for a room.
    """
    await create_explicit_dispatch(room_name, agent_name, metadata)
    token = (
        api.AccessToken(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
        .with_identity(user.get("user_token"))
        .with_name(user.get("full_name"))
        .with_grants(api.VideoGrants(room_join=True, room=room_name))
    )
    return token.to_jwt()


async def delete_room(room_name):
    """
    Delete a room.
    """
    async with get_livekit_client() as client:
        await client.room.delete_room(
            api.DeleteRoomRequest(
                room=room_name,
            )
        )
    return True


async def list_rooms():
    """
    List all rooms.
    """
    async with api.LiveKitAPI(
        settings.LIVEKIT_URL,
        api_key=settings.LIVEKIT_API_KEY,
        api_secret=settings.LIVEKIT_API_SECRET,
    ) as client:
        rooms = await client.room.list_rooms(api.ListRoomsRequest())
        rooms_list = []
        from google.protobuf.json_format import MessageToDict

        for room in rooms.rooms:
            room_dict = MessageToDict(room)
            rooms_list.append(room_dict)
        return rooms_list

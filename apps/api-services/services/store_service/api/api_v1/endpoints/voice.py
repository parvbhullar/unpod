from fastapi import APIRouter, Request
from pydantic import BaseModel
from libs.api.logger import get_logger
from libs.core.jsondecoder import customResponse

app_logging = get_logger("store_service")
from services.store_service.core.live_kit import (
    delete_room,
    generate_room_token,
    list_rooms,
)
from services.store_service.schemas.response import DynamicResponseModel

router = APIRouter()


class GenerateVoiceTokenRequest(BaseModel):
    room_name: str
    agent_name: str
    metadata: dict
    user: dict


class GenerateVoiceTokenResponse(BaseModel):
    token: str
    room_name: str
    agent_name: str


@router.post(
    "/genrate_voice_token/",
    response_model=DynamicResponseModel[GenerateVoiceTokenResponse],
)
async def generate_persona(data: GenerateVoiceTokenRequest, request: Request):
    token = await generate_room_token(
        data.room_name, data.agent_name, data.metadata, data.user
    )
    res = {
        "token": token,
        "room_name": data.room_name,
        "agent_name": data.agent_name,
    }
    return customResponse({"message": "Token generated successfully", "data": res})


@router.delete("/delete_voice_room/{room_name}/")
async def delete_voice_room(room_name):
    try:
        await delete_room(room_name)
    except Exception as e:
        app_logging.error("Failed to delete voice room", str(e))
    return customResponse({"message": "Room deleted successfully"})


@router.get("/list_voice_rooms/")
async def list_voice_rooms():
    rooms = []
    try:
        rooms = await list_rooms()
    except Exception as e:
        app_logging.error("Failed to list voice rooms", str(e))
    return customResponse({"message": "Rooms listed successfully", "data": rooms})

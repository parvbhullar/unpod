from fastapi import APIRouter, Depends
from services.messaging_service.api.auth import get_current_user
from libs.core.jsondecoder import customResponse
from services.messaging_service.schemas.response import DynamicResponseModel
from services.messaging_service.schemas.user import UserMe

router = APIRouter()


@router.get("/me/", response_model=DynamicResponseModel[UserMe])
def get_user(user: dict = Depends(get_current_user)):
    return customResponse(user)

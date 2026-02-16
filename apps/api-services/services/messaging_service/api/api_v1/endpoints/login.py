from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from services.messaging_service import schemas
from libs.core import security
from services.messaging_service.views.auth import authenticate
from libs.api.config import get_settings

settings = get_settings()
router = APIRouter()


@router.post("/access-token/", response_model=schemas.Token)
def login_auth_token(form_data: OAuth2PasswordRequestForm = Depends()) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = authenticate(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect Username / Email")
    elif not user.get("is_active", None):
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    user = {
        "user_id": user["id"],
        "username": user["username"],
        "email": user["email"],
    }
    return {
        "access_token": security.create_access_token(
            user, expires_delta=access_token_expires
        ),
        "token_type": "jwt",
    }

import os
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from mongomantic import connect, disconnect

os.environ.setdefault("SETTINGS_FILE", "settings.local")
os.environ.setdefault("PROJECT_NAME", "API Service")
os.environ.setdefault("SERVICE_NAME", "api_service")

from libs.api.config import get_settings
from libs.api.logger import get_logger

settings = get_settings()
app_logging = get_logger("api_service")

from api.api import api_router, websocket_router
from libs.core.exceptions import (
    API206Exception,
    APICommonException,
    build_exception_response,
)
from services.messaging_service.core.broadcaster import broadcaster


@asynccontextmanager
async def lifespan(app):
    # Startup
    connect(settings.MONGO_DSN, settings.MONGO_DB)
    app_logging.info("MongoDB connected")
    await broadcaster.connect()
    app_logging.info("Broadcaster connected")
    yield
    # Shutdown
    await broadcaster.disconnect()
    app_logging.info("Broadcaster disconnected")
    disconnect()
    app_logging.info("MongoDB disconnected")


app = FastAPI(
    title=f"{settings.PROJECT_NAME} {settings.ENV_NAME}",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS or ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(websocket_router, prefix=settings.WEBSOCKET_V1_STR)


@app.exception_handler(APICommonException)
def http_exception_handler(request, exc):
    return build_exception_response(exc, 400)


@app.exception_handler(API206Exception)
def http_206_exception_handler(request, exc):
    return build_exception_response(exc, 206)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=9116,
        log_config="config.yaml",
    )

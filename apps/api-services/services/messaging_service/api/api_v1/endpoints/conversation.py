import json
from fastapi import APIRouter, Depends, Request
from pydantic import ValidationError
from services.messaging_service.api.auth import get_current_user
from starlette.responses import JSONResponse
from services.messaging_service.core.block_processor import addTaskToKafka
from libs.core.datetime import get_datetime_now
from libs.core.jsondecoder import customResponse, fetchError
from services.messaging_service.schemas.conversation import BlockCreateSchema, BlockList
from services.messaging_service.schemas.response import (
    DynamicResponseModelWithPagination,
)
from services.messaging_service.schemas.websocket import MessageReceived
from services.messaging_service.views.conversation import (
    createBlockReaction,
    deleteBlock,
    fetchAnswer,
    fetchBlocks,
)
from services.messaging_service.views.websocket import (
    processWebsocketRequest,
    validateBlockId,
    validateThreadId,
)

router = APIRouter()


# fmt: off
@router.get("/{thread_id}/messages/", response_model=DynamicResponseModelWithPagination[BlockList])
def getConversationMessage(thread_id: str, request: Request, user: dict = Depends(get_current_user)):
    post, message = validateThreadId(thread_id, user)
    if not post:
        return JSONResponse({"message": message, "data": {}}, status_code=206)
    data = fetchBlocks(thread_id, request)
    return customResponse(data)


@router.get("/{thread_id}/answer/")
def getAnswerBlock(thread_id: str, request: Request):
    data = fetchAnswer(thread_id)
    return customResponse(data)


@router.put("/{thread_id}/")
def processConversation(thread_id: str, data: MessageReceived, user: dict = Depends(get_current_user)):
    try:
        post, message = validateThreadId(thread_id, user)
        if not post:
            return JSONResponse({"message": message, "data": {}}, status_code=206)
        data = data.dict(exclude_unset=True)
        message_processed = processWebsocketRequest(data, thread_id, user)
        message_processed = {
            **message_processed,
            "timestamp": int(get_datetime_now().timestamp()),
        }
        return message_processed
    except (json.decoder.JSONDecodeError, ValidationError) as ex:
        return_data = {
            "message": "Invalid JSON format",
            "timestamp": int(get_datetime_now().timestamp())
        }
        if isinstance(ex, ValidationError):
            return_data['errors'] = fetchError(ex.errors())
        return JSONResponse(return_data, status_code=206)

@router.post("/{block_id}/reaction/")
def processReaction(block_id: str, data: BlockCreateSchema, request: Request, user: dict = Depends(get_current_user)):
    block = validateBlockId(block_id)
    if not block:
        return JSONResponse({"message": "Invalid block id", "data": {}}, status_code=206)
    data = createBlockReaction(block, data, user)
    return data

@router.delete("/{block_id}/block/")
def processReaction(block_id: str, request: Request, user: dict = Depends(get_current_user)):
    res, error = deleteBlock(block_id, user)
    return customResponse(res, error=error)

@router.post("/{thread_id}/add_task/")
def addTask(thread_id: str, data: MessageReceived, request: Request, user: dict = Depends(get_current_user)):
    data = data.dict(exclude_unset=True)
    if request.headers.get("AppType") and request.headers.get("AppType") == "social":
        if data.get("pilot"):
            data["data"]["data"]["pilot_handle"] = data["pilot"]
        else:
            data["data"]["data"]["pilot_handle"] = "multi-ai"
        data["pilot"] = "multi-ai"
    res = addTaskToKafka(data, thread_id, user)
    return res

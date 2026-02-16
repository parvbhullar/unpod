import json
from fastapi import WebSocket, WebSocketDisconnect
from collections import defaultdict
from libs.core.exceptions import APICommonException
from services.messaging_service.core.broadcaster import broadcaster
from fastapi.concurrency import run_until_first_complete
from libs.core.datetime import get_datetime_now
from libs.core.jsondecoder import MongoJsonEncoder, fetchError
from services.messaging_service.views.websocket import (
    get_source,
    processWebsocketRequest,
    validateThreadId,
)
from services.messaging_service.schemas import MessageReceived
from libs.api.logger import get_logger
from pydantic import ValidationError

app_logging = get_logger("messaging_service")


class ChannelNotifier:
    """
    Manages chat room sessions and members along with message routing
    """

    def __init__(self):
        self.connections = defaultdict(list)
        self.broadcaster = broadcaster

    async def connect(self, websocket: WebSocket, thread_id: str, user):
        await websocket.accept()
        self.connections[thread_id].append(websocket)
        post, message = validateThreadId(thread_id, user)
        if not post:
            return_data = {
                "message": message,
                "timestamp": int(get_datetime_now().timestamp()),
            }
            await websocket.send_json(return_data)
            self.connections[thread_id].remove(websocket)
            await websocket.close(code=1003)
            return

        unique_id = user.get("user_id")
        await run_until_first_complete(
            (
                self.receiver_channel_message,
                {
                    "websocket": websocket,
                    "thread_id": thread_id,
                    "unique_id": unique_id,
                    "user": user,
                },
            ),
            (
                self.send_channel_message,
                {
                    "websocket": websocket,
                    "thread_id": thread_id,
                    "unique_id": unique_id,
                    "user": user,
                },
            ),
        )

    async def receiver_channel_message(
        self, websocket: WebSocket, thread_id: str, unique_id, user
    ):
        async for message in websocket.iter_json():
            try:
                if message.get("event") in ["block"]:
                    message["data"]["data"]["source"] = get_source(websocket)
                data = MessageReceived(**message)
                if websocket.query_params.get("app_type"):
                    if websocket.query_params.get("app_type") == "social":
                        if data.event == "block":
                            data.data.data["pilot_handle"] = data.pilot
                        data.pilot = "multi-ai"
                event = data.event
                if event != "ping":
                    message_processed = processWebsocketRequest(
                        data.dict(), thread_id, user
                    )
                    if message_processed.get("data", {}).get("unsend", False):
                        continue
                    message = {
                        **message_processed,
                        "timestamp": int(get_datetime_now().timestamp()),
                    }
                else:
                    message = {"event": "pong"}
                    await websocket.send_json(message)
                    continue
            except (json.decoder.JSONDecodeError, ValidationError) as ex:
                return_data = {
                    "event": "error",
                    "message": "Invalid JSON format",
                    "timestamp": int(get_datetime_now().timestamp()),
                }
                if isinstance(ex, ValidationError):
                    return_data["errors"] = fetchError(ex.errors())
                await websocket.send_json(return_data)
                await websocket.close(code=1003)
                return
            except APICommonException as ex:
                return_data = {
                    "event": "error",
                    "message": "Invalid JSON format",
                    "timestamp": int(get_datetime_now().timestamp()),
                }
                if len(ex.args):
                    res = ex.args[0]
                else:
                    res = json.loads(str(ex))
                return_data["message"] = res.pop("message", "Error")
                return_data.update(res)
                await websocket.send_json(return_data)
                await websocket.close(code=1003)
                return
            except WebSocketDisconnect:
                app_logging.debug("The connection is closed.")
                return
            message["from_user"] = user.get("user_id")
            message["include_self"] = True
            await self.broadcaster.publish(
                channel=thread_id, message=json.dumps(message, cls=MongoJsonEncoder)
            )

    async def send_channel_message(
        self, websocket: WebSocket, thread_id: str, unique_id, user
    ):
        async with self.broadcaster.subscribe(channel=thread_id) as subscriber:
            async for event in subscriber:
                message = json.loads(event.message)
                include_self = message.pop("include_self", False)
                from_user = message.pop("from_user")
                self_only = message.pop("self_only", False)
                if (
                    (self_only == unique_id)
                    or (include_self and from_user == unique_id)
                    or (from_user != unique_id and not self_only)
                ):
                    try:
                        await websocket.send_json(message)
                    except Exception as ex:
                        app_logging.debug(
                            "The connection is closed in send Json", str(ex)
                        )

    async def _notify(self, message: dict, thread_id: str):
        app_logging.debug(thread_id, message)
        await self.broadcaster.publish(channel=thread_id, message=message)


channel_notifier = ChannelNotifier()

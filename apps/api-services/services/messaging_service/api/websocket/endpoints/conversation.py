from fastapi import APIRouter, WebSocket, Depends
from services.messaging_service.api.auth import validate_websocket_auth
from services.messaging_service.core.notifier import channel_notifier
from typing import Dict

router = APIRouter()


@router.websocket("/{thread_id}/")
async def websocket_endpoint(
    thread_id: str, websocket: WebSocket, user: Dict = Depends(validate_websocket_auth)
):
    await channel_notifier.connect(websocket, thread_id, user)
    # post, message = validateThreadId(thread_id, user)
    # if not post:
    #     return_data = {
    #         "message": message,
    #         "timestamp": int(get_datetime_now().timestamp())
    #     }
    #     await websocket.send_json(return_data)
    #     channel_notifier.remove(websocket, thread_id)
    #     await websocket.close(code=1003)
    #     return
    # while True:
    #     try:
    #         data = await websocket.receive_json()
    #         print(data)
    #         data = MessageReceived(**data)
    #         message_processed = processWebsocketRequest(data.dict(), thread_id, user)
    #         messsage = {
    #                 **message_processed,
    #                 "timestamp": int(get_datetime_now().timestamp()),
    #             }
    #         await channel_notifier._notify(messsage, thread_id)
    #     except (json.decoder.JSONDecodeError, ValidationError) as ex:
    #         return_data = {
    #             "message": "Invalid JSON format",
    #             "timestamp": int(get_datetime_now().timestamp())
    #         }
    #         if type(ex) == ValidationError:
    #             return_data['errors'] = fetchError(ex.errors())
    #         return_data['event'] = 'error'
    #         await websocket.send_json(return_data)
    #         channel_notifier.remove(websocket, thread_id)
    #         await websocket.close(code=1003)
    #         break
    #     except (APICommonException) as ex:
    #         return_data = {
    #             "message": "Invalid JSON format",
    #             "timestamp": int(get_datetime_now().timestamp())
    #         }
    #         if len(ex.args):
    #             res = ex.args[0]
    #         else:
    #             res = json.loads(str(ex))
    #         return_data['message'] = res.pop('message', "Error")
    #         return_data.update(res)
    #         return_data['event'] = 'error'
    #         await websocket.send_json(return_data)
    #         channel_notifier.remove(websocket, thread_id)
    #         await websocket.close(code=1003)
    #         break
    #     except WebSocketDisconnect:
    #         channel_notifier.remove(websocket, thread_id)
    #         print("The connection is closed.")
    #         break

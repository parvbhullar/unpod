from services.messaging_service.core.block_processor import (
    processActionData,
    saveBlockData,
)
from libs.storage.postgres import executeQuery
from services.messaging_service.models.conversation import BlockModel
from libs.api.logger import get_logger

app_logging = get_logger("messaging_service")


SOURCE_DICT = {"https://qa2.unpod.tv": "qa2", "http://localhost:4200": "qa2"}


def get_source(request):
    return "qa2"
    origin = request.headers.get("Origin")
    return SOURCE_DICT.get(origin, "main")


def validatePermission(post, user):
    if post["privacy_type"] == "public":
        return True, "This is a public post"
    else:
        post_per = executeQuery(
            "SELECT * FROM thread_threadpostpermission WHERE post_id=%s AND user_id=%s",
            (post["id"], user["user_id"]),
        )
        return post_per, "You do not have permission to view this post"


def validateThreadId(thread_id, user):
    return True, "Valid Thread Id"
    try:
        thread_id = int(thread_id)
    except Exception as ex:
        return False, "Invalid Thread Id"
    post = executeQuery(
        "SELECT * FROM thread_threadpost WHERE post_id=%s", (thread_id,)
    )
    if post:
        return validatePermission(post, user)
    return False, "Invalid Post Id"


def validateBlockId(block_id):
    block = BlockModel.find_one(block_id=block_id)
    return BlockModel.Meta.model.from_mongo(block)


def processBlockData(data, thread_id, user):
    create_data = saveBlockData(data, thread_id, user)
    create_data.pop("modified", None)
    create_data.pop("id", None)
    return create_data


def processWebsocketEvent(event, data, thread_id, user):
    EVENT_MAP = {"block": processBlockData, "action": processActionData}
    result = EVENT_MAP[event](data, thread_id, user)
    return {"data": result or {}}


def processWebsocketRequest(data, thread_id, user):
    event = data.pop("event")
    event_data = data.pop("data")
    app_logging.debug("event_data", event_data)
    event_data.update(data)
    res = processWebsocketEvent(event, event_data, thread_id, user)
    res = {**res, "event": event}
    return res

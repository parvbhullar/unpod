import json
from libs.core.exceptions import APICommonException
from fastapi.encoders import jsonable_encoder
from services.messaging_service.core.kafka_store import KAFKA_BASE
from libs.core.datetime import get_datetime_now
from libs.core.generator import generateRandomKey
from libs.core.jsondecoder import convertFromBaseModel
from libs.core.message import send_message
from libs.storage.postgres import executeQuery
from libs.storage.redis_storage import REDIS
from libs.storage.s3_url import s3_path_split
from services.messaging_service.models.conversation import (
    BlockModel,
    CheggQuestionSolverLogsModel,
)
from services.messaging_service.core.storage import imagekitBackend
from libs.api.config import get_settings
from libs.api.logger import get_logger

settings = get_settings()
app_logging = get_logger("messaging_service")


def get_superpilotuser():
    return {
        "user_id": "superpilot",
        "full_name": "Superpilot",
        "email": "superpilot@unpod.ai",
    }


def get_pilot(pilot: str):
    return {
        "user_id": pilot,
        "full_name": pilot.replace("-", " ").title(),
        "email": f"{pilot.replace('-', '_')}@unpod.ai",
    }


def send_block_to_channel(thread_id, json_data, user, event="block"):
    message = {
        "event": event,
        "data": json_data,
        "timestamp": int(get_datetime_now().timestamp()),
        "from_user": user["user_id"],
        "self_only": json_data.pop("self_only", False),
        "include_self": json_data.pop("include_self", True),
    }
    send_message(thread_id, message)


def send_metadata(thread_id, json_data, superpilot_user, self_only):
    title_data = {
        "thread_id": thread_id,
        "user_id": superpilot_user.get("user_id"),
        "user": getUser(superpilot_user),
        "block_id": generateRandomKey("", unique=True, length=0),
        "block_type": "metadata",
        "block": "metadata",
        "data": json_data,
        "self_only": self_only,
    }
    send_block_to_channel(thread_id, title_data, superpilot_user)


def getUser(user):
    user = user.copy()
    user.pop("exp", None)
    user.pop("iat", None)
    user.pop("username", None)
    user.pop("email", None)
    user.pop("password", None)
    return user


def get_seq_number(thread_id):
    redis_key = f"{thread_id}_seq_number"
    seq_data = REDIS.get(redis_key)
    if seq_data:
        seq_data = int(seq_data)
        return redis_key, seq_data
    else:
        seq_data = BlockModel.count(thread_id=thread_id)
        return redis_key, seq_data


def get_thread_content(thread_id):
    content = BlockModel._get_collection().find_one(
        {
            "thread_id": thread_id,
            "is_active": True,
            "block_type": {"$ne": "sys_msg"},
        },
        {"data": 1},
        sort=[("_id", -1)],
    )
    if content:
        return content.get("data", {}).get("content", "")
    return ""


def fetch_thread_history(thread_id, last_count=10):
    query = {
        "thread_id": thread_id,
        "is_active": True,
        "block_type": {"$ne": "sys_msg"},
    }
    projection = [
        "user_id",
        "user",
        "block_id",
        "block_type",
        "data",
        "pilot_handle",
        "seq_number",
    ]
    old_messages = BlockModel._get_collection().find(
        query, projection, sort=[("_id", -1)], skip=1, limit=last_count
    )
    return list(old_messages)


def processParent(parent_id):
    from services.messaging_service.views.websocket import validateBlockId

    block = validateBlockId(parent_id)
    parent_data = {}
    if block:
        parent_data_keys = [
            "block_id",
            "block",
            "block_type",
            "data",
            "media",
            "seq_number",
            "created",
            "user_id",
            "user",
        ]
        for key in parent_data_keys:
            if hasattr(block, key) and getattr(block, key):
                parent_data[key] = getattr(block, key)
    return parent_data


def processTextMsg(
    data, thread_id, user, create=True, broadcaster=None, save_file=True
):
    # pilot_handle = data.get("pilot", '')
    block_type = data["block_type"]
    if block_type not in ["notebook"]:
        content = data["data"].get("content", "")
        try:
            content_json = json.loads(content)
            if not content_json:
                data["data"]["content"] = ""
            if "content" in content_json:
                data["data"]["content"] = content_json["content"]
        except Exception as ex:
            pass
    conversation_type = data.get("data", {}).get("conversation_type", "")
    create_data = {
        "thread_id": thread_id,
        "user_id": user.get("user_id"),
        "user": getUser(user),
        "block_id": generateRandomKey("", unique=True, length=0),
        "block_type": data["block_type"],
        "block": data["block"],
        "data": {
            "content": data["data"]["content"],
            "knowledge_bases": data["data"].get("knowledge_bases", []),
        },
        "pilot_handle": data.get("pilot", ""),
    }
    if conversation_type:
        create_data["data"]["conversation_type"] = conversation_type
    if data["data"].get("files", []):
        create_data["data"]["files"] = files_to_block(data["data"].get("files", []))
    if data.get("parent_id"):
        parent_data = processParent(data["parent_id"])
        if len(parent_data):
            create_data["parent_id"] = data["parent_id"]
            create_data["parent"] = parent_data
    redis_key, seq_data = get_seq_number(thread_id)
    create_data["seq_number"] = seq_data + 1
    if create:
        create_data = BlockModel.save_single_to_db(create_data)
        REDIS.set(redis_key, create_data.seq_number)
        executeQuery(
            "UPDATE thread_threadpost SET reply_count = (thread_threadpost.reply_count + 1) WHERE (NOT thread_threadpost.is_deleted AND thread_threadpost.post_id = %s)",
            (thread_id,),
            commit=True,
        )
    create_data = convertFromBaseModel(create_data)
    create_data["data"]["files"] = convert_files_url(
        create_data["data"].get("files", [])
    )
    return create_data


def processVideoMsg(data, thread_id, user, create=True, broadcaster=None):
    media = data["data"].pop("media", {})
    create_data = {
        "thread_id": thread_id,
        "user_id": user.get("user_id"),
        "user": getUser(user),
        "block_id": generateRandomKey("", unique=True, length=0),
        "block_type": data["block_type"],
        "block": data["block"],
        "data": data["data"],
    }
    if data.get("parent_id"):
        parent_data = processParent(data["parent_id"])
        if len(parent_data):
            create_data["parent_id"] = data["parent_id"]
            create_data["parent"] = parent_data
    redis_key, seq_data = get_seq_number(thread_id)
    create_data["seq_number"] = seq_data + 1
    if create:
        create_data = BlockModel.save_single_to_db(create_data)
        REDIS.set(redis_key, create_data.seq_number)
        executeQuery(
            "UPDATE thread_threadpost SET reply_count = (thread_threadpost.reply_count + 1) WHERE (NOT thread_threadpost.is_deleted AND thread_threadpost.post_id = %s)",
            (thread_id,),
            commit=True,
        )
    create_data = convertFromBaseModel(create_data)
    create_data["media"] = media
    send_block_to_channel(thread_id, create_data, user)
    return create_data


def processQuestion(data, thread_id, user, create=True):
    data["data"]["conversation_type"] = "initiate"
    pilot = data.get("pilot", "")
    current_msg = processTextMsg(data, thread_id, user, create, save_file=False)
    kafak_data = {"thread_id": thread_id, "user": user, "data": data}
    kafka_key = "task_queue"
    if pilot in ["multi-ai"]:
        kafka_key = "task_queue_upgrade"
    KAFKA_BASE().push_to_kafka(kafka_key, kafak_data)

    typing_check_key = f"typing_check_key_{thread_id}"
    REDIS.set(typing_check_key, "typing", 2 * 60)
    kafak_data = {
        "thread_id": thread_id,
        "user_id": user.get("user_id"),
        "block_type": data.get("block_type"),
        "include_self": True,
    }
    KAFKA_BASE().push_to_kafka("typing_message_queue", kafak_data)
    return current_msg


def processNotebook(data, thread_id, user, create=True):
    data["data"]["conversation_type"] = "initiate"
    current_msg = processTextMsg(data, thread_id, user, create, save_file=False)
    kafak_data = {"thread_id": thread_id, "user": user, "data": data}
    kafka_quene = "notebook_queue"
    kafka_prefix = settings.KAFKA_TOPIC_BASE_SUPERBOOK
    KAFKA_BASE().push_to_kafka(kafka_quene, kafak_data, kafka_prefix)

    typing_check_key = f"typing_check_key_{thread_id}"
    REDIS.set(typing_check_key, "typing", 2 * 60)
    kafak_data = {
        "thread_id": thread_id,
        "user_id": user.get("user_id"),
        "block_type": data.get("block_type"),
        "include_self": True,
    }
    KAFKA_BASE().push_to_kafka("typing_message_queue", kafak_data)
    return current_msg


def processWrite(data, thread_id, user, create=True):
    kafak_data = {"thread_id": thread_id, "user": user, "data": data}
    KAFKA_BASE().push_to_kafka("task_queue", kafak_data)

    typing_check_key = f"typing_check_key_{thread_id}"
    REDIS.set(typing_check_key, "typing", 2 * 60)
    kafak_data = {
        "thread_id": thread_id,
        "user_id": user.get("user_id"),
        "block_type": data.get("block_type"),
        "include_self": True,
    }
    KAFKA_BASE().push_to_kafka("typing_message_queue", kafak_data)
    return {"unsend": True}


def saveBlockData(data, thread_id, user, create=True):
    data = jsonable_encoder(data)
    block_type = data["block_type"]
    # data['pilot'] = 'question_pilot_01'
    EVENT_MAP = {
        "text_msg": processTextMsg,
        "question": processQuestion,
        "video_msg": processVideoMsg,
        "write": processWrite,
        "notebook": processNotebook,
    }
    try:
        result = EVENT_MAP[block_type](data, thread_id, user, create)
    except KeyError as ex:
        result = {
            "message": "Invalid block based data",
            "exception": str(ex),
            "data": data,
            "status_code": 206,
        }
        raise APICommonException(result)
    return result


def processSaveBlock(block, user, thread_id):
    create_data = {
        "thread_id": thread_id,
        "user_id": user.get("user_id"),
        "user": getUser(user),
        "block_id": generateRandomKey("", unique=True, length=0),
    }
    create_data.update(block)
    redis_key, seq_data = get_seq_number(thread_id)
    create_data["seq_number"] = seq_data + 1
    create_data = BlockModel.save_single_to_db(create_data)
    REDIS.set(redis_key, create_data.seq_number)
    create_data = convertFromBaseModel(create_data)
    return create_data


def addTaskToKafka(data, thread_id, user):
    event_data = data.pop("data", {})
    space_data = event_data.pop("space", {})
    user["space"] = space_data
    event_data.update(data)
    kafka_data = {"thread_id": thread_id, "user": user, "data": event_data}
    kafka_quene = "task_queue"
    kafka_prefix = None
    if event_data.get("block_type") == "notebook":
        kafka_quene = "notebook_queue"
        kafka_prefix = settings.KAFKA_TOPIC_BASE_SUPERBOOK
    pilot = data.get("pilot", "")
    if pilot in ["multi-ai"]:
        kafka_quene = "task_queue_upgrade"
    KAFKA_BASE().push_to_kafka(kafka_quene, kafka_data, prefix=kafka_prefix)
    typing_check_key = f"typing_check_key_{thread_id}"
    REDIS.set(typing_check_key, "typing", 2 * 60)
    kafka_data = {
        "thread_id": thread_id,
        "user_id": user.get("user_id"),
        "block_type": data.get("block_type"),
        "include_self": True,
    }
    KAFKA_BASE().push_to_kafka("typing_message_queue", kafka_data)
    return {"message": "Task added to kafka queue", "data": {"thread_id": thread_id}}


def processActionData(data, thread_id, user):
    action = data.get("action")
    execution_type = data.get("execution_type")
    data_to_push = {"data": {"content": action}, "pilot": "multi-ai"}
    if execution_type:
        data_to_push["data"]["execution_type"] = execution_type
    kafka_data = {"thread_id": thread_id, "user": user, "data": data_to_push}
    kafka_key = "task_queue_upgrade"
    KAFKA_BASE().push_to_kafka(kafka_key, kafka_data)
    typing_check_key = f"typing_check_key_{thread_id}"
    REDIS.set(typing_check_key, "typing", 2 * 60)
    kafka_data = {
        "thread_id": thread_id,
        "user_id": user.get("user_id"),
        "block_type": data.get("block_type"),
        "include_self": True,
    }
    KAFKA_BASE().push_to_kafka("typing_message_queue", kafka_data)
    return {"unsend": True}


def files_to_block(files):
    if not files:
        return []
    if isinstance(files, dict):
        return {"file_type": files["media_type"], "url": files["url"]}
    final_files = []
    for file in files:
        file_data = {"file_type": file["media_type"], "url": file["url"]}
        final_files.append(file_data)
    return final_files


def convert_files_url(files):
    for file in files:
        if file.get("file_type") == "image":
            file_url = file.get("url")
            try:
                bucket_name, key = s3_path_split(file_url)
                file_url = imagekitBackend.generateURL(key)
                file["url"] = file_url
            except Exception as e:
                app_logging.error("S3 Image path split error", e)
    return files


def save_chegg_logs(thread_id, user, user_id, files, response, pilot, status=1):
    data_create = {
        "thread_id": thread_id,
        "user_id": user_id,
        "user": getUser(user),
        "files": files_to_block(files),
        "response": response,
        "pilot": pilot,
    }
    CheggQuestionSolverLogsModel.save_single_to_db(data_create)
    return True


def stop_typing(thread_id):
    typing_check_key = f"typing_check_key_{thread_id}"
    REDIS.set(typing_check_key, "stop_typing", 30)
    return True

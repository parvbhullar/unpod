from super_services.db.services.models.conversations import BlockModel
from super_services.libs.core.redis import REDIS
from super_services.libs.core.generator import generateRandomKey
from super_services.libs.core.jsondecoder import convertFromBaseModel
from super_services.libs.core.datetime import get_datetime_now
from super_services.libs.core.message import send_message

def get_pilot(pilot: str):
    return {
        "user_id": pilot,
        "full_name": pilot.replace("-", " ").title(),
        "email": f"{pilot.replace('-', '_')}@unpod.ai",
    }


def get_seq_number(thread_id):
    redis_key = f"{thread_id}_seq_number"
    seq_data = REDIS.get(redis_key)
    if seq_data:
        seq_data = int(seq_data)
        return redis_key, seq_data
    else:
        seq_data = BlockModel.count(thread_id=thread_id)
        return redis_key, seq_data

def getUser(user):
    user = user.copy()
    user.pop("exp", None)
    user.pop("iat", None)
    user.pop("username", None)
    user.pop("email", None)
    user.pop("password", None)
    return user

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
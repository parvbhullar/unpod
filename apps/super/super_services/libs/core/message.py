import json
from super_services.libs.core.jsondecoder import MongoJsonEncoder
from super_services.libs.core.redis import redisStorage

def send_message(channel, message):
    if isinstance(message, dict):
        message = json.dumps(message, cls=MongoJsonEncoder)
    # print(channel, message)
    return redisStorage.publish(channel, message)

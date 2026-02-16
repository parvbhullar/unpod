import json
from libs.core.jsondecoder import MongoJsonEncoder


def send_message(channel, message, redis_storage=None):
    """
    Send a message to a Redis channel.

    Args:
        channel: Channel name to publish to
        message: Message to send (dict or string)
        redis_storage: Redis storage instance with publish() method

    Returns:
        Result from redis publish operation

    Raises:
        ValueError: If redis_storage is not provided
    """
    if redis_storage is None:
        raise ValueError("redis_storage must be provided")

    if isinstance(message, dict):
        message = json.dumps(message, cls=MongoJsonEncoder)
    # print(channel, message)
    return redis_storage.publish(channel, message)

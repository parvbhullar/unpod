import pickle
from redis import StrictRedis

from super_services.libs.config import settings
from super_services.libs.storage.redis_storage import RedisStorageWrapper

REDIS: StrictRedis = StrictRedis.from_url(
    settings.REDIS_URL,
    socket_timeout=5,
    socket_connect_timeout=5,
)

redisStorage = RedisStorageWrapper(REDIS)


class RedisSerializer:
    def __init__(self, protocol=None):
        self.protocol = pickle.HIGHEST_PROTOCOL if protocol is None else protocol

    def dumps(self, obj):
        if type(obj) is int:
            return obj
        return pickle.dumps(obj, self.protocol)

    def loads(self, data):
        try:
            return int(data)
        except ValueError:
            return pickle.loads(data)


redisSerializer = RedisSerializer()


def redis_key(key, device_id):
    key = f"{settings.REDIS_PREFIX}__"
    key += str(key) + "__"
    if device_id:
        key += str(device_id) + "__"
    key += str(settings.SETTINGS_FILE).split(".")[-1]
    return key


def set_key(key, value, timeout, device_id=None):
    key = redis_key(key, device_id)
    REDIS.set(key, redisSerializer.dumps(value), ex=timeout)
    return True


def get_key(key, device_id=None):
    key = redis_key(key, device_id)
    data = REDIS.get(key)
    if data:
        return redisSerializer.loads(data)
    return None


def delete_key(key, device_id=None):
    key = redis_key(key, device_id)
    REDIS.delete(key)
    return True


def delete_pattern(pattern, device_id=None):
    pattern = redis_key(pattern, device_id)
    pattern = f"{pattern}*"
    pipe = REDIS.pipeline()
    cursor = None
    SCAN_BATCH_SIZE = 5000
    while cursor != 0:
        cursor, keys = REDIS.scan(
            cursor=cursor or 0, match=pattern, count=SCAN_BATCH_SIZE
        )
        if keys:
            pipe.delete(*keys)
    pipe.execute()

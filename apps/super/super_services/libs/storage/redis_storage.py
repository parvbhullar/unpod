import redis
from super_services.libs.core.exceptions import NotFound


REDIS_URL_KEY = "REDIS_URL"


class RedisStorageWrapper:
    """
    Product RedisStorage

    A very simple example of a custom Nameko dependency. Simplified
    implementation of products database based on Redis key value store.

    """

    NotFound = NotFound

    def __init__(self, client):
        self.client: redis.StrictRedis = client

    def _format_key(self, type, id):
        return "{}:{}".format(type, id)

    def _from_hash(self, document):
        return document

    def get(self, _type, key):
        obj = self.client.hgetall(self._format_key(type, key))
        if not obj:
            raise NotFound("Key {} does not exist".format(key))
        else:
            return self._from_hash(obj)

    def list(self, _type):
        keys = self.client.keys(self._format_key(type, "*"))
        for key in keys:
            yield self._from_hash(self.client.hgetall(key))

    def create(self, _type, obj):
        self.client.hmset(self._format_key(_type, obj["id"]), obj)

    def decrement(self, _type, _id, amount):
        return self.client.hincrby(self._format_key(_type, _id), "amount", -amount)

    def publish(self, channel, message):
        return self.client.publish(channel, message)

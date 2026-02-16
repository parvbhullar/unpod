import json
import logging
import uuid
from datetime import datetime

from super.core.memory.kv.base import BaseCache
from super.core.memory.settings import MemoryConfig
from redis.asyncio import Redis  # Updated: Using redis-py's async client


class KVMemory(BaseCache):
    def __init__(
        self,
        memory_config: MemoryConfig,
        logger: logging.Logger = logging.getLogger(__name__),
        *args,
        **kwargs,
    ):
        self._memory = self._initialize_client(memory_config)
        self.logger = logger
        self.key_prefix = memory_config.collection_name or "memory"

    def _initialize_client(self, config: MemoryConfig):
        # Initialize and return a Redis client instance
        if config.provider != "redis":
            raise ValueError(
                f"Invalid provider: {config.provider}. Only 'redis' is supported."
            )
        return Redis.from_url(config.url)

    @property
    def client(self):
        return self._memory

    async def add(self, key, value, ttl=None):
        """
        Add a key-value pair to Redis.
        """
        return await self._memory.set(f"{self.key_prefix}:{key}", value, ex=ttl)

    async def get(self, key):
        """
        Retrieve a value from Redis using a key.
        """
        return await self._memory.get(f"{self.key_prefix}:{key}")

    async def delete(self, key):
        """
        Delete a key-value pair from Redis.
        """
        return await self._memory.delete(f"{self.key_prefix}:{key}")

    async def add_all(self, memories: list, ref_id, metadata=None):
        """
        Add multiple memories to Redis.
        """
        memory_ids = []
        for memory in memories:
            text = memory.get("memory") or memory.get("text") or memory.get("content")
            if text is None:
                continue  # Skip if no text is found
            memory_ref_id = memory.get("ref_id") or ref_id
            doc_metadata = metadata.copy() if metadata else {}
            doc_metadata.update(memory.get("metadata", {}))
            memory_id = self.add(text, memory_ref_id, metadata=doc_metadata)
            memory_ids.append(memory_id)
        return memory_ids

    async def search(self, query, ref_id=None, filters=None):
        """
        Search for memories in Redis.
        """
        if filters is None:
            filters = {}

        # Get all memories associated with ref_id
        if ref_id:
            memory_ids = await self._memory.lrange(f"ref_id:{ref_id}:memories", 0, -1)
        else:
            # Get all memory_ids
            keys = await self._memory.keys("memory:*")
            memory_ids = [key.decode("utf-8").split(":")[1] for key in keys]

        results = []
        for memory_id in memory_ids:
            memory_data = await self._memory.hgetall(
                f"memory:{memory_id.decode('utf-8') if isinstance(memory_id, bytes) else memory_id}"
            )
            # Convert bytes to string
            memory_data = {
                k.decode("utf-8"): v.decode("utf-8") for k, v in memory_data.items()
            }
            memory_text = memory_data.get("memory", "")
            if query.lower() in memory_text.lower():
                # Apply filters
                match = True
                for key, value in filters.items():
                    if memory_data.get(key) != value:
                        match = False
                        break
                if match:
                    results.append(memory_data)
        return results

    async def get_all(self, ref_id, agent_id=None, run_id=None):
        """
        Retrieve all memories associated with a specific ref_id.
        """
        # Get all memory_ids associated with ref_id
        memory_ids = await self._memory.lrange(f"ref_id:{ref_id}:memories", 0, -1)

        memories = []
        for memory_id in memory_ids:
            memory_data = await self._memory.hgetall(
                f"memory:{memory_id.decode('utf-8')}"
            )
            # Convert bytes to string
            memory_data = {
                k.decode("utf-8"): v.decode("utf-8") for k, v in memory_data.items()
            }
            memories.append(memory_data)
        return memories

    async def update(self, memory_id, data):
        """
        Update a specific memory in Redis.
        """
        # Get the current memory data
        current_data = await self._memory.hgetall(f"memory:{memory_id}")
        if current_data:
            # Store the current data in history
            timestamp = datetime.utcnow().isoformat()
            # Serialize current_data
            current_data_serialized = json.dumps(
                {k.decode("utf-8"): v.decode("utf-8") for k, v in current_data.items()}
            )
            await self._memory.lpush(
                f"memory:{memory_id}:history",
                json.dumps({"timestamp": timestamp, "data": current_data_serialized}),
            )
        # Update the memory data
        await self._memory.hset(f"memory:{memory_id}", mapping=data)
        return True

    async def delete_all(self, ref_id, agent_id=None, run_id=None):
        """
        Delete all memories associated with a specific ref_id.
        """
        # Get all memory_ids associated with ref_id
        memory_ids = await self._memory.lrange(f"ref_id:{ref_id}:memories", 0, -1)

        for memory_id in memory_ids:
            # Delete the memory hash
            await self._memory.delete(f"memory:{memory_id.decode('utf-8')}")
        # Delete the ref_id key
        await self._memory.delete(f"ref_id:{ref_id}:memories")

    async def history(self, memory_id):
        """
        Retrieve the history of changes for a specific memory.
        """
        history_list = await self._memory.lrange(f"memory:{memory_id}:history", 0, -1)
        history = []
        for item in history_list:
            # Deserialize the item
            item_data = json.loads(item.decode("utf-8"))
            timestamp = item_data["timestamp"]
            data = json.loads(item_data["data"])
            history.append({"timestamp": timestamp, "data": data})
        return history


if __name__ == "__main__":
    m_conf = MemoryConfig.factory(collection_name="test")

    # Example usage
    s_id = "session_123"
    vector_state = KVMemory(s_id, m_conf)

    # Adding memory data
    vector_state.add(
        "Likes to play cricket on weekends",
        ref_id="alice",
        metadata={"category": "hobbies"},
    )

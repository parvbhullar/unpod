import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, AsyncIterator, Dict, Optional
import typing
import redis.asyncio as redis
from libs.api.config import get_settings

settings = get_settings()


class Event:
    def __init__(self, channel: str, message: str) -> None:
        self.channel = channel
        self.message = message

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Event)
            and self.channel == other.channel
            and self.message == other.message
        )

    def __repr__(self) -> str:
        return f"Event(channel={self.channel!r}, message={self.message!r})"


class Unsubscribed(Exception):
    pass


class RedisBackend:
    def __init__(self, url: str):
        self._url = url
        self._pub_conn = None
        self._sub_conn = None
        self._pubsub = None

    async def connect(self) -> None:
        # Create separate connections for publishing and subscribing
        self._pub_conn = await redis.from_url(
            self._url, encoding="utf-8", decode_responses=True
        )
        self._sub_conn = await redis.from_url(
            self._url, encoding="utf-8", decode_responses=True
        )
        self._pubsub = self._sub_conn.pubsub()

    async def disconnect(self) -> None:
        if self._pubsub:
            await self._pubsub.close()
        if self._pub_conn:
            await self._pub_conn.close()
        if self._sub_conn:
            await self._sub_conn.close()

    async def subscribe(self, channel: str) -> None:
        await self._pubsub.subscribe(channel)

    async def unsubscribe(self, channel: str) -> None:
        await self._pubsub.unsubscribe(channel)

    async def publish(self, channel: str, message: typing.Any) -> None:
        await self._pub_conn.publish(channel, message)

    async def next_published(self) -> Event:
        # Check if there are any active channels subscribed
        if not self._pubsub.channels:
            # No subscriptions yet, return None to avoid RuntimeError
            await asyncio.sleep(0.1)  # Small delay to avoid busy waiting
            return None

        message = await self._pubsub.get_message(
            ignore_subscribe_messages=True, timeout=1.0
        )
        if message and message["type"] == "message":
            return Event(channel=message["channel"], message=message["data"])
        return None


class Broadcast:
    def __init__(self, url: str):
        self._subscribers: Dict[str, Any] = {}
        self._backend = RedisBackend(url)

    async def __aenter__(self) -> "Broadcast":
        await self.connect()
        return self

    async def __aexit__(self, *args: Any, **kwargs: Any) -> None:
        await self.disconnect()

    async def connect(self) -> None:
        await self._backend.connect()
        self._listener_task = asyncio.create_task(self._listener())

    async def disconnect(self) -> None:
        if self._listener_task.done():
            self._listener_task.result()
        else:
            self._listener_task.cancel()
        await self._backend.disconnect()

    async def _listener(self) -> None:
        while True:
            event = await self._backend.next_published()
            if event is not None:
                for queue in list(self._subscribers.get(event.channel, [])):
                    await queue.put(event)

    async def publish(self, channel: str, message: Any) -> None:
        await self._backend.publish(channel, message)

    @asynccontextmanager
    async def subscribe(self, channel: str) -> AsyncIterator["Subscriber"]:
        queue: asyncio.Queue = asyncio.Queue()

        try:
            if not self._subscribers.get(channel):
                await self._backend.subscribe(channel)
                self._subscribers[channel] = set([queue])
            else:
                self._subscribers[channel].add(queue)

            yield Subscriber(queue)

            self._subscribers[channel].remove(queue)
            if not self._subscribers.get(channel):
                del self._subscribers[channel]
                await self._backend.unsubscribe(channel)
        finally:
            await queue.put(None)


class Subscriber:
    def __init__(self, queue: asyncio.Queue) -> None:
        self._queue = queue

    async def __aiter__(self) -> Optional[AsyncGenerator]:
        try:
            while True:
                yield await self.get()
        except Unsubscribed:
            pass

    async def get(self) -> Event:
        item = await self._queue.get()
        if item is None:
            raise Unsubscribed()
        return item


broadcaster = Broadcast(settings.REDIS_URL)

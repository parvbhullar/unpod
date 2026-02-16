class FakeRoom:
    """Minimal EventEmitter-style fake room for unit tests."""

    def __init__(self):
        self._handlers = {}

    def on(self, event):
        def _register(fn):
            self._handlers.setdefault(event, []).append(fn)
            return fn

        return _register

    def emit(self, event, *args, **kwargs):
        for fn in self._handlers.get(event, []):
            fn(*args, **kwargs)


class FakeEventBridge:
    """Minimal fake bridge that records published payloads."""

    def __init__(self):
        self.published = []

    async def publish_data(
        self,
        data,
        topic="message",
        reliable=True,
        destination_identities=None,
    ):
        self.published.append(
            {
                "data": data,
                "topic": topic,
                "reliable": reliable,
                "destination_identities": destination_identities,
            }
        )
        return True

    def record_publish(self, data, topic):
        self.published.append({"data": data, "topic": topic})
        return True

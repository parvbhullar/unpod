import abc
import logging

from super.core.context.schema import Context


class BaseState(abc.ABC):
    @abc.abstractmethod
    def __init__(self, *args, **kwargs):
        ...

    @abc.abstractmethod
    async def save(self, context: Context) -> None:
        ...

    @abc.abstractmethod
    async def load(self) -> Context:
        ...


class State(BaseState):
    def __init__(
        self,
        logger: logging.Logger = logging.getLogger(__name__),
        context: Context = None,
        *args,
        **kwargs,
    ):
        self._logger = logger
        self._context = (
            context
            if context is not None
            else Context(kwargs.get("session_id", "session-id-1"))
        )

    async def save(self, context: Context) -> None:
        self._context = context

    async def load(self) -> Context:
        return self._context

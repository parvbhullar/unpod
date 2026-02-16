import logging
import pickle
from super.core.context.schema import Context
from super.core.memory.settings import MemoryConfig, MemoryProviders
from super.core.memory.vector import VectorMemory
from super.core.state.base import BaseState


class VectorState(BaseState):
    def __init__(
        self,
        session_id: str,
        logger: logging.Logger = logging.getLogger(__name__),
        *args,
        **kwargs,
    ):
        super().__init__(logger, *args, **kwargs)
        self._session_id = session_id
        m_conf = MemoryConfig.factory(
            collection_name="session_context",
            provider=kwargs.get("provider", MemoryProviders.REDIS.value),
            host=kwargs.get("host", "redis://localhost"),
            port=kwargs.get("port", None),
            # TODO load store config from environment variables
        )

        self._memory = VectorMemory(m_conf, logger=logger)
        self.logger = logger

    def set_session_id(self, session_id: str) -> None:
        self._session_id = session_id

    async def save(self, context: Context) -> None:
        """Save context and state data directly to the memory vector store."""
        # Clear existing context for this session ID
        await self._memory.delete_all(ref_id=self._session_id)
        # Save context in memory
        await self._memory.add_all(
            context.to_memories(), ref_id=self._session_id, metadata={}
        )
        self.logger.debug(f"Context saved for session ID: {self._session_id}")

    async def load(self) -> Context:
        """Load the context directly from the memory vector store."""
        # Retrieve context for this session ID
        results = await self._memory.get_all(ref_id=self._session_id)

        # If a result is found, we will parse it back to Context (assuming it's serialized to string or JSON)
        state = Context.from_memories(self._session_id, results)
        return state

    async def clear(self) -> None:
        """Clear the context and state data from the memory vector store."""
        await self._memory.delete_all(ref_id=self._session_id)
        self.logger.debug(f"Context cleared for session ID: {self._session_id}")

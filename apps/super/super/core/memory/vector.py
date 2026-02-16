import logging
from mem0 import Memory

from super.core.memory.base import BaseMemory
from super.core.memory.settings import MemoryConfig


class VectorMemory(BaseMemory):
    def __init__(
        self,
        memory_config: MemoryConfig,
        logger: logging.Logger = logging.getLogger(__name__),
        *args,
        **kwargs,
    ):
        self._memory = Memory.from_config(memory_config.get_config())
        self.logger = logger

    async def add(self, memory, ref_id, metadata=None):
        """
        Add a memory to the mem0 vector store.
        """
        if not isinstance(memory, str):
            memory = memory.get("text") or memory.get("content")
        if memory is None:
            raise ValueError("Memory must have a 'text' or 'content' field.")

        added_memory = self._memory.add(memory, user_id=ref_id, metadata=metadata)
        return added_memory

    async def add_all(self, memories: list, ref_id, metadata=None):
        """
        Add multiple memories to the mem0 vector store.
        """
        documents = []
        for memory in memories:
            text = memory.get("memory") or memory.get("text") or memory.get("content")
            if text is None:
                continue  # Skip if no text is found
            ref_id = memory.get("ref_id") or ref_id
            doc_metadata = metadata.copy() if metadata else {}
            doc_metadata.update(memory.get("metadata", {}))
            document = self.add(text, ref_id, metadata=doc_metadata)
            documents.append(document)
        return documents

    async def search(self, query, ref_id=None, filters=None):
        """
        Search for memories in the mem0 vector store.
        """
        if filters is None:
            filters = {}
        results = self._memory.search(query=query, user_id=ref_id, filters=filters)
        return results

    async def get_all(self, ref_id, agent_id=None, run_id=None):
        """
        Retrieve all memories associated with a specific ref_id.
        """
        memories = self._memory.get_all(
            user_id=ref_id, agent_id=agent_id, run_id=run_id
        )
        return memories

    async def update(self, memory_id, data):
        """
        Update a specific memory in the mem0 vector store.
        """
        updated_memory = self._memory.update(document_id=memory_id, data=data)
        return updated_memory

    async def delete_all(self, ref_id, agent_id=None, run_id=None):
        """
        Delete all memories associated with a specific ref_id.
        """
        # filters = {'ref_id': ref_id}
        self._memory.delete_all(user_id=ref_id, agent_id=agent_id, run_id=run_id)

    async def history(self, memory_id):
        """
        Retrieve the history of changes for a specific memory.
        """
        history = self._memory.history(memory_id=memory_id)
        return history


if __name__ == "__main__":
    m_conf = MemoryConfig.factory(collection_name="test")
    # m_conf = MemoryConfig.factory(
    #     url="http://localhost:6333",
    #     username="",
    #     password="",
    #     collection_name="test"
    # )

    # Example usage
    s_id = "session_123"
    vector_state = VectorMemory(s_id, m_conf)

    # Adding memory data
    vector_state.add(
        "Likes to play cricket on weekends",
        ref_id="alice",
        metadata={"category": "hobbies"},
    )

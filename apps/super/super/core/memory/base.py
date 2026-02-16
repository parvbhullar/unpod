from abc import ABC, abstractmethod


class BaseMemory(ABC):
    @abstractmethod
    def add(self, memory, ref_id, metadata=None):
        """
        Add a memory.
        Args:
            memory (dict): Memory to add.
            ref_id (str): ID of the memory to retrieve.
            metadata (dict): Metadata to store with the memory

        Returns:
            dict: Retrieved memory.
        """
        pass

    @abstractmethod
    def add_all(self, memories: list, ref_id):
        """
        Add multiple memories.
        Args:
            memories (list): List of memories to add.
            ref_id (str): ID of the memory to retrieve.

        Returns:
            dict: Retrieved memory.
        """
        pass

    @abstractmethod
    def search(self, query, ref_id=None, filters=None):
        """
        Search for memories.

        Args:
            query (str): Query to search for.
            ref_id (str): Reference ID to search for.
            filters (dict): Filters to apply to the search.

        Returns:
            list: List of memories.
        """
        pass

    @abstractmethod
    def get_all(self, ref_id):
        """
        List all memories.
        Args:
            ref_id (str): ID of the memory to retrieve.
        Returns:
            list: List of all memories.
        """
        pass

    @abstractmethod
    def update(self, memory_id, data):
        """
        Update a memory by ID.

        Args:
            memory_id (str): ID of the memory to update.
            data (dict): Data to update the memory with.

        Returns:
            dict: Updated memory.
        """
        pass

    @abstractmethod
    def delete_all(self, ref_id):
        """
        Delete all memories by ID.

        Args:
            ref_id (str): ID of the memory to delete.
        """
        pass

    @abstractmethod
    def history(self, ref_id):
        """
        Get the history of changes for a memory by ID.

        Args:
            ref_id (str): ID of the memory to get history for.

        Returns:
            list: List of changes for the memory.
        """
        pass


class MemoryItem(ABC):
    pass


class MessageHistory(ABC):
    pass

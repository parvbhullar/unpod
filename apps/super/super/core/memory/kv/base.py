from abc import ABC, abstractmethod


class BaseCache(ABC):
    @abstractmethod
    def add(self, key, value, ttl=None):
        """
        Add a key, value.
        Args:
            key (str): Memory ID.
            value (dict): Memory to add.
            ttl (int): Time to live in seconds.

        Returns:
            dict: Added value
        """
        pass

    @abstractmethod
    def get(self, key):
        """
        Get a memory by key.

        Args:
            key (str): ID of the memory to update.

        Returns:
            memory.
        """
        pass

    @abstractmethod
    def delete(self, key):
        """
        Delete a memory by ID.

        Args:
            key (str): ID of the memory to update.

        Returns:
            deleted memory.
        """
        pass


class MemoryItem(ABC):
    pass


class MessageHistory(ABC):
    pass

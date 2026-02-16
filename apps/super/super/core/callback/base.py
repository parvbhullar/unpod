from abc import ABC, abstractmethod
from typing import Optional

import inflection

from super.core.context.schema import Message


class BaseCallback(ABC):
    """Base class for message callbacks.

    Provides a standardized interface for sending and receiving messages
    with optional thread_id for persistence.
    """

    @abstractmethod
    async def send(self, message: Message, thread_id: Optional[str] = None) -> None:
        """Send a message through the callback.

        Args:
            message: The Message object to send
            thread_id: Optional thread ID for persistence
        """
        ...

    @abstractmethod
    async def receive(self, message: Message) -> None:
        """Receive and store a user's message.

        Args:
            message: The Message object received from the user
        """
        ...

    # @abstractmethod
    # async def on_chain_start(self, *args, **kwargs):
    #     ...
    #
    # @abstractmethod
    # async def on_pilot_execute(self, *args, **kwargs):
    #     ...
    #
    # @abstractmethod
    # async def on_ability_perform(self, *args, **kwargs):
    #     ...
    #
    # @abstractmethod
    # async def on_info(self, *args, **kwargs):
    #     ...
    #
    # async def on_execution(self, *args, **kwargs):
    #     pass
    #
    # async def on_observation_start(self, *args, **kwargs):
    #     pass

    @classmethod
    def name(cls) -> str:
        """The name of the ability."""
        return inflection.underscore(cls.__name__)


# Define the Callback class
class DefaultCallback(BaseCallback):
    async def send(
        self, message: Message, thread_id: Optional[str] = None
    ) -> None:
        print(f"Sent: {message}")

    async def receive(self, message: Message) -> None:
        print(f"Received: {message}")

from abc import ABC, abstractmethod
from rest_framework.response import Response


class BaseProvider(ABC):
    """Abstract base class for providers."""

    @abstractmethod
    def auth(self, creds: dict) -> str:
        """Authenticate with the provider using credentials."""
        pass

    @abstractmethod
    def set_inbound(self, config: dict) -> Response:
        """Set up inbound configuration for the provider."""
        pass

    @abstractmethod
    def set_outbound(self, config: dict) -> Response:
        """Set up inbound configuration for the provider."""
        pass

    @abstractmethod
    def update_trunk(self, config: dict) -> Response:
        """Update a trunk configuration for the provider."""
        pass

    @abstractmethod
    def delete_trunk(self, config: dict) -> Response:
        """Delete a trunk configuration for the provider."""
        pass

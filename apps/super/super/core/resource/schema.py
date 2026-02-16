import abc
import enum
from typing import List, Union

from pydantic import ConfigDict, SecretBytes, SecretStr
from pydantic.v1 import SecretField

from super.core.configuration import (
    SystemConfiguration,
    SystemSettings,
    UserConfigurable,
)


class ResourceType(str, enum.Enum):
    """An enumeration of resource types."""

    MODEL = "model"
    MEMORY = "memory"


class ProviderUsage(SystemConfiguration, abc.ABC):
    @abc.abstractmethod
    def update_usage(self, *args, **kwargs) -> None:
        """Update the usage of the resource."""
        ...


class ProviderBudget(SystemConfiguration):
    total_budget: float = UserConfigurable()
    total_cost: float
    remaining_budget: float
    usage: ProviderUsage

    @abc.abstractmethod
    def update_usage_and_cost(self, *args, **kwargs) -> None:
        """Update the usage and cost of the resource."""
        ...


class ProviderCredentials(SystemConfiguration):
    """Struct for credentials."""

    # TODO[pydantic]: The following keys were removed: `json_encoders`.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-config for more information.
    model_config = ConfigDict(
        json_encoders={
            SecretStr: lambda v: v.get_secret_value() if v else None,
            SecretBytes: lambda v: v.get_secret_value() if v else None,
            SecretField: lambda v: v.get_secret_value() if v else None,
        }
    )


class ProviderSettings(SystemSettings):
    resource_type: ResourceType
    credentials: Union[ProviderCredentials, None] = None
    budget: Union[ProviderBudget, None] = None


# Used both by model providers and memory providers
Embedding = List[float]

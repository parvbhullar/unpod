import abc
import logging
from pathlib import Path
import inflection
from super.core.plugin.base import PluginLocation, PluginStorageFormat
from super.core.resource.model_providers import (
    ModelProviderName,
    AIModelName,
)
from typing import ClassVar, List
from super.core.configuration.schema import SystemConfiguration, UserConfigurable
from pydantic import Field
from pprint import pformat
from typing import Dict, Union, Any
import json, enum


class BlockType(str, enum.Enum):
    LLM = "llm"


class BlockConfiguration(SystemConfiguration):
    """Struct for model configuration."""

    location: PluginLocation
    packages_required: List[str] = Field(default_factory=list)
    block_type: str = UserConfigurable()
    metadata: Dict = UserConfigurable()
    seq_order: int = UserConfigurable()
    input_schema: Dict = UserConfigurable()
    output_schema: Dict = UserConfigurable()
    body: str = UserConfigurable()
    id: int = UserConfigurable()

    @classmethod
    def factory(
        cls,
        block_data: Dict[str, Any],
    ) -> "BlockConfiguration":
        return BlockConfiguration(
            id=block_data["id"],
            location=block_data["location"],
            block_type=block_data["block_type"],
            metadata=block_data["metadata"],
            seq_order=block_data["seq_order"],
            input_schema=block_data["input_schema"],
            output_schema=block_data["output_schema"],
            body=block_data["body"],
        )


class Block(abc.ABC):
    """A class representing an pilot block."""

    default_configuration: ClassVar[BlockConfiguration]

    _summary: str = None

    @classmethod
    def name(cls) -> str:
        """The name of the block."""
        return inflection.underscore(cls.__name__)

    @classmethod
    @abc.abstractmethod
    def description(cls) -> str:
        """A detailed description of what the block does."""
        return ""

    @classmethod
    @abc.abstractmethod
    def arguments(cls) -> dict:
        """A dict of arguments in standard json schema format."""
        ...

    @property
    @abc.abstractmethod
    def config(self) -> BlockConfiguration:
        """A dict of config in standard json schema format."""
        ...

    @classmethod
    def required_arguments(cls) -> List[str]:
        """A list of required arguments."""
        return []

    @property
    def summary(self) -> str:
        """A summary of the block result."""
        return self._summary

    @abc.abstractmethod
    async def __call__(self, *args, **kwargs):
        ...

    def __str__(self) -> str:
        return pformat(self.dump)

    @staticmethod
    def _parse_response(response_content: dict) -> dict:
        return {"content": response_content["content"]}

    def dump(self) -> dict:
        return {
            "name": self.name(),
            # "description": self.description(),
            "parameters": {
                "type": "object",
                # "properties": self.config(),
            },
        }

    @classmethod
    def create_block(
        cls,
        block_type: type,  # Assuming you pass the Class itself
        logger: logging.Logger,
        configuration: BlockConfiguration,
    ) -> "Block":
        # Instantiate and return Block
        return block_type(logger=logger, configuration=configuration)


class BlockRegistry(abc.ABC):
    @abc.abstractmethod
    def register_block(
        self, block_name: str, block_configuration: BlockConfiguration
    ) -> None:
        ...

    @abc.abstractmethod
    def list_blocks(self) -> List[str]:
        ...

    @abc.abstractmethod
    def blocks(self) -> List[Block]:
        ...

    @abc.abstractmethod
    def dump_blocks(self) -> List[dict]:
        ...

    @abc.abstractmethod
    def get_block(self, block_name: str) -> Block:
        ...

    @abc.abstractmethod
    async def perform(self, block_name: str, block_args: dict, **kwargs):
        ...


class BlockException(Exception):
    """Base exception for the block subsystem."""

    pass

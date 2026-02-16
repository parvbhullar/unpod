from super.core.block.base import BlockRegistry, Block
from super.core.configuration import Configurable, SystemSettings
import logging
from typing import Dict, List, Any
from super.core.block.base import BlockConfiguration
from super.core.plugin.simple import SimplePluginService


class BlockRegistrySettings(SystemSettings):
    pass


class SimpleBlockRegistry(BlockRegistry, Configurable):
    default_settings = BlockRegistrySettings(
        name="simple_block_registry",
        description="A simple block registry.",
    )

    def __init__(
        self,
        blocks: Dict[str, BlockConfiguration],
        logger: logging.Logger = logging.getLogger("SimpleBlockRegistry"),
        settings: BlockRegistrySettings = default_settings,
    ):
        self._logger = logger
        self._blocks = []
        for (
            block_name,
            block_configuration,
        ) in blocks.items():
            self.register_block(block_name, block_configuration)

    def register_block(
        self, block_name: str, block_configuration: BlockConfiguration
    ) -> None:
        block_class = SimplePluginService.get_plugin(block_configuration.location)
        block_args = {
            "logger": self._logger.getChild(block_name),
            "configuration": block_configuration,
        }
        if block_configuration.packages_required:
            # TODO: Check packages are installed and maybe install them.
            pass

        block = block_class(**block_args)
        self._blocks.append(block)

    def list_blocks(self) -> List[str]:
        return [f"{block.name()}: {block.description()}" for block in self._blocks]

    def dump_blocks(self) -> List[dict]:
        return [block.dump() for block in self._blocks]

    def get_block(self, block_name: str) -> Block:
        for block in self._blocks:
            if block.name() == block_name:
                return block
        raise ValueError(f"Block '{block_name}' not found.")

    async def perform(self, block_name: str, **kwargs):  # -> BlockAction:
        block = self.get_block(block_name)
        return await block(**kwargs)

    def blocks(self) -> List[Block]:
        return self._blocks

    @classmethod
    def factory(cls, json_blocks: List[Dict[str, Any]]):
        """
        Loads blocks from JSON data and registers them in the block registry.
        """
        blocks = {}
        for block in json_blocks:
            b = BlockConfiguration.factory(block)
            blocks[str(b.id)] = b

        return cls(blocks)

import asyncio
import logging
from typing import List, Dict, Any
from super.core.block.base import Block, BlockRegistry
from super.core.handler import BaseHandler


class SuperExecutor(BaseHandler):
    def __init__(
        self,
        block_registry: BlockRegistry,
        logger: logging.Logger = logging.getLogger(__name__),
    ):
        self._logger = logger
        self._block_registry = block_registry
        self._execution_state: Dict[str, Any] = {}

    async def execute(self, **kwargs) -> Dict[str, Any]:
        self._logger.debug("Executing blocks...")
        self._execution_state = {"global": kwargs}
        for block in self._block_registry.blocks():
            try:
                block_input = self._prepare_block_input(
                    block, block.config.input_schema
                )
                response = await self._block_registry.perform(
                    block.name(), **block_input
                )
                self._update_execution_state(block, response)
                self._logger.debug(f"Response from block {block.name()}: {response}")
            except Exception as e:
                self._logger.error(f"Error executing block {block.name()}: {e}")
                raise e
        return self._execution_state

    def _prepare_block_input(
        self, block: Block, input_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        block_input = {}
        for input_key, input_value in input_schema.items():
            if isinstance(input_value, dict):
                if "reference" in input_value:
                    block_id, nesting = input_value["reference"].split(".", 1)
                    block_input[input_key] = self.get_nested_value(
                        self._execution_state[block_id], nesting
                    )
                elif "value" in input_value:
                    block_input[input_key] = input_value["value"]
                else:
                    block_input[input_key] = self._prepare_block_input(
                        block, input_value
                    )
            else:
                block_input[input_key] = input_value
        return block_input

    def _update_execution_state(self, block: Block, response: Dict[str, Any]) -> None:
        self._execution_state[f"block_{block.config.id}"] = response

    def get_nested_value(self, data: Dict[str, Any], keys: str) -> Any:
        for key in keys.split("."):
            if key in data:
                data = data[key]
            else:
                return None
        return data

    def __repr__(self):
        return f"SuperExecutor(block_registry={self._block_registry})"

    def dump(self):
        pass

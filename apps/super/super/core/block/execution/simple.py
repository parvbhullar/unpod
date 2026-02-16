import asyncio
import logging
import platform
import time
from typing import List, Dict, Any
import distro
import inflection
import json

from super.core.block.base import BlockRegistry, Block
from super.core.handler import BaseHandler
from super.core.handler.config import ExecutionNature


class SimpleExecutor(BaseHandler):
    default_configuration = {}

    def __init__(
        self,
        block_registry: BlockRegistry,
        logger: logging.Logger = logging.getLogger(__name__),
    ) -> None:
        self._logger = logger
        self._block_registry = block_registry
        self._execution_nature = ExecutionNature.SEQUENTIAL
        self._execution_state: Dict[str, Any] = {}

    # async def interaction_handler(self):
    async def execute(self, **kwargs):
        """Execute the task."""
        self._logger.debug(f"Executing task:")
        return await self.exec_blocks(**kwargs)

    async def exec_blocks(self, **kwargs) -> None:
        self._execution_state = {"global": kwargs}
        # Execute for Sequential nature
        for block in self._block_registry.blocks():
            try:
                # <<<<<<< HEAD
                #                 block_input = self._prepare_block_input(block, block.config.input_schema)
                # =======
                if block.config.block_type == "form":
                    block_input = kwargs
                else:
                    block_input = self._prepare_block_input(
                        block, block.config.input_schema
                    )
                # >>>>>>> 2cfbc95a52e5b79e1271f34c1ed45d591d1a5564
                response = await self._block_registry.perform(
                    block.name(), **block_input
                )
                self._update_execution_state(block, response)
                self._logger.debug(f"Response from block {block.name()}: {response}")
                self._logger.debug(f"Execution State {self._execution_state}")
            except Exception as e:
                self._logger.error(f"Error executing block {block.name()}: {e}")
                raise e
        return self._execution_state

    def get_nested_val(self, object, nesting):
        for key in nesting.split("."):
            if key in object:
                object = object[key]
            else:
                return None
        return object

    # <<<<<<< HEAD
    def _prepare_block_input(self, block: Block, fields) -> Dict[str, Any]:
        block_input = {}
        print("Block", block.name())
        print("Schema", fields)
        for input_key, input_schema in fields.items():
            # =======
            #     def _prepare_block_input(self, block: Block, properties) -> Dict[str, Any]:
            #         block_input = {}
            #         print("Block", block.name())
            #         print("Schema", properties)
            #         for input_key, input_schema in properties.items():
            # >>>>>>> 2cfbc95a52e5b79e1271f34c1ed45d591d1a5564
            # if 'reference' in value:
            #     reference_path = value['reference'].split('.')
            #     value_from_previous = self.get_value_from_nested_dict(previous_input_schema, reference_path[1:])
            print("Input key", input_key, input_schema)
            # <<<<<<< HEAD
            if input_schema.get("properties"):
                block_input[input_key] = self._prepare_block_input(
                    block, input_schema.get("properties")
                )
            # =======
            #             if input_schema.get('properties'):
            #                 block_input[input_key] = self._prepare_block_input(block, input_schema.get('properties'))
            # >>>>>>> 2cfbc95a52e5b79e1271f34c1ed45d591d1a5564
            elif input_schema.get("reference"):
                block_id, nesting = input_schema["reference"].split(".", 1)
                block_input[input_key] = self.get_nested_val(
                    self._execution_state[block_id], nesting
                )
            elif input_schema.get("value"):
                block_input[input_key] = input_schema["value"]
            else:
                block_input[input_key] = None
            print("Input Value", block_input[input_key])
        print("Block Input", block_input)
        return block_input

    def _update_execution_state(self, block: Block, response: Dict[str, Any]) -> None:
        self._execution_state[f"block_{block.config.id}"] = response
        # for output_key in block.config.output_schema.keys():
        #     if output_key in response:
        #         self._execution_state[f"block_{block.config.id}"][output_key] = response[output_key]
        #     else:
        #         self._logger.warning(f"Expected output '{output_key}' not found in response from block {block.name()}")

    def get_value_from_nested_dict(self, data, keys):
        for key in keys:
            data = data[key]
        return data

    def set_value_in_nested_dict(self, data, keys, value):
        for key in keys[:-1]:
            data = data.setdefault(key, {})
        data[keys[-1]] = value

    def load_values_from_previous_block(self, previous_block, next_block):
        previous_input_schema = json.loads(previous_block["input_schema"])
        next_input_schema = json.loads(next_block["input_schema"])

        for key, value in next_input_schema["query_params"].items():
            if "reference" in value:
                reference_path = value["reference"].split(".")
                value_from_previous = self.get_value_from_nested_dict(
                    previous_input_schema, reference_path[1:]
                )
                self.set_value_in_nested_dict(
                    next_input_schema,
                    ["query_params", key, "value"],
                    value_from_previous,
                )

        next_block["input_schema"] = json.dumps(next_input_schema)

    def __repr__(self):
        pass

    def dump(self):
        pass

    @classmethod
    def factory(cls, config, logger):
        pass


def get_os_info() -> str:
    os_name = platform.system()
    os_info = (
        platform.platform(terse=True)
        if os_name != "Linux"
        else distro.name(pretty=True)
    )
    return os_info

import logging
from typing import Dict, Any
from super.core.block.base import Block, BlockConfiguration
from super.core.plugin.base import PluginLocation, PluginStorageFormat


class FormBlock(Block):
    default_configuration = BlockConfiguration(
        id=0,
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route=f"{__name__}.FormBlock",
        ),
        block_type="api",
        metadata={
            "name": "Form Block",
            "description": "A block that interacts with the API.",
            "config": {"url": "", "method": "GET", "headers": {"product_id": ""}},
        },
        input_schema={},  # This will be user defined fields but populated by api, csv, form
        output_schema={
            # This will be same as input schema
        },
        body="",
        seq_order=0,
    )

    def __init__(
        self,
        logger: logging.Logger,
        configuration: BlockConfiguration,
    ):
        self._logger = logger
        self._configuration = configuration
        # self._update_input_schema()

    def _update_input_schema(self):
        config = self._configuration.metadata["config"]
        input_schema = {
            "url": {
                "type": "string",
                "description": "The URL of the API endpoint.",
            },
            "method": {
                "type": "string",
                "description": "The HTTP method for the API request.",
            },
        }

        for param in config.get("params_inputs", []):
            input_schema[param] = {
                "type": "string",
                "description": f"Parameter: {param}",
            }

        for payload_item in config.get("payload_inputs", []):
            input_schema[payload_item] = {
                "type": "string",
                "description": f"Payload item: {payload_item}",
            }

        self._configuration.input_schema = input_schema

    @property
    def description(self) -> str:
        return "API Block for interacting with the API."

    @property
    def config(self) -> BlockConfiguration:
        return self._configuration

    @property
    def arguments(self) -> Dict[str, Any]:
        return self._configuration.input_schema

    async def __call__(self, **kwargs) -> Dict[str, Any]:
        self._configuration.output_schema = kwargs
        self._logger.info("GST API Block called.")
        return kwargs

        config = self._configuration.metadata["config"]

        # Prepare the API request
        url = kwargs.get("url", config["url"])
        method = kwargs.get("method", config["method"])

        params = {}
        payload = {}
        headers = config.get("headers", {})

        for param in config.get("params_inputs", []):
            if param in kwargs:
                params[param] = kwargs[param]

        for payload_item in config.get("payload_inputs", []):
            if payload_item in kwargs:
                payload[payload_item] = kwargs[payload_item]

        # Here you would typically make the actual API call using the prepared data
        # For demonstration, we'll just return a mock response
        return {
            "response": {
                "status": "success",
                "data": {
                    "url": url,
                    "method": method,
                    "params": params,
                    "payload": payload,
                    "headers": headers,
                    "message": "API call prepared successfully",
                },
            }
        }

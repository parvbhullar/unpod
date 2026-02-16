import logging
from typing import Dict, Any

import requests

from super.core.block.base import Block, BlockConfiguration
from super.core.plugin.base import PluginLocation, PluginStorageFormat


class APIBlock(Block):
    default_configuration = BlockConfiguration(
        id=0,
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route=f"{__name__}.APIBlock",
        ),
        block_type="api",
        metadata={
            "name": "API Block",
            "description": "A block that interacts with the API.",
            "config": {"url": "", "method": "GET", "headers": {"product_id": ""}},
        },
        input_schema={},  # This will be dynamically populated
        output_schema={
            "response": {
                "type": "object",
                "description": "The response from the API.",
            },
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

    # def _update_input_schema(self):
    #     config = self._configuration.metadata['config']
    #     input_schema = {
    #         "url": {
    #             "type": "string",
    #             "description": "The URL of the API endpoint.",
    #         },
    #         "method": {
    #             "type": "string",
    #             "description": "The HTTP method for the API request.",
    #         }
    #     }
    #
    #     for param in config.get('params_inputs', []):
    #         input_schema[param] = {
    #             "type": "string",
    #             "description": f"Parameter: {param}",
    #         }
    #
    #     for payload_item in config.get('payload_inputs', []):
    #         input_schema[payload_item] = {
    #             "type": "string",
    #             "description": f"Payload item: {payload_item}",
    #         }
    #
    #     self._configuration.input_schema = input_schema

    @property
    def description(self) -> str:
        return "API Block for interacting with the API."

    @property
    def config(self) -> BlockConfiguration:
        return self._configuration

    @property
    def arguments(self) -> Dict[str, Any]:
        return self._configuration.input_schema

    async def __call__(self, **api_kwargs) -> Dict[str, Any]:
        self._logger.info("GST API Block called.")

        config = self._configuration.metadata["config"]

        # Prepare the API request
        url = config["url"]
        method = config["method"]
        headers = config.get("headers", {})

        params = api_kwargs.get("query_params", {})
        payload = api_kwargs.get("payload", {})
        # headers = headers.update(api_kwargs.get('headers', {}))
        print("api_kwargs", api_kwargs)
        print("params", params)
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params)
            else:
                response = requests.request(
                    method, url, headers=headers, params=params, json=payload
                )

            # response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
            return {"response": response.json()}
        except requests.exceptions.RequestException as e:
            self._logger.error(f"An error occurred: {e}")
            return {"response": {"status": "error", "message": str(e)}}

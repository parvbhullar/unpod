import logging
import os

from super.core.block.base import Block, BlockConfiguration
from super.core.handler.planner.strategies import SimplePrompt
from super.core.handler.simple import SimpleHandler
from super.core.handler.strategy.config import PromptStrategyConfiguration

from super.core.plugin.base import PluginLocation, PluginStorageFormat
from super.core.resource.llm.schema import LanguageModelClassification
from super.core.resource.model_providers import AIModelName, ModelProviderName
from super.core.workspace import Workspace


model_mapping = {
    ModelProviderName.OPENAI: {
        "ADA": AIModelName.ADA,
        "GPT3": AIModelName.OPENAI_GPT4,
        "GPT3_16K": AIModelName.OPENAI_GPT3_16K,
        "GPT4": AIModelName.OPENAI_GPT4,
        "GPT4_32K": AIModelName.OPENAI_GPT4_32K,
        "GPT4_TURBO": AIModelName.OPENAI_GPT4_TURBO,
        "GPT4_VISION": AIModelName.OPENAI_GPT4_VISION,
        "GPT4_32K_NEW": AIModelName.OPENAI_GPT4_32K_NEW,
        "GPT3_FINETUNE_MODEL": AIModelName.OPENAI_GPT3_FINETUNE_MODEL,
        "GPT4_O": AIModelName.OPENAI_GPT4_O,
    }
}

model_provider_mapping = {"OPEN_AI": ModelProviderName.OPENAI}


class LLMBlock(Block):
    default_configuration = BlockConfiguration(
        id=0,
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route=f"{__name__}.LLMBlock",
        ),
        block_type="llm",
        metadata={
            "name": "llm",
            "description": "A block that uses a language model to generate text.",
            "config": {
                "model_name": "gpt-3.5-turbo",
                "model_temp": "0.5",
                "model_provider": "OPEN_AI",
                "system_prompt": "Write a story about a dragon based on given keywords",
            },
        },
        input_schema={
            "genre": {
                "type": "string",
                "description": "The genre of the story.",
            },
            "keywords": {
                "type": "string",
                "description": "Temp of the model to use.",
            },
        },
        output_schema={
            "response": {
                "type": "string",
                "description": "The output of the block.",
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

    @property
    def description(self) -> str:
        return "LLM block."

    @property
    def config(self) -> str:
        return self._configuration

    @property
    def arguments(self) -> dict:
        return {
            "model_name": {
                "type": "string",
                "description": "The name of the model to use.",
            },
            "model_temp": {
                "type": "string",
                "description": "Temp of the model to use.",
            },
            "system_prompt": {
                "type": "string",
                "description": "The system prompt to use.",
            },
        }

    async def __call__(self, **block_args: dict) -> dict:
        print("LLM block called.", block_args)

        model_provider = model_provider_mapping.get(
            self._configuration.metadata["config"]["model_provider"],
            ModelProviderName.OPENAI,
        )
        model_name = model_mapping.get(
            self._configuration.metadata["config"]["model_name"],
            AIModelName.OPENAI_GPT4,
        )

        print("Model config", model_name, model_provider)

        task_pilot = SimpleHandler.create(
            PromptStrategyConfiguration(
                model_classification=LanguageModelClassification.SMART_MODEL,
                system_prompt=self._configuration.metadata["config"]["system_prompt"],
                user_prompt_template=SimplePrompt.DEFAULT_USER_PROMPT_TEMPLATE,
                parser_schema=SimplePrompt.DEFAULT_PARSER_SCHEMA,
            ),
            smart_model_name=AIModelName.OPENAI_GPT4_VISION,
            fast_model_name=AIModelName.OPENAI_GPT4,
        )

        # task_pilot = SimpleTaskPilot(
        #     configuration=TaskPilotConfiguration(
        #         location=PluginLocation(
        #             storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
        #             storage_route="super.core.flow.simple.SuperTaskPilot",
        #         ),
        #         pilot=PilotConfiguration(
        #             name="simple_task_pilot",
        #             role=("An AI Pilot designed to complete simple tasks with "),
        #             goals=[
        #                 "Complete simple tasks",
        #             ],
        #             cycle_count=0,
        #             max_task_cycle_count=3,
        #             creation_time="",
        #             execution_nature=ExecutionNature.AUTO,
        #         ),
        #         execution_nature=ExecutionNature.SIMPLE,
        #         prompt_strategy=PromptStrategyConfiguration(
        #             model_classification=LanguageModelClassification.SMART_MODEL,
        #             system_prompt=self._configuration.metadata['config']['system_prompt'],
        #             user_prompt_template=SimplePrompt.DEFAULT_USER_PROMPT_TEMPLATE,
        #             parser_schema=SimplePrompt.DEFAULT_PARSER_SCHEMA,
        #         ),
        #         models={
        #             LanguageModelClassification.FAST_MODEL: LanguageModelConfiguration(
        #                 model_name=AIModelName.OPENAI_GPT4,
        #                 provider_name=ModelProviderName.OPENAI,
        #                 temperature=0.9,
        #             ),
        #             LanguageModelClassification.SMART_MODEL: LanguageModelConfiguration(
        #                 model_name=AIModelName.OPENAI_GPT4_O,
        #                 provider_name=ModelProviderName.OPENAI,
        #                 temperature=self._configuration.metadata['config']['model_temp'],
        #             ),
        #         },
        #     )
        # )

        res = await task_pilot.execute(str(block_args))

        return res.content

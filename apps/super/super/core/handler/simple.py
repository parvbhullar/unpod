import enum
import json
from datetime import datetime
from typing import List, Any, Dict
import logging
import platform
from abc import ABC

from super.core.context.schema import Message
from super.core.handler.base import BaseHandler
from super.core.handler.config import (
    HandlerConfiguration,
    RoleConfiguration,
    ExecutionNature,
)
from super.core.handler.planner.strategies import SimplePrompt
from super.core.handler.strategy.base import PromptStrategy
from super.core.plugin.base import PluginLocation, PluginStorageFormat
import distro

from super.core.plugin.utlis import load_class
from super.core.resource.llm.schema import LanguageModelClassification
from super.core.resource.model_providers import (
    LanguageModelProvider,
    AIModelName,
    OPEN_AI_MODELS,
)
from super.core.resource.model_providers.factory import (
    ModelProviderFactory,
    ModelConfigFactory,
)
from super.core.resource.model_providers.schema import LanguageModelResponse
from super.core.resource.model_providers.utils.token_counter import count_string_tokens


class SimpleHandler(BaseHandler, ABC):
    """A class representing a handler step."""

    default_configuration = HandlerConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route="super.core.handle.simple.SimpleHandler",
        ),
        role=RoleConfiguration(
            id="simple_handler",
            name="Simple Handler",
            role=("A simple handler to handle llm calls."),
            cycle_count=0,
            max_task_cycle_count=3,
        ),
        execution_nature=ExecutionNature.AUTO,
    )

    def __init__(
        self,
        configuration: HandlerConfiguration = default_configuration,
        logger: logging.Logger = logging.getLogger(__name__),
        session_id: str = None,
        model_providers=None,
        orc=None,
        **kwargs,
    ) -> None:
        super().__init__(logger, **kwargs)
        self._session_id = session_id
        self._logger = logger
        self._configuration = configuration
        self._execution_nature = configuration.execution_nature
        self._orc = orc

        self._providers: Dict[LanguageModelClassification, LanguageModelProvider] = {}
        if model_providers is None:
            model_providers = ModelProviderFactory.load_providers()
        for model, model_config in self._configuration.models.items():
            self._providers[model] = model_providers[model_config.provider_name]

        prompt_config = self._configuration.prompt_strategy.dict()
        location = prompt_config.pop("location", None)
        if location is not None:
            self._prompt_strategy = load_class(location, prompt_config)
        else:
            self._prompt_strategy = SimplePrompt(**prompt_config)

    async def execute(
        self, objective: str | Message, *args, **kwargs
    ) -> LanguageModelResponse:
        """Execute the task."""
        self._logger.debug(f"Executing task: {objective}")
        if not isinstance(objective, Message):
            # if task is not passed, one is created with default settings
            task = Message.create(objective)
        else:
            task = objective

        context_res = await self.exec_task(task, **kwargs)
        return context_res

    async def exec_task(self, message: Message, **kwargs) -> LanguageModelResponse:
        template_kwargs = message.generate_kwargs()
        template_kwargs.update(kwargs)

        return await self.chat_with_model(
            self._prompt_strategy,
            **template_kwargs,
        )

    async def chat_with_model(
        self,
        prompt_strategy: PromptStrategy,
        **kwargs,
    ) -> LanguageModelResponse:
        model_classification = prompt_strategy.model_classification
        model_configuration = self._configuration.models[model_classification]

        template_kwargs = self._make_template_kwargs_for_strategy(prompt_strategy)
        kwargs.update(template_kwargs)
        prompt = prompt_strategy.build_prompt(
            model_name=model_configuration.model_name, **kwargs
        )
        # print("Prompt", prompt)
        model_configuration = self.choose_model(
            model_classification, model_configuration, prompt
        )

        model_configuration = model_configuration.dict()
        self._logger.debug(f"Using model configuration: {model_configuration}")
        del model_configuration["provider_name"]
        provider = self._providers[model_classification]
        if "response_format" in kwargs:
            model_configuration["response_format"] = kwargs["response_format"]

        # self._logger.debug(f"Using prompt:\n{prompt}\n\n")

        response = await provider.completion(
            model_prompt=prompt.messages,
            functions=prompt.functions,
            function_call=prompt.get_function_call(),
            # req_res_callback=(
            #     self._callback.model_req_res_callback if self._callback else None
            # ),
            **model_configuration,
            completion_parser=prompt_strategy.parse_response_content,
        )

        return LanguageModelResponse.parse_obj(response.dict())

    def choose_model(self, model_classification, model_configuration, prompt):
        if model_configuration.model_name not in [
            AIModelName.OPENAI_GPT4,
            AIModelName.OPENAI_GPT4,
        ]:
            return model_configuration
        current_tokens = count_string_tokens(
            str(prompt), model_configuration.model_name
        )
        # print("Tokens", current_tokens)
        token_limit = OPEN_AI_MODELS[model_configuration.model_name].max_tokens
        completion_token_min_length = 1000
        send_token_limit = token_limit - completion_token_min_length
        if current_tokens > send_token_limit:
            if model_classification == LanguageModelClassification.FAST_MODEL:
                model_configuration.model_name = AIModelName.OPENAI_GPT4_O_MINI
            elif model_classification == LanguageModelClassification.SMART_MODEL:
                print("Using GPT4_TURBO")
                model_configuration.model_name = AIModelName
        return model_configuration

    def _make_template_kwargs_for_strategy(self, strategy: PromptStrategy):
        provider = self._providers[strategy.model_classification]
        template_kwargs = {
            "os_info": get_os_info(),
            "api_budget": provider.get_remaining_budget(),
            "current_time": datetime.strftime(datetime.now(), "%c"),
        }
        return template_kwargs

    def __repr__(self):
        return f"{self.__class__.__name__}()"

    def __str__(self):
        return self._configuration.__str__()

    def name(self) -> str:
        """The name of the ability."""
        return self._configuration.role.id

    def dump(self) -> dict:
        role_config = self._configuration.role
        dump = {
            "id": role_config.id,
            "name": role_config.name,
            "role": role_config.role,
            # "prompt_strategy": self._prompt_strategy.get_config().__dict__
        }
        return dump

    @classmethod
    def from_json(cls, json_data: str | dict) -> "SimpleHandler":
        if isinstance(json_data, dict):
            data = json_data
        else:
            data = json.loads(json_data)
        fields = data.get("fields", data)

        models_config = ModelConfigFactory.get_models_config(
            smart_model_name=fields.get(
                "smart_model_name", AIModelName.OPENAI_GPT4_O_MINI
            ),
            fast_model_name=fields.get("fast_model_name", AIModelName.OPENAI_GPT4),
            smart_model_temp=fields.get("smart_model_temp", 0.2),
            fast_model_temp=fields.get("fast_model_temp", 0.2),
        )

        system_prompt = fields.get("system_prompt", SimplePrompt.DEFAULT_SYSTEM_PROMPT)
        user_prompt_template = fields.get(
            "user_prompt_template", SimplePrompt.DEFAULT_USER_PROMPT_TEMPLATE
        )
        prompt_strategy = SimplePrompt.factory(
            system_prompt=system_prompt,
            user_prompt_template=user_prompt_template,
        )

        configuration = HandlerConfiguration(
            location=PluginLocation(
                storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
                storage_route="super.app.agent_types.PersonaGenPrompt",
            ),
            role=RoleConfiguration(
                name=fields.get("persona_name", fields.get("name", "")),
                role=fields.get("about", ""),
                cycle_count=0,
                max_task_cycle_count=3,
            ),
            execution_nature=ExecutionNature.AUTO,
            models=models_config,
            prompt_strategy=prompt_strategy.get_config(),
        )
        instance = cls(configuration)
        return instance

    @classmethod
    def create(
        cls,
        prompt_config,
        smart_model_name=AIModelName.OPENAI_GPT4,
        fast_model_name=AIModelName.OPENAI_GPT3_16K,
        smart_model_temp=0.9,
        fast_model_temp=0.9,
        model_providers=None,
        role_config=None,
        orc=None,
        session_id: str = None,
        logger: logging.Logger = None,
    ):
        models_config = ModelConfigFactory.get_models_config(
            smart_model_name=smart_model_name,
            fast_model_name=fast_model_name,
            smart_model_temp=smart_model_temp,
            fast_model_temp=fast_model_temp,
        )
        if model_providers is None:
            model_providers = ModelProviderFactory.load_providers()

        # Initialize settings
        config = cls.default_configuration.copy()
        # Use default logger if not provided
        if logger is None:
            logger = logging.getLogger(__name__)
        if prompt_config is not None:
            config.prompt_strategy = prompt_config
        if role_config is not None:
            config.role = role_config
        if models_config is not None:
            config.models = models_config

        # Create and return SimpleTaskPilot instance

        return cls(
            configuration=config,
            model_providers=model_providers,
            logger=logger,
            # callback=callback,
            orc=orc,
            session_id=session_id,
        )


def get_os_info() -> str:
    os_name = platform.system()
    os_info = (
        platform.platform(terse=True)
        if os_name != "Linux"
        else distro.name(pretty=True)
    )
    return os_info

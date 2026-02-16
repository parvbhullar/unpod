import logging
from typing import Dict, Optional, Any

from super.core.handler.config import HandlerConfiguration
from super.core.handler.strategy.base import PromptStrategy
from super.core.plugin.utlis import load_class
from super.core.resource.model_providers import LanguageModelProvider
from super.core.resource.model_providers.schema import (
    LanguageModelResponse,
    AsyncLLMResponseGen,
)
from llama_index.llms.litellm import LiteLLM
from .base import BaseLLM
from .schema import LanguageModelClassification, LanguageModelPrompt
from ..model_providers.factory import ModelProviderFactory
from ...handler.planner.strategies import SimplePrompt


class SimpleLLM(BaseLLM):
    """Simple implementation of the LLM interface."""

    def __init__(
        self,
        configuration: HandlerConfiguration,
        logger: Optional[Any] = None,
        model_providers: Optional[Dict[str, LanguageModelProvider]] = None,
    ) -> None:
        """Initialize the LLM handler."""
        self._logger = logger or logging.getLogger(__name__)
        self._configuration = configuration
        self._execution_nature = configuration.execution_nature

        self._load_providers(model_providers)
        self._setup_prompt_strategy()

    def _setup_agent(self):
        """Set up the agent with appropriate model configuration."""
        model_classification = self._prompt_strategy.model_classification
        model_config = self._configuration.models[model_classification]
        self.llm = LiteLLM(model_config.model_name, model_config.temperature)

    def _load_providers(
        self, model_providers: Optional[Dict[str, LanguageModelProvider]] = None
    ) -> None:
        """Load language model providers."""
        self._providers: Dict[LanguageModelClassification, LanguageModelProvider] = {}
        if model_providers is None:
            model_providers = ModelProviderFactory.load_providers()
        for model, model_config in self._configuration.models.items():
            self._providers[model] = model_providers[model_config.provider_name]

    def _setup_prompt_strategy(self) -> None:
        """Set up the prompt strategy based on configuration."""
        prompt_config = self._configuration.prompt_strategy.dict()
        location = prompt_config.pop("location", None)
        if location is not None:
            self._prompt_strategy = load_class(location, prompt_config)
        else:
            self._prompt_strategy = SimplePrompt(**prompt_config)

    def _make_template_kwargs_for_strategy(
        self, prompt_strategy: PromptStrategy
    ) -> Dict[str, Any]:
        """Create template kwargs for the prompt strategy."""
        return {}

    async def chat_stream(self, **kwargs) -> AsyncLLMResponseGen:
        """Stream chat responses from the language model."""
        try:
            model_classification = self._prompt_strategy.model_classification
            model_configuration = self._configuration.models[model_classification]

            template_kwargs = self._make_template_kwargs_for_strategy(
                self._prompt_strategy
            )
            kwargs.update(template_kwargs)
            prompt = await self._get_prompt(**kwargs)
            model_configuration = model_configuration.dict()
            self._logger.debug(f"Using model configuration: {model_configuration}")
            del model_configuration["provider_name"]

            provider = self._providers[model_classification]
            if "response_format" in kwargs:
                model_configuration["response_format"] = kwargs["response_format"]

            # self._logger.debug(f"Using prompt:\n{prompt}\n\n")
            stream = provider.completion_stream(
                model_prompt=prompt.messages,
                functions=prompt.functions,
                function_call=prompt.get_function_call(),
                **model_configuration,
                completion_parser=self._prompt_strategy.parse_response_content,
            )

            async for chunk in stream:
                yield chunk

        except Exception as e:
            self._logger.error(f"Error in chat stream: {str(e)}")
            raise

    async def chat(self, **kwargs) -> LanguageModelResponse:
        """Get a single chat response from the language model."""
        try:
            model_classification = self._prompt_strategy.model_classification
            model_configuration = self._configuration.models[model_classification]

            template_kwargs = self._make_template_kwargs_for_strategy(
                self._prompt_strategy
            )
            kwargs.update(template_kwargs)
            prompt = await self._get_prompt(**kwargs)
            model_configuration = model_configuration.dict()
            self._logger.debug(f"Using model configuration: {model_configuration}")
            del model_configuration["provider_name"]

            provider = self._providers[model_classification]
            if "response_format" in kwargs:
                model_configuration["response_format"] = kwargs["response_format"]

            # self._logger.debug(f"Using prompt:\n{prompt}\n\n")

            return await provider.completion(
                model_prompt=prompt.messages,
                functions=prompt.functions,
                function_call=prompt.get_function_call(),
                **model_configuration,
                completion_parser=self._prompt_strategy.parse_response_content,
            )

        except Exception as e:
            self._logger.error(f"Error in chat: {str(e)}")
            raise

    async def _get_prompt(self, **kwargs) -> LanguageModelPrompt:
        """Get the prompt for the language model."""
        model_classification = self._prompt_strategy.model_classification
        model_configuration = self._configuration.models[model_classification]

        template_kwargs = self._make_template_kwargs_for_strategy(self._prompt_strategy)
        kwargs.update(template_kwargs)
        prompt = self._prompt_strategy.build_prompt(
            model_name=model_configuration.model_name, **kwargs
        )
        if "response_format" in kwargs:
            model_configuration["response_format"] = kwargs["response_format"]
        # self._logger.debug(f"Using prompt:\n{prompt}\n\n")
        return prompt

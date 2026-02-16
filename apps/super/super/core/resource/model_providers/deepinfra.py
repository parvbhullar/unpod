import enum
import functools
import logging
import math
import time
from typing import Callable, List, TypeVar, Optional, Any

import openai
from openai import APIError, RateLimitError

from super.core.configuration import (
    Configurable,
    SystemConfiguration,
    UserConfigurable,
)
from super.core.resource.model_providers.contants import (
    DEEP_INFRA_MODELS,
    AIModelName,
    DEEP_INFRA_EMBEDDING_MODELS,
    DEEP_INFRA_LANGUAGE_MODELS,
)
from super.core.resource.model_providers.schema import (
    Embedding,
    EmbeddingModelProvider,
    EmbeddingModelProviderModelResponse,
    LanguageModelFunction,
    LanguageModelMessage,
    LanguageModelProvider,
    LanguageModelProviderModelInfo,
    ModelProviderResponse,
    ModelProviderBudget,
    ModelProviderCredentials,
    ModelProviderName,
    ModelProviderService,
    ModelProviderSettings,
    ModelProviderUsage,
    AsyncLLMResponseGen,
)

DeepInfraEmbeddingParser = Callable[[Embedding], Embedding]
DeepInfraChatParser = Callable[[str], dict]


class DeepInfraConfiguration(SystemConfiguration):
    retries_per_request: int = UserConfigurable()


class DeepInfraModelProviderBudget(ModelProviderBudget):
    graceful_shutdown_threshold: float = UserConfigurable()
    warning_threshold: float = UserConfigurable()


class DeepInfraSettings(ModelProviderSettings):
    configuration: DeepInfraConfiguration
    credentials: ModelProviderCredentials
    budget: DeepInfraModelProviderBudget


class DeepInfraProvider(
    Configurable,
    LanguageModelProvider,
    EmbeddingModelProvider,
):
    default_settings = DeepInfraSettings(
        name="deepinfra_provider",
        description="Provides access to DeepInfra's API.",
        configuration=DeepInfraConfiguration(
            retries_per_request=10,
        ),
        credentials=ModelProviderCredentials(),
        budget=DeepInfraModelProviderBudget(
            total_budget=math.inf,
            total_cost=0.0,
            remaining_budget=math.inf,
            usage=ModelProviderUsage(
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
            ),
            graceful_shutdown_threshold=0.005,
            warning_threshold=0.01,
        ),
    )

    def __init__(
        self,
        settings: DeepInfraSettings = default_settings,
        logger: logging.Logger = logging.getLogger(__name__),
    ):
        self._configuration = settings.configuration
        self._credentials = settings.credentials
        self._budget = settings.budget

        self._logger = logger

        retry_handler = _DeepInfraRetryHandler(
            logger=self._logger,
            num_retries=self._configuration.retries_per_request,
        )
        self._create_completion = retry_handler(_create_completion)
        self._create_embedding = retry_handler(_create_embedding)

    def get_token_limit(self, model_name: AIModelName) -> int:
        """Get the token limit for a given model."""
        return DEEP_INFRA_MODELS[model_name].max_tokens

    def get_remaining_budget(self) -> float:
        """Get the remaining budget."""
        return self._budget.remaining_budget

    def get_total_cost(self) -> float:
        """Get the total cost."""
        return self._budget.total_cost

    async def completion(
        self,
        messages: List[LanguageModelMessage],
        model_name: AIModelName,
        *,
        functions: Optional[List[LanguageModelFunction]] = None,
        callback_handler: Optional[Callable] = None,
        completion_parser: Optional[Callable[[dict], Any]] = None,
        **kwargs,
    ) -> ModelProviderResponse:
        """Create a completion using the DeepInfra API."""
        completion_kwargs = self._get_completion_kwargs(model_name, functions, **kwargs)
        response = await self._create_completion(
            messages=messages,
            **completion_kwargs,
        )
        response_args = {
            "model_info": DEEP_INFRA_LANGUAGE_MODELS[model_name],
            "prompt_tokens_used": response.usage.prompt_tokens,
            "completion_tokens_used": response.usage.completion_tokens,
        }

        parsed_response = completion_parser(response.choices[0].message.dict())
        if callback_handler:
            await callback_handler(
                messages,
                functions,
                response,
                parsed_response,
                response_args,
                **kwargs,
            )
        response = ModelProviderResponse(content=parsed_response, **response_args)
        self._budget.update_usage_and_cost(response)
        return response

    async def completion_stream(
        self,
        messages: List[LanguageModelMessage],
        model_name: AIModelName,
        *,
        functions: Optional[List[LanguageModelFunction]] = None,
        callback_handler: Optional[Callable] = None,
        completion_parser: Optional[Callable[[dict], Any]] = None,
        **kwargs,
    ) -> AsyncLLMResponseGen:
        """Create a completion using the DeepInfra API."""
        completion_kwargs = self._get_completion_kwargs(model_name, functions, **kwargs)
        response = await self._create_completion(
            messages=messages,
            **completion_kwargs,
        )
        response_args = {
            "model_info": DEEP_INFRA_LANGUAGE_MODELS[model_name],
            "prompt_tokens_used": response.usage.prompt_tokens,
            "completion_tokens_used": response.usage.completion_tokens,
        }

        parsed_response = completion_parser(response.choices[0].message.dict())
        if callback_handler:
            await callback_handler(
                messages,
                functions,
                response,
                parsed_response,
                response_args,
                **kwargs,
            )
        response = ModelProviderResponse(content=parsed_response, **response_args)
        self._budget.update_usage_and_cost(response)
        yield response

    async def create_image(
        self,
        messages: List[LanguageModelMessage],
        model_name: AIModelName,
        *,
        functions: Optional[List[LanguageModelFunction]] = None,
        callback_handler: Optional[Callable] = None,
        completion_parser: Optional[Callable[[dict], Any]] = None,
        **kwargs,
    ) -> ModelProviderResponse:
        """Create a completion using the DeepInfra API."""
        completion_kwargs = self._get_completion_kwargs(model_name, functions, **kwargs)
        response = await self._create_completion(
            messages=messages,
            **completion_kwargs,
        )
        response_args = {
            "model_info": DEEP_INFRA_LANGUAGE_MODELS[model_name],
            "prompt_tokens_used": response.usage.prompt_tokens,
            "completion_tokens_used": response.usage.completion_tokens,
        }

        parsed_response = completion_parser(response.choices[0].message.dict())
        if callback_handler:
            await callback_handler(
                messages,
                functions,
                response,
                parsed_response,
                response_args,
                **kwargs,
            )
        response = ModelProviderResponse(content=parsed_response, **response_args)
        self._budget.update_usage_and_cost(response)
        return response

    async def create_embedding(
        self,
        text: str,
        model_name: AIModelName,
        **kwargs,
    ) -> EmbeddingModelProviderModelResponse:
        """Create an embedding using the DeepInfra API."""
        embedding_kwargs = self._get_embedding_kwargs(model_name, **kwargs)
        response = await self._create_embedding(text=text, **embedding_kwargs)

        response_args = {
            "model_info": DEEP_INFRA_EMBEDDING_MODELS[model_name],
            "prompt_tokens_used": response.usage.prompt_tokens,
            "completion_tokens_used": response.usage.completion_tokens,
        }
        response = EmbeddingModelProviderModelResponse(
            **response_args,
            embedding=response.embeddings[0],
        )
        self._budget.update_usage_and_cost(response)
        return response

    def _get_completion_kwargs(
        self,
        model_name: AIModelName,
        functions: List[LanguageModelFunction],
        **kwargs,
    ) -> dict:
        """Get kwargs for completion API call.

        Args:
            model: The model to use.
            kwargs: Keyword arguments to override the default values.

        Returns:
            The kwargs for the chat API call.

        """
        completion_kwargs = {
            "model": model_name,
            **kwargs,
            **self._credentials.unmasked(),
            "timeout": 300,
            "api_base": "https://api.deepinfra.com/v1/openai",
        }
        completion_kwargs["max_tokens"] = self.get_token_limit(model_name)
        if functions:
            completion_kwargs["functions"] = functions

        return completion_kwargs

    def _get_embedding_kwargs(
        self,
        model_name: AIModelName,
        **kwargs,
    ) -> dict:
        """Get kwargs for embedding API call.

        Args:
            model: The model to use.
            kwargs: Keyword arguments to override the default values.

        Returns:
            The kwargs for the embedding API call.

        """
        embedding_kwargs = {
            "model": model_name,
            **kwargs,
            **self._credentials.unmasked(),
        }

        return embedding_kwargs

    def __repr__(self):
        return "DeepInfraProvider()"

    @classmethod
    def factory(
        cls,
        api_key: Optional[str] = None,
        retries_per_request: int = 10,
        total_budget: float = float("inf"),
        graceful_shutdown_threshold: float = 0.005,
        warning_threshold: float = 0.01,
        logger: Optional[logging.Logger] = None,
    ) -> "DeepInfraProvider":
        # Configure logger
        if logger is None:
            logger = logging.getLogger(__name__)

        settings = cls.init_settings(
            api_key,
            retries_per_request,
            total_budget,
            graceful_shutdown_threshold,
            warning_threshold,
        )

        # Instantiate and return DeepInfraProvider
        return DeepInfraProvider(settings=settings, logger=logger)

    @classmethod
    def init_settings(
        cls,
        api_key: Optional[str] = None,
        retries_per_request: int = 10,
        total_budget: float = float("inf"),
        graceful_shutdown_threshold: float = 0.005,
        warning_threshold: float = 0.01,
    ):
        # Initialize settings
        settings = cls.default_settings
        settings.configuration.retries_per_request = retries_per_request
        settings.credentials.api_key = api_key or settings.credentials.api_key
        settings.budget.total_budget = total_budget
        settings.budget.graceful_shutdown_threshold = graceful_shutdown_threshold
        settings.budget.warning_threshold = warning_threshold
        settings = cls.build_configuration(settings.dict())
        return settings


async def _create_embedding(text: str, *_, **kwargs) -> openai.Embedding:
    """Embed text using the OpenAI API.

    Args:
        text str: The text to embed.
        model_name str: The name of the model to use.

    Returns:
        str: The embedding.
    """
    aclient = openai.AsyncClient(
        api_key=kwargs.pop("api_key", None), base_url=kwargs.pop("api_base", None)
    )
    return await aclient.embeddings.create(input=[text], **kwargs)


async def _create_completion(
    messages: List[LanguageModelMessage], *_, **kwargs
) -> openai.types.Completion:
    """Create a chat completion using the DeepInfra API.

    Args:
        messages: The prompt to use.

    Returns:
        The completion.

    """
    messages = [message.dict() for message in messages]
    if "functions" in kwargs:
        kwargs["functions"] = [function.json_schema for function in kwargs["functions"]]
    else:
        del kwargs["function_call"]
    # print(messages)
    aclient = openai.AsyncClient(
        api_key=kwargs.pop("api_key", None), base_url=kwargs.pop("api_base", None)
    )
    return await aclient.chat.completions.create(messages=messages, **kwargs)


_T = TypeVar("_T")
# _P = TypeVar("_P")


class _DeepInfraRetryHandler:
    """Retry Handler for DeepInfra API call.

    Args:
        num_retries int: Number of retries. Defaults to 10.
        backoff_base float: Base for exponential backoff. Defaults to 2.
        warn_user bool: Whether to warn the user. Defaults to True.
    """

    _retry_limit_msg = "Error: Reached rate limit, passing..."
    _api_key_error_msg = (
        "Please double check that you have setup a PAID DeepInfra API Account. You can "
        "read more here: https://docs.agpt.co/setup/#getting-an-api-key"
    )
    _backoff_msg = "Error: API Bad gateway. Waiting {backoff} seconds..."

    def __init__(
        self,
        logger: logging.Logger,
        num_retries: int = 10,
        backoff_base: float = 2.0,
        warn_user: bool = True,
    ):
        self._logger = logger
        self._num_retries = num_retries
        self._backoff_base = backoff_base
        self._warn_user = warn_user

    def _log_rate_limit_error(self) -> None:
        self._logger.debug(self._retry_limit_msg)
        if self._warn_user:
            self._logger.warning(self._api_key_error_msg)
            self._warn_user = False

    def _backoff(self, attempt: int) -> None:
        backoff = self._backoff_base ** (attempt + 2)
        self._logger.debug(self._backoff_msg.format(backoff=backoff))
        time.sleep(backoff)

    def __call__(self, func):
        @functools.wraps(func)
        async def _wrapped(*args, **kwargs) -> _T:
            num_attempts = self._num_retries + 1  # +1 for the first attempt
            for attempt in range(1, num_attempts + 1):
                try:
                    return await func(*args, **kwargs)

                except RateLimitError:
                    if attempt == num_attempts:
                        raise
                    self._log_rate_limit_error()

                except APIError as e:
                    if (e.http_status != 502) or (attempt == num_attempts):
                        raise

                self._backoff(attempt)

        return _wrapped

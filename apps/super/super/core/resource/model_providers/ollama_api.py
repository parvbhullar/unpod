import enum
import functools
import logging
import math
import time
import json

from typing import Callable, List, TypeVar, Optional, Any

from requests.exceptions import HTTPError, RetryError

from super.core.configuration import (
    Configurable,
    SystemConfiguration,
    UserConfigurable,
)
from super.core.resource.model_providers.contants import (
    OLLAMA_MODELS,
    AIModelName,
    OLLAMA_LANGUAGE_MODELS,
    OLLAMA_EMBEDDING_MODELS,
)
from super.core.resource.model_providers.schema import (
    Embedding,
    EmbeddingModelProvider,
    EmbeddingModelProviderModelInfo,
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
from super.core.resource.model_providers.utils.api_client import (
    APIClient,
)

OllamaEmbeddingParser = Callable[[Embedding], Embedding]
OllamaChatParser = Callable[[str], dict]


class OllamaConfiguration(SystemConfiguration):
    retries_per_request: int = UserConfigurable()


class OllamaModelProviderBudget(ModelProviderBudget):
    graceful_shutdown_threshold: float = UserConfigurable()
    warning_threshold: float = UserConfigurable()


class OllamaSettings(ModelProviderSettings):
    configuration: OllamaConfiguration
    credentials: ModelProviderCredentials
    budget: OllamaModelProviderBudget


class OllamaApiProvider(
    Configurable,
    LanguageModelProvider,
    EmbeddingModelProvider,
):
    default_settings = OllamaSettings(
        name="ollama_provider",
        description="Provides access to Ollama's API.",
        configuration=OllamaConfiguration(
            retries_per_request=10,
        ),
        credentials=ModelProviderCredentials(),
        budget=OllamaModelProviderBudget(
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
        settings: OllamaSettings = default_settings,
        logger: logging.Logger = logging.getLogger(__name__),
    ):
        self._configuration = settings.configuration
        self._credentials = settings.credentials
        self._budget = settings.budget

        self._logger = logger

        retry_handler = _OllamaRetryHandler(
            logger=self._logger,
            num_retries=self._configuration.retries_per_request,
        )

        self._client = APIClient(base_url="http://super-ollama.co")
        self._create_completion = retry_handler(_create_completion)
        # self._create_embedding = retry_handler(_create_embedding) ## TODO: Enable embedding as well.

    def get_token_limit(self, model_name: AIModelName) -> int:
        """Get the token limit for a given model."""
        return OLLAMA_MODELS[model_name].max_tokens

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
        """Create a completion using the Ollama API."""
        completion_kwargs = self._get_completion_kwargs(model_name, functions, **kwargs)
        response = await self._create_completion(
            messages=messages,
            client=self._client,
            **completion_kwargs,
        )
        print(response.text)
        response_args = {
            "model_info": OLLAMA_LANGUAGE_MODELS[model_name],
            "prompt_tokens_used": self._client.count_tokens(
                self.combine_text_from_objects(messages, functions), model_name
            ),
            "completion_tokens_used": self._client.count_tokens(
                response.completion, model_name
            ),
        }

        parsed_response = (
            completion_parser(response.dict()) if completion_parser else response.dict()
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
        """Create a completion using the Ollama API."""
        completion_kwargs = self._get_completion_kwargs(model_name, functions, **kwargs)
        response = await self._create_completion(
            messages=messages,
            client=self._client,
            **completion_kwargs,
        )
        print(response.text)
        response_args = {
            "model_info": OLLAMA_LANGUAGE_MODELS[model_name],
            "prompt_tokens_used": self._client.count_tokens(
                self.combine_text_from_objects(messages, functions), model_name
            ),
            "completion_tokens_used": self._client.count_tokens(
                response.completion, model_name
            ),
        }

        parsed_response = (
            completion_parser(response.dict()) if completion_parser else response.dict()
        )
        response = ModelProviderResponse(content=parsed_response, **response_args)
        self._budget.update_usage_and_cost(response)
        yield response

    def combine_text_from_objects(self, model_prompt, functions):
        combined_text = ""

        # Assuming each object in model_prompt has a 'text' attribute
        for message in model_prompt:
            combined_text += str(message) + "\n"

        # Assuming each object in functions has a 'text' attribute
        for function in functions:
            combined_text += str(function) + "\n"

        return combined_text

    async def create_embedding(
        self,
        text: str,
        model_name: AIModelName,
        **kwargs,
    ) -> EmbeddingModelProviderModelResponse:
        """Create an embedding using the Ollama API."""
        embedding_kwargs = self._get_embedding_kwargs(model_name, **kwargs)
        response = await self._create_embedding(text=text, **embedding_kwargs)

        response_args = {
            "model_info": OLLAMA_EMBEDDING_MODELS[model_name],
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
            # **self._credentials.unmasked(),
            # "request_timeout": 120,
        }
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
            # **self._credentials.unmasked(),
        }

        return embedding_kwargs

    def _wrap_prompt(self, prompt: str, **kwargs: Any) -> str:
        # As a last resort, wrap the prompt ourselves to emulate instruct-style.
        return f"{prompt}\n"

    def __repr__(self):
        return "OllamaProvider()"

    @classmethod
    def factory(
        cls,
        api_key: Optional[str] = None,
        retries_per_request: int = 10,
        total_budget: float = float("inf"),
        graceful_shutdown_threshold: float = 0.005,
        warning_threshold: float = 0.01,
        logger: Optional[logging.Logger] = None,
    ) -> "OllamaApiProvider":
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

        # Instantiate and return OllamaProvider
        return OllamaApiProvider(settings=settings, logger=logger)

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


async def _create_completion(
    messages: List[LanguageModelMessage], client: APIClient, *_, **kwargs
) -> str:
    """Create a chat completion using the Ollama API.

    Args:
        messages: The prompt to use.

    Returns:
        The completion.

    """
    prompt = "\n".join([message.__str__() for message in messages])
    if "functions" in kwargs:
        kwargs["functions"] = [function.json_schema for function in kwargs["functions"]]
    else:
        del kwargs["function_call"]
    if "function_call" in kwargs:
        del kwargs["function_call"]
    if "functions" in kwargs:
        del kwargs["functions"]

    callback = kwargs.pop("callback", None)
    # del kwargs["api_type"]
    # del kwargs["api_base"]
    # del kwargs["api_version"]
    # del kwargs["deployment_id"]
    # del kwargs["request_timeout"]
    # ollama_api_key = kwargs.pop("api_key")
    params = {
        "model": kwargs.pop("model"),
        "prompt": prompt,
    }
    res = client.completion(
        params,
        **kwargs,
    )
    # # Use a list to store chunks
    # chunks = []
    #
    # # Iterate over the stream in chunks
    # for chunk in res.iter_content(chunk_size=8192):  # 8K chunks
    #     chunks.append(chunk)
    #     # print(chunk, "*"*32)

    full_response = ""
    # Iterating over the response line by line and displaying the details
    for line in res.iter_lines():
        if line:
            # Parsing each line (JSON chunk) and extracting the details
            chunk = json.loads(line)

            # If a callback function is provided, call it with the chunk
            if callback:
                callback(chunk)
            else:
                # If this is not the last chunk, add the "response" field value to full_response and print it
                if not chunk.get("done"):
                    response_piece = chunk.get("response", "")
                    full_response += response_piece
                    print(response_piece, end="", flush=True)

            # Check if it's the last chunk (done is true)
            if chunk.get("done"):
                final_context = chunk.get("context")

    # Combine chunks to form the full content
    # res._content = b"".join(chunks)
    res._content = full_response

    print(res)
    return res


_T = TypeVar("_T")
# _P = TypeVar("_P")


class _OllamaRetryHandler:
    """Retry Handler for Ollama API call.

    Args:
        num_retries int: Number of retries. Defaults to 10.
        backoff_base float: Base for exponential backoff. Defaults to 2.
        warn_user bool: Whether to warn the user. Defaults to True.
    """

    _retry_limit_msg = "Error: Reached rate limit, passing..."
    _api_key_error_msg = (
        "Please double check that you have setup a PAID Ollama API Account. You can "
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

                except RetryError:
                    if attempt == num_attempts:
                        raise
                    self._log_rate_limit_error()

                except HTTPError as e:
                    if (e.response.status_code != 502) or (attempt == num_attempts):
                        raise

                self._backoff(attempt)

        return _wrapped

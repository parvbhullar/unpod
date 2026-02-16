from linecache import cache

import math
import time
from typing import AsyncGenerator, Generator, Optional, Any, List, Callable

import litellm

from super.core.configuration import Configurable, SystemConfiguration, UserConfigurable
from super.core.resource.llm.schema import LanguageModelMessage, LanguageModelFunction
from super.core.resource.model_providers.contants import AI_MODELS, AI_EMBEDDING_MODELS
from super.core.resource.model_providers.schema import (
    AsyncLLMResponseGen,
    LanguageModelProvider,
    ModelProviderBudget,
    ModelProviderSettings,
    ModelProviderCredentials,
    ModelProviderUsage,
    EmbeddingModelProviderModelResponse,
    ModelProviderResponse,
    LanguageModelResponse,
)
import logging

from super.core.resource.schema import Embedding
from super.core.utils.logger import setup_logger

# logger = setup_logger()


class LLMConfiguration(SystemConfiguration):
    retries_per_request: int = UserConfigurable()
    cache: bool = UserConfigurable(default=True)


class LLMModelProviderBudget(ModelProviderBudget):
    graceful_shutdown_threshold: float = UserConfigurable()
    warning_threshold: float = UserConfigurable()


class LLMSettings(ModelProviderSettings):
    configuration: LLMConfiguration
    credentials: ModelProviderCredentials
    budget: LLMModelProviderBudget


class LiteLLMProvider(Configurable, LanguageModelProvider):
    """LiteLLM provider that supports multiple LLM backends through litellm library."""

    default_settings = LLMSettings(
        name="litellm_provider",
        description="Provides access to all litellm models API.",
        configuration=LLMConfiguration(
            retries_per_request=10,
            cache=False,
        ),
        credentials=ModelProviderCredentials(),
        budget=LLMModelProviderBudget(
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
        settings: LLMSettings = default_settings,
        logger: logging.Logger = logging.getLogger(__name__),
        **kwargs,
    ):
        self._configuration = settings.configuration
        self._credentials = settings.credentials
        self._budget = settings.budget

        self._logger = logger
        self.custom_config = kwargs.get("custom_config") or {}
        self.extra_headers = kwargs.get("extra_headers") or {}

        if not self._configuration.cache:
            litellm.cache = None
            litellm.cache_responses = False

    async def completion(
        self,
        model_prompt: List[LanguageModelMessage],
        functions: List[LanguageModelFunction],
        model_name: str,
        completion_parser: Callable[[dict], dict],
        callback_handler: Callable = None,
        **kwargs,
    ) -> ModelProviderResponse:
        """Create a completion using the OpenAI API."""
        completion_kwargs = self._get_completion_kwargs(model_name, functions, **kwargs)

        # print("completion_kwargs", completion_kwargs)

        response = await self.acomplete(
            model_prompt,
            **completion_kwargs,
        )
        response_args = {
            "model_info": AI_MODELS[model_name],
            "prompt_tokens_used": response.usage.prompt_tokens,
            "completion_tokens_used": response.usage.completion_tokens,
        }

        parsed_response = completion_parser(response.choices[0].message.dict())
        if callback_handler:
            await callback_handler(
                model_prompt,
                functions,
                response,
                parsed_response,
                response_args,
                **kwargs,
            )
        response = LanguageModelResponse(content=parsed_response, **response_args)
        self._budget.update_usage_and_cost(response)
        return response

    def _convert_delta_to_message(
        self, delta_dict: dict, curr_msg: Optional[litellm.Message] = None
    ) -> litellm.Message:
        """Convert a delta dictionary to a Message object."""
        role = delta_dict.get("role") or "assistant"
        content = delta_dict.get("content") or ""
        additional_kwargs = {}

        if delta_dict.get("function_call"):
            additional_kwargs.update(
                {"function_call": dict(delta_dict["function_call"])}
            )

        tool_calls = delta_dict.get("tool_calls")
        if tool_calls:
            additional_kwargs["tool_calls"] = tool_calls

        return litellm.Message(
            role=role or "assistant", content=content, **additional_kwargs
        )

    async def completion_stream(
        self,
        model_prompt: List[LanguageModelMessage],
        model_name: str,
        *,
        functions: Optional[List[LanguageModelFunction]] = None,
        callback_handler: Optional[Callable] = None,
        completion_parser: Optional[Callable[[dict], Any]] = None,
        **kwargs,
    ) -> AsyncLLMResponseGen:
        """Create a streaming completion using the LiteLLM API."""
        try:
            completion_kwargs = self._get_completion_kwargs(
                model_name, functions, **kwargs
            )
            stream = True
            response_stream = self.acomplete_stream(
                model_prompt, stream=stream, **completion_kwargs
            )

            output_message = None
            async for chunk in response_stream:
                if not hasattr(chunk, "choices") or not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                if not delta:
                    continue
                # Convert delta to message
                delta_dict = delta.dict() if hasattr(delta, "dict") else delta
                message_chunk = self._convert_delta_to_message(
                    delta_dict, output_message
                )

                if output_message is None:
                    output_message = message_chunk
                else:
                    # Merge the new chunk with existing message
                    output_message.content += message_chunk.content
                    if message_chunk.function_call:
                        output_message.function_call.update(message_chunk.function_call)
                    if message_chunk.tool_calls:
                        output_message.tool_calls.extend(message_chunk.tool_calls)

                # Yield the content for streaming
                if message_chunk.content:
                    yield message_chunk.content

            # Create final response
            final_response = self._create_final_response(output_message, model_name)

            # Process final response
            response_args = {
                "model_info": AI_MODELS[model_name],
                "prompt_tokens_used": final_response.usage.prompt_tokens,
                "completion_tokens_used": final_response.usage.completion_tokens,
            }

            parsed_response = completion_parser(
                final_response.choices[0].message.dict()
            )
            response = ModelProviderResponse(content=parsed_response, **response_args)
            self._budget.update_usage_and_cost(response)
            yield response

        except Exception as e:
            self._logger.error(f"Error in streaming completion: {str(e)}")
            raise

    def _create_final_response(
        self, output_message: litellm.Message, model_name: str
    ) -> litellm.ModelResponse:
        """Create a final ModelResponse from the accumulated message."""
        from litellm.utils import ModelResponse, Usage, Choices, Delta

        usage = Usage(
            prompt_tokens=0,  # Will be updated in future
            completion_tokens=0,
            total_tokens=0,
        )

        # Create final delta and choice
        delta = Delta(
            content=output_message.content,
            function_call=output_message.function_call
            if hasattr(output_message, "function_call")
            else None,
            tool_calls=output_message.tool_calls
            if hasattr(output_message, "tool_calls")
            else None,
            role=output_message.role,
        )

        choice = Choices(
            index=0, message=output_message, delta=delta, finish_reason="stop"
        )
        # Create and return final response object
        return ModelResponse(
            id=f"chatcmpl-{int(time.time())}",
            choices=[choice],
            model=model_name,
            usage=usage,
            created=int(time.time()),
        )

    async def acomplete(
        self,
        messages: List[LanguageModelMessage],
        tools: list[dict] | None = None,
        tool_choice: Any | None = None,
        *_,
        **kwargs,
    ) -> litellm.ModelResponse:
        """Async complete the given messages using litellm."""
        try:
            messages = [message.dict() for message in messages]
            if "functions" in kwargs:
                kwargs["functions"] = [
                    function.json_schema for function in kwargs["functions"]
                ]
            else:
                del kwargs["function_call"]

            # print("messages", messages)
            # print("kwargs", kwargs)
            model_name = kwargs.pop("model")
            response = await litellm.acompletion(
                model=f"{model_name}",
                messages=messages,
                tools=tools,
                tool_choice=tool_choice if tools else None,
                stream=False,
                cache=self._configuration.cache,
                **kwargs,
            )
            # response = cast(
            #     litellm.ModelResponse, self._completion(prompt, tools, tool_choice, False)
            # )
            return response
        except Exception as e:
            self._logger.error(f"Error in LiteLLM async completion: {str(e)}")
            raise

    async def acomplete_stream(
        self,
        messages: List[LanguageModelMessage],
        tools: list[dict] | None = None,
        tool_choice: Any | None = None,
        *_,
        **kwargs,
    ) -> AsyncLLMResponseGen:
        """Async stream completion using litellm."""
        try:
            messages = [message.dict() for message in messages]
            if "functions" in kwargs:
                kwargs["functions"] = [
                    function.json_schema for function in kwargs["functions"]
                ]
            elif "function_call" in kwargs:
                del kwargs["function_call"]

            self._logger.debug(f"Streaming messages: {messages}")
            self._logger.debug(f"Streaming kwargs: {kwargs}")

            kwargs.pop("stream", None)  # Ensure stream is not duplicated
            model_name = kwargs.pop("model")

            stream = await litellm.acompletion(
                model=f"{model_name}",
                messages=messages,
                tools=tools,
                tool_choice=tool_choice if tools else None,
                stream=True,
                cache=self._configuration.cache,
                **kwargs,
            )

            async for chunk in stream:
                yield chunk

        except Exception as e:
            self._logger.error(f"Error in LiteLLM streaming: {str(e)}")
            raise

    def get_token_limit(self, model_name: str) -> int:
        """Get the token limit for a given model."""
        return AI_MODELS[model_name].max_tokens

    def get_remaining_budget(self) -> float:
        """Get the remaining budget."""
        return self._budget.remaining_budget

    def get_total_cost(self) -> float:
        """Get the total cost."""
        return self._budget.total_cost

    async def create_embedding(
        self,
        text: str,
        model_name: str,
        embedding_parser: Callable[[Embedding], Embedding],
        **kwargs,
    ) -> EmbeddingModelProviderModelResponse:
        """Create an embedding using the OpenAI API."""
        embedding_kwargs = self._get_embedding_kwargs(model_name, **kwargs)

        # TODO link this to embedding function
        response = await self._create_embedding(text=text, **embedding_kwargs)

        response_args = {
            "model_info": AI_EMBEDDING_MODELS[model_name],
            "prompt_tokens_used": response.usage.prompt_tokens,
            "completion_tokens_used": response.usage.completion_tokens,
        }
        response = EmbeddingModelProviderModelResponse(
            **response_args,
            embedding=embedding_parser(response.embeddings[0]),
        )
        self._budget.update_usage_and_cost(response)
        return response

    def _get_completion_kwargs(
        self,
        model_name: str,
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
            # "max_tokens": self.get_token_limit(model_name),
        }

        if functions:
            completion_kwargs["functions"] = functions

        return completion_kwargs

    def _get_embedding_kwargs(
        self,
        model_name: str,
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
        return "LiteLLMProvider()"

    @classmethod
    def factory(
        cls,
        api_key: Optional[str] = None,
        retries_per_request: int = 10,
        total_budget: float = float("inf"),
        graceful_shutdown_threshold: float = 0.005,
        warning_threshold: float = 0.01,
        logger: Optional[logging.Logger] = None,
    ) -> "LiteLLMProvider":
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

        # Instantiate and return OpenAIProvider
        return cls(settings=settings, logger=logger)

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

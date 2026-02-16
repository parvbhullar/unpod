import abc
import enum
from dataclasses import asdict
from typing import (
    Callable,
    ClassVar,
    List,
    Optional,
    Union,
    Any,
    Generator,
    AsyncGenerator,
)
import json
from functools import wraps
import numpy as np
from pydantic import field_validator, ConfigDict, BaseModel, Field, SecretStr
from pydantic.v1 import validate_arguments

from super.core.configuration import UserConfigurable
from super.core.plugin.base import PluginLocation
from super.core.resource.llm.schema import LanguageModelMessage, LanguageModelFunction
from super.core.resource.schema import (
    Embedding,
    ProviderBudget,
    ProviderCredentials,
    ProviderSettings,
    ProviderUsage,
    ResourceType,
)
from langchain_core.messages import BaseMessageChunk


class ModelProviderService(str, enum.Enum):
    """A ModelService describes what kind of service the model provides."""

    EMBEDDING: str = "embedding"
    LANGUAGE: str = "language"
    TEXT: str = "text"
    IMAGE: str = "text"
    VIDEO: str = "text"


class ModelProviderName(str, enum.Enum):
    OPENAI: str = "openai"
    ANTHROPIC: str = "anthropic"
    HUGGINGFACE: str = "huggingface"
    OLLAMA: str = "ollama"
    TOGETHER: str = "together"
    DEEPINFRA: str = "deepinfra"
    LITELLM: str = "litellm"
    GROQ: str = "groq"
    GOOGLE :str ='google'


class ModelProviderDetail(BaseModel):
    name: ModelProviderName
    location: PluginLocation


class ModelProviderModelInfo(BaseModel):
    """Struct for model information.

    Would be lovely to eventually get this directly from APIs, but needs to be
    scraped from websites for now.

    """

    name: str
    service: ModelProviderService
    provider_name: ModelProviderName
    prompt_token_cost: float = 0.0
    completion_token_cost: float = 0.0


class ModelProviderModelResponse(BaseModel):
    """Standard response struct for a response from a model."""

    prompt_tokens_used: int = 0
    completion_tokens_used: int = 0
    total_cost: float = 0.0
    model_info: ModelProviderModelInfo = None


class ModelProviderCredentials(ProviderCredentials):
    """Credentials for a model provider."""

    api_key: Union[SecretStr, None] = UserConfigurable(default=None)
    api_type: Union[SecretStr, None] = UserConfigurable(default=None)
    api_base: Union[SecretStr, None] = UserConfigurable(default=None)
    api_version: Union[SecretStr, None] = UserConfigurable(default=None)
    deployment_id: Union[SecretStr, None] = UserConfigurable(default=None)

    def unmasked(self) -> dict:
        return unmask(self)

    model_config = ConfigDict(extra="ignore", arbitrary_types_allowed=True)





def unmask(model: BaseModel):
    unmasked_fields = {}
    for field_name, field in model.__fields__.items():
        value = getattr(model, field_name)
        if value:
            if isinstance(value, SecretStr):
                unmasked_fields[field_name] = value.get_secret_value()
            else:
                unmasked_fields[field_name] = value
    return unmasked_fields


class ModelProviderUsage(ProviderUsage):
    """Usage for a particular model from a model provider."""

    completion_tokens: int = 0
    prompt_tokens: int = 0
    total_tokens: int = 0

    def update_usage(
        self,
        model_response: ModelProviderModelResponse,
    ) -> None:
        self.completion_tokens += model_response.completion_tokens_used
        self.prompt_tokens += model_response.prompt_tokens_used
        self.total_tokens += (
            model_response.completion_tokens_used + model_response.prompt_tokens_used
        )


class ModelProviderBudget(ProviderBudget):
    total_budget: Optional[float] = Field(default=np.inf)
    total_cost: float = 0
    remaining_budget: Optional[float] = Field(default=0.0)
    usage: ModelProviderUsage

    def update_usage_and_cost(
        self,
        model_response: ModelProviderModelResponse,
    ) -> Any:
        """Update the usage and cost of the provider."""
        model_info = model_response.model_info
        self.usage.update_usage(model_response)
        incremental_cost = (
            model_response.completion_tokens_used * model_info.completion_token_cost
            + model_response.prompt_tokens_used * model_info.prompt_token_cost
        ) / 1000.0
        arb = 0.0055  # TODO: Fit this or get this from the provider
        cost = incremental_cost + arb
        print("Usage", self.usage)
        print("Cost", round(cost, 4))
        self.total_cost += cost
        self.remaining_budget -= cost
        model_response.total_cost = cost
        return self


class ModelProviderSettings(ProviderSettings):
    resource_type: ResourceType = ResourceType.MODEL
    credentials: ModelProviderCredentials
    budget: ModelProviderBudget


class ModelProvider(abc.ABC):
    """A ModelProvider abstracts the details of a particular provider of models."""

    defaults: ClassVar[ModelProviderSettings]

    @abc.abstractmethod
    def get_token_limit(self, model_name: str) -> int:
        ...

    @abc.abstractmethod
    def get_remaining_budget(self) -> float:
        ...

    @abc.abstractmethod
    def get_total_cost(self) -> float:
        ...


####################
# Embedding Models #
####################


class EmbeddingModelProviderModelInfo(ModelProviderModelInfo):
    """Struct for embedding model information."""

    model_service: ModelProviderService = ModelProviderService.EMBEDDING
    embedding_dimensions: int


class EmbeddingModelProviderModelResponse(ModelProviderModelResponse):
    """Standard response struct for a response from an embedding model."""

    embedding: Embedding = Field(default_factory=list)

    @classmethod
    @field_validator("completion_tokens_used")
    @classmethod
    def _verify_no_completion_tokens_used(cls, v):
        if v > 0:
            raise ValueError("Embeddings should not have completion tokens used.")
        return v


class EmbeddingModelProvider(ModelProvider):
    @abc.abstractmethod
    async def create_embedding(
        self,
        text: str,
        model_name: str,
        embedding_parser: Callable[[Embedding], Embedding],
        **kwargs,
    ) -> EmbeddingModelProviderModelResponse:
        ...


###################
# Language Models #
###################


class LanguageModelProviderModelInfo(ModelProviderModelInfo):
    """Struct for language model information."""

    model_service: ModelProviderService = ModelProviderService.LANGUAGE
    max_tokens: int


class ModelProviderResponse(ModelProviderModelResponse):
    """Standard response struct for a response from a language model."""

    content: dict = None

    def get(self, key, default=None):
        if self.content is None:
            return default
        return self.content.get(key, default)


CompletionModelResponseGen = Generator[
    ModelProviderResponse | BaseMessageChunk | str, None, None
]
AsyncLLMResponseGen = AsyncGenerator[
    ModelProviderResponse | BaseMessageChunk | str, None
]


class LanguageModelProvider(ModelProvider):
    @abc.abstractmethod
    async def completion(
        self,
        model_prompt: List[LanguageModelMessage],
        functions: List[LanguageModelFunction],
        model_name: str,
        completion_parser: Callable[[dict], dict],
        stream: bool = False,
        **kwargs,
    ) -> ModelProviderResponse:
        ...

    @abc.abstractmethod
    async def completion_stream(
        self,
        model_prompt: List[LanguageModelMessage],
        functions: List[LanguageModelFunction],
        model_name: str,
        completion_parser: Callable[[dict], dict],
        stream: bool = False,
        **kwargs,
    ) -> AsyncLLMResponseGen:
        ...


class LanguageModelResponse(ModelProviderResponse):
    """Standard response struct for a response from a language model."""

    @classmethod
    def from_agent_response(cls, agent_response):
        if not isinstance(agent_response, dict):
            agent_response = asdict(agent_response)
        return LanguageModelResponse(content=agent_response)


###################
# Media Models #
###################


class MediaModelProviderModelInfo(ModelProviderModelInfo):
    """Struct for language model information."""

    model_service: ModelProviderService = ModelProviderService.IMAGE
    max_tokens: int


class MediaModelProviderModelResponse(ModelProviderModelResponse):
    """Standard response struct for a response from a language model."""

    content: dict = None


class MediaModelProvider(ModelProvider):
    @abc.abstractmethod
    async def generate(
        self,
        model_prompt: dict,
        model_name: str,
        completion_parser: Callable[[dict], dict],
        **kwargs,
    ) -> MediaModelProviderModelResponse:
        ...

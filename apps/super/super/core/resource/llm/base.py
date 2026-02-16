from abc import ABC, abstractmethod
from typing import Dict, Optional, Any, AsyncIterator

from super.core.handler.config import HandlerConfiguration
from super.core.handler.strategy.base import PromptStrategy
from super.core.resource.llm.schema import LanguageModelPrompt
from super.core.resource.model_providers import LanguageModelProvider
from super.core.resource.model_providers.schema import (
    LanguageModelResponse,
    AsyncLLMResponseGen,
)


class BaseLLM(ABC):
    """Base interface for LLM operations."""

    @abstractmethod
    def __init__(
        self,
        configuration: HandlerConfiguration,
        logger: Optional[Any] = None,
        model_providers: Optional[Dict[str, LanguageModelProvider]] = None,
    ) -> None:
        """Initialize the LLM handler."""
        pass

    @abstractmethod
    def _load_providers(
        self, model_providers: Optional[Dict[str, LanguageModelProvider]] = None
    ) -> None:
        """Load language model providers."""
        pass

    @abstractmethod
    def _setup_prompt_strategy(self) -> None:
        """Set up the prompt strategy based on configuration."""
        pass

    @abstractmethod
    def _make_template_kwargs_for_strategy(
        self, prompt_strategy: PromptStrategy
    ) -> Dict[str, Any]:
        """Create template kwargs for the prompt strategy."""
        pass

    @abstractmethod
    async def chat_stream(
        self, prompt_strategy: PromptStrategy, **kwargs
    ) -> AsyncLLMResponseGen:
        """Stream chat responses from the language model."""
        pass

    @abstractmethod
    async def chat(
        self, prompt_strategy: PromptStrategy, **kwargs
    ) -> LanguageModelResponse:
        """Get a single chat response from the language model."""
        pass

    @abstractmethod
    async def _get_prompt(
        self, prompt_strategy: PromptStrategy, **kwargs
    ) -> LanguageModelPrompt:
        """Get the prompt for the language model."""
        pass

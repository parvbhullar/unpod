import enum
import logging
from typing import List, Dict

from super.core.configuration import SystemConfiguration
from super.core.handler.strategy.config import LanguageModelConfiguration
from super.core.plugin.base import PluginLocation
from super.core.resource.llm.schema import LanguageModelClassification
from super.core.resource.model_providers import AIModelName
from super.core.resource.model_providers.factory import (
    ModelConfigFactory,
    ModelProviderFactory,
)


class ExecutionNature(str, enum.Enum):
    AUTO = "auto"
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"


class RoleConfiguration(SystemConfiguration):
    name: str
    role: str
    id: str = ""
    cycle_count: int = 0
    max_task_cycle_count: int = 3


class HandlerConfiguration(SystemConfiguration):
    """Struct for model configuration."""

    location: PluginLocation = None
    role: RoleConfiguration = None
    execution_nature: ExecutionNature = ExecutionNature.AUTO
    models: Dict[LanguageModelClassification, LanguageModelConfiguration] = None
    callbacks: List[PluginLocation] = None
    prompt_strategy: SystemConfiguration = None
    memory_provider_required: bool = False
    workspace_required: bool = False

    @classmethod
    def factory(cls, **kwargs):
        """Factory method to create a new instance of HandlerConfiguration."""
        logger = kwargs.get("logger", logging.getLogger(__name__))
        prompt_config = kwargs.get("prompt_config", None)
        role_config = kwargs.get("role_config", None)
        smart_model_name = kwargs.get(
            "smart_model_name", AIModelName.OPENAI_GPT4_O_MINI
        )
        fast_model_name = kwargs.get("fast_model_name", AIModelName.OPENAI_GPT4_O_MINI)
        smart_model_temp = kwargs.get("smart_model_temp", 0.7)
        fast_model_temp = kwargs.get("fast_model_temp", 0.7)

        models_config = ModelConfigFactory.get_models_config(
            smart_model_name=smart_model_name,
            fast_model_name=fast_model_name,
            smart_model_temp=smart_model_temp,
            fast_model_temp=fast_model_temp,
        )

        # Initialize settings
        config = cls()
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
        return config

from typing import Union, Any

from super.core.configuration import SystemConfiguration, UserConfigurable
from super.core.resource.llm.schema import LanguageModelClassification
from super.core.resource.model_providers import ModelProviderName


class LanguageModelConfiguration(SystemConfiguration):
    """Struct for model configuration."""

    model_name: str = UserConfigurable()
    provider_name: ModelProviderName = UserConfigurable()
    temperature: float = UserConfigurable()


class PromptStrategyConfiguration(SystemConfiguration):
    model_classification: LanguageModelClassification = UserConfigurable()
    system_prompt: str = UserConfigurable()
    user_prompt_template: str = UserConfigurable()
    parser_schema: Union[dict, None] = None
    location: Any = None

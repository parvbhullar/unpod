import logging
import os
from typing import Dict

from super.core.handler.strategy.config import LanguageModelConfiguration
from super.core.plugin.simple import (
    PluginLocation,
    PluginStorageFormat,
    SimplePluginService,
)
from super.core.configuration import SystemConfiguration, SystemSettings
from super.core.resource.llm.schema import LanguageModelClassification
from super.core.resource.model_providers import (
    OPEN_AI_MODELS,
    ANTHROPIC_MODELS,
    OLLAMA_MODELS,
    AIModelName,
    LanguageModelProvider,
    ModelProviderName,
)

from super.core.resource.model_providers.deepinfra import DEEP_INFRA_MODELS
from super.core.resource.model_providers.openai import OPEN_AI_EMBEDDING_MODELS


class ModelProviderConfiguration(SystemConfiguration):
    user_configuration: Dict = dict()
    location: PluginLocation


class ProviderFactorySettings(SystemSettings):
    models: Dict[str, ModelProviderConfiguration]


class ModelProviderFactory:
    default_settings = ProviderFactorySettings(
        name="simple_model_provider_factory",
        description="A simple model provider factory.",
        models={
            ModelProviderName.OPENAI: ModelProviderConfiguration(
                user_configuration={},
                location=PluginLocation(
                    storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
                    storage_route="super.core.resource.model_providers.LiteLLMProvider",
                ),
            ),
            ModelProviderName.ANTHROPIC: ModelProviderConfiguration(
                user_configuration={},
                location=PluginLocation(
                    storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
                    storage_route="super.core.resource.model_providers.LiteLLMProvider",
                ),
            ),
            ModelProviderName.DEEPINFRA: ModelProviderConfiguration(
                user_configuration={"api_key": os.environ.get("DEEPINFRA_API_KEY")},
                location=PluginLocation(
                    storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
                    storage_route="super.core.resource.model_providers.DeepInfraProvider",
                ),
            ),
        },
    )

    def __init__(
        self,
        settings: ProviderFactorySettings,
        logger: logging.Logger,
        model_providers: Dict[ModelProviderName, LanguageModelProvider] = None,
    ):
        self._settings = settings
        self._logger = logger
        self._model_providers = model_providers

    @classmethod
    def factory(
        cls,
        model_provider_configs: Dict[
            ModelProviderName, ModelProviderConfiguration
        ] = None,
        logger: logging.Logger = None,
    ):
        if logger is None:
            logger = logging.getLogger(cls.__name__)
        model_providers = cls.load_providers(
            model_provider_configs=model_provider_configs,
            logger=logger,
        )
        return cls(
            settings=cls.default_settings,
            logger=logger,
            model_providers=model_providers,
        )

    @classmethod
    def load_providers(
        cls,
        model_provider_configs: Dict[
            ModelProviderName, ModelProviderConfiguration
        ] = None,
        logger: logging.Logger = None,
    ):
        if logger is None:
            logger = logging.getLogger(cls.__name__)

        if model_provider_configs is not None:
            cls.default_settings.models.update(model_provider_configs)

        model_providers = {}
        for model_provider_name, config in cls.default_settings.models.items():
            model_providers.update(
                {
                    model_provider_name: cls._get_model_provider_instance(
                        config.user_configuration,
                        config.location,
                        logger,
                    )
                }
            )

        return model_providers

    @classmethod
    def _get_model_provider_instance(
        cls,
        user_configuration: dict,
        location: PluginLocation,
        logger: logging.Logger,
        *args,
        **kwargs,
    ):
        model_provider_class = SimplePluginService.get_plugin(location)
        model_provider_settings = model_provider_class.init_settings(
            **user_configuration
        )
        model_provider_parameter = model_provider_class.__init__.__annotations__
        model_provider_kwargs = {}
        for key in kwargs:
            if key in model_provider_parameter:
                model_provider_kwargs[key] = kwargs[key]
        if "logger" in model_provider_parameter:
            model_provider_kwargs["logger"] = logger.getChild(
                model_provider_class.__name__
            )
        model_provider_instance = model_provider_class(
            model_provider_settings,
            *args,
            **model_provider_kwargs,
        )
        return model_provider_instance


class ModelConfigFactory:
    AI_MODELS = {
        **OPEN_AI_MODELS,
        **ANTHROPIC_MODELS,
        **OLLAMA_MODELS,
        **DEEP_INFRA_MODELS,
    }

    def __init__(self):
        pass

    def get_ai_models(self):
        return self.AI_MODELS

    @classmethod
    def get_ai_model(cls, model_name):
        return cls.AI_MODELS[model_name]

    @classmethod
    def get_models_config(
        cls,
        smart_model_name=AIModelName.OPENAI_GPT4,
        fast_model_name=AIModelName.OPENAI_GPT3_16K,
        smart_model_temp=0.2,
        fast_model_temp=0.2,
    ):
        smart_model = cls.get_ai_model(smart_model_name)
        fast_model = cls.get_ai_model(fast_model_name)
        models_config = {
            LanguageModelClassification.SMART_MODEL: LanguageModelConfiguration(
                model_name=smart_model.name,
                provider_name=smart_model.provider_name,
                temperature=smart_model_temp,
            ),
            LanguageModelClassification.FAST_MODEL: LanguageModelConfiguration(
                model_name=fast_model.name,
                provider_name=fast_model.provider_name,
                temperature=fast_model_temp,
            ),
        }
        return models_config


def load_model_provider(provider_name: ModelProviderName, user_configuration={}):
    from super.core.resource.model_providers.contants import MODEL_PROVIDERS_DICT

    provider_location = MODEL_PROVIDERS_DICT.get(provider_name).location
    logger = logging.getLogger(__name__)
    return ModelProviderFactory._get_model_provider_instance(
        user_configuration, provider_location, logger
    )


# Usage example
if __name__ == "__main__":
    model_provider_list = ModelProviderFactory.load_providers()
    print(model_provider_list)

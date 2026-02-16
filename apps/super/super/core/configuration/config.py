from __future__ import annotations
import os
from pathlib import Path
from typing import Optional, List
from super.core.configuration import SystemSettings, Configurable
from functools import lru_cache


class Config(SystemSettings, arbitrary_types_allowed=True):
    name: str = "Super configuration"
    description: str = "Default configuration for the Super application."
    ########################
    # Application Settings #
    ########################
    debug_mode: bool = False
    # OpenAI
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    together_api_key: Optional[str] = None
    deepinfra_api_key: Optional[str] = None

    # Google
    google_api_key: Optional[str] = None
    google_custom_search_engine_id: Optional[str] = None
    # Huggingface
    huggingface_api_token: Optional[str] = None
    # Stable Diffusion
    sd_webui_auth: Optional[str] = None
    # SerpAPI
    serp_api_key: Optional[str] = None

    fast_llm_model: Optional[str] = None

    smart_llm_model: Optional[str] = None

    plugins: Optional[List] = []

    stability_api_key: Optional[str] = None

    stability_engine_id: Optional[str] = None

    clipdrop_api_key: Optional[str] = None

    web_proxy: Optional[List] = []

    selenium_browser_type: Optional[str] = None

    scraperapi_api_key: Optional[str] = None


class ConfigBuilder(Configurable[Config]):
    default_settings = Config()

    @classmethod
    def build_config_from_env(cls, workdir: Path = None) -> Config:
        config_dict_without_none_values = cls.load_env(workdir)

        config = cls.build_configuration(config_dict_without_none_values)

        # Set secondary config variables (that depend on other config variables)

        # config.plugins_config = PluginsConfig.load_config(
        #     config.workdir / config.plugins_config_file,
        #     config.plugins_denylist,
        #     config.plugins_allowlist,
        # )

        return config

    @classmethod
    def load_env(cls, workdir):
        """Initialize the Config class"""
        config_dict = {
            "debug_mode": os.getenv("DEBUG_MODE", "False") == "True",
            "github_api_key": os.getenv("GITHUB_API_KEY"),
            "github_username": os.getenv("GITHUB_USERNAME"),
            "google_api_key": os.getenv("GOOGLE_API_KEY"),
            "serp_api_key": os.getenv("SERP_API_KEY"),
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
            "google_custom_search_engine_id": os.getenv("CUSTOM_SEARCH_ENGINE_ID"),
            "fast_llm_model": os.getenv("FAST_LLM_MODEL"),
            "smart_llm_model": os.getenv("SMART_LLM_MODEL"),
            "stability_api_key": os.getenv("STABILITY_API_KEY"),
            "stability_engine_id": os.getenv("STABILITY_ENGINE_ID"),
            "clipdrop_api_key": os.getenv("CLIPDROP_API_KEY"),
            "web_proxy": os.getenv("WEB_PROXY", "").split(","),
            "selenium_browser_type": os.getenv("SELENIUM_BROWSER_TYPE", "chrome"),
            "scraperapi_api_key": os.getenv("SCRAPERAPI_API_KEY"),
            "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
            "together_api_key": os.getenv("TOGETHER_API_KEY"),
            "deepinfra_api_key": os.getenv("DEEPINFRA_API_KEY"),
        }

        config_dict_without_none_values = {
            k: v for k, v in config_dict.items() if v is not None
        }
        return config_dict_without_none_values


@lru_cache()
def get_config(configuration=Path(__file__).parent.parent.parent) -> Config:
    """
    Returns the config object.
    """
    config = ConfigBuilder.build_config_from_env(configuration)
    return config

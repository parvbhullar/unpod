import os
import litellm
from libs.api.logger import get_logger

app_logging = get_logger("search_service")

# Silence litellm telemetry
litellm.telemetry = False
litellm.drop_params = True


def get_llm_config():
    """Get LLM config from MongoDB, falling back to environment variables."""
    try:
        from services.search_service.models.llm_provider import LLMProviderModel

        provider = LLMProviderModel.find_one(is_default=True)
        if provider:
            return {
                "provider": provider.provider,
                "model": provider.model_name,
                "api_key": provider.api_key,
                "api_base": provider.api_base,
                "api_version": provider.api_version,
                "custom_config": provider.custom_config or {},
            }
    except Exception as e:
        app_logging.debug("Could not load LLM config from MongoDB", str(e))

    return {
        "provider": os.environ.get("LLM_PROVIDER", "openai"),
        "model": os.environ.get("LLM_MODEL", "gpt-4"),
        "api_key": os.environ.get("LLM_API_KEY"),
        "api_base": os.environ.get("LLM_API_BASE"),
        "api_version": os.environ.get("LLM_API_VERSION"),
        "custom_config": {},
    }


def _build_model_string(config):
    """Build litellm model string from config."""
    provider = config.get("provider", "openai")
    model = config.get("model", "gpt-4")
    if provider and provider != "openai" and not model.startswith(f"{provider}/"):
        return f"{provider}/{model}"
    return model


def llm_invoke(messages, config=None, temperature=0.7, max_tokens=4096):
    """Call LLM and return full response."""
    if config is None:
        config = get_llm_config()

    model_str = _build_model_string(config)
    response = litellm.completion(
        model=model_str,
        messages=messages,
        api_key=config.get("api_key"),
        api_base=config.get("api_base"),
        api_version=config.get("api_version"),
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


def llm_stream(messages, config=None, temperature=0.7, max_tokens=4096):
    """Stream LLM response, yielding token strings."""
    if config is None:
        config = get_llm_config()

    model_str = _build_model_string(config)
    response = litellm.completion(
        model=model_str,
        messages=messages,
        api_key=config.get("api_key"),
        api_base=config.get("api_base"),
        api_version=config.get("api_version"),
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )
    for chunk in response:
        delta = chunk.choices[0].delta
        if delta and delta.content:
            yield delta.content

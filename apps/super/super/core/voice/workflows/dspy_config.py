"""
Thread-safe DSPy LM configuration manager for multi-process environments.

This module provides a singleton configuration manager that creates process-local
DSPy LM instances, avoiding threading conflicts when running in environments like
Prefect with DaskTaskRunner or ProcessPoolExecutor.

Usage:
    from super.core.voice.workflows.dspy_config import get_dspy_lm

    # Get a process-local LM instance
    lm = get_dspy_lm()

    # Use in DSPy modules
    class MyModule(dspy.Module):
        def __init__(self, lm=None):
            super().__init__()
            self.lm = lm or get_dspy_lm()

        def forward(self, ...):
            with dspy.context(lm=self.lm):
                # Your DSPy logic here
                pass
"""

import os
import threading
import dspy
from dotenv import load_dotenv

load_dotenv(override=True)


class DSPyConfig:
    """
    Thread-safe DSPy LM configuration manager using process-local storage.

    This singleton class ensures that each process/thread gets its own DSPy LM
    instance, preventing the "dspy.settings can only be changed by the thread
    that initially configured it" error.

    The class uses threading.local() to store process-local LM instances, ensuring
    that each worker process in a ProcessPoolExecutor or Prefect DaskTaskRunner
    gets its own independent LM configuration.
    """

    _instance = None
    _lock = threading.Lock()
    _process_local = threading.local()

    def __new__(cls):
        """Singleton pattern with thread-safe initialization."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    # Maps provider prefix to the env var holding its API key.
    PROVIDER_API_KEY_MAP = {
        "openai": "OPENAI_API_KEY",
        "google": "GOOGLE_API_KEY",
        "gemini": "GOOGLE_API_KEY",
        "groq": "GROQ_API_KEY",
    }

    # OpenAI reasoning models require temperature=1.0 and max_tokens>=16000.
    # Model name substring matches (case-insensitive).
    OPENAI_REASONING_MODELS = {"o1", "o3", "o4", "gpt-5"}

    @classmethod
    def _resolve_api_key(cls, model_name: str) -> str:
        """Resolve the correct API key env var based on model provider prefix.

        Supported prefixes:
          - openai/*   -> OPENAI_API_KEY
          - google/*   -> GOOGLE_API_KEY
          - gemini/*   -> GOOGLE_API_KEY
          - groq/*     -> GROQ_API_KEY

        Falls back to OPENAI_API_KEY for unknown providers.
        """
        provider = model_name.split("/")[0].lower() if "/" in model_name else ""
        env_var = cls.PROVIDER_API_KEY_MAP.get(provider, "OPENAI_API_KEY")
        api_key = os.getenv(env_var)
        if not api_key:
            raise ValueError(
                f"{env_var} environment variable is not set "
                f"(required for model '{model_name}')"
            )
        return api_key

    @classmethod
    def _is_openai_reasoning_model(cls, model_name: str) -> bool:
        """Check if model is an OpenAI reasoning model that needs special params."""
        provider = model_name.split("/")[0].lower() if "/" in model_name else ""
        if provider != "openai":
            return False
        model_part = model_name.split("/", 1)[1].lower() if "/" in model_name else ""
        return any(tag in model_part for tag in cls.OPENAI_REASONING_MODELS)

    def get_lm(
        self,
        model_name: str = None,
        temperature: float = None,
    ):
        """Get or create process-local LM instance.

        Resolution order for each param:
        1. Explicit argument
        2. Environment variable (ANALYSIS_MODEL_NAME / ANALYSIS_LLM_TEMPERATURE)
        3. Hardcoded default ('openai/gpt-5-mini' / 0.7)

        Supported providers (via model name prefix):
        - openai/gpt-4o, openai/gpt-4o-mini, openai/gpt-5-mini, etc.
        - openai/o1, openai/o3, openai/o4-mini (reasoning models)
        - google/gemini-2.5-flash, gemini/gemini-2.5-pro, etc.
        - groq/qwen3-32b, groq/llama-3.3-70b, etc.

        OpenAI reasoning models (o1, o3, o4, gpt-5) automatically get
        temperature=1.0 and max_tokens=16000 as required by the API.
        """
        resolved_model = (
            model_name
            or os.getenv("ANALYSIS_MODEL_NAME")
            or "openai/gpt-5-mini"
        )

        is_reasoning = self._is_openai_reasoning_model(resolved_model)

        if is_reasoning:
            # Reasoning models require temperature=1.0 and max_tokens>=16000
            resolved_temp = 1.0
            max_tokens = 16000
        else:
            resolved_temp = (
                temperature
                if temperature is not None
                else float(os.getenv("ANALYSIS_LLM_TEMPERATURE", "0.7"))
            )
            max_tokens = None

        cache_key = (resolved_model, resolved_temp, max_tokens)

        cached_key = getattr(self._process_local, "lm_key", None)
        cached_lm = getattr(self._process_local, "lm", None)

        if cached_lm is not None and cached_key == cache_key:
            return cached_lm

        api_key = self._resolve_api_key(resolved_model)

        lm_kwargs = {
            "api_key": api_key,
            "temperature": resolved_temp,
        }
        if max_tokens is not None:
            lm_kwargs["max_tokens"] = max_tokens

        lm = dspy.LM(resolved_model, **lm_kwargs)
        self._process_local.lm = lm
        self._process_local.lm_key = cache_key
        return lm


def get_dspy_lm(
    model_name: str = None,
    temperature: float = None,
):
    """Convenience function to get thread-safe DSPy LM instance.

    Reads defaults from env vars ANALYSIS_MODEL_NAME and ANALYSIS_LLM_TEMPERATURE.
    Falls back to 'openai/gpt-4o-mini' and 0.7.

    Supports multiple providers — set the model name with the provider prefix:
      - ANALYSIS_MODEL_NAME=openai/gpt-4o-mini  (needs OPENAI_API_KEY)
      - ANALYSIS_MODEL_NAME=google/gemini-2.5-flash  (needs GOOGLE_API_KEY)
      - ANALYSIS_MODEL_NAME=groq/qwen3-32b  (needs GROQ_API_KEY)
    """
    return DSPyConfig().get_lm(model_name=model_name, temperature=temperature)

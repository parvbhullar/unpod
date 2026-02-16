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

    def get_lm(self, model_name='openai/gpt-4o-mini'):
        """
        Get or create process-local LM instance.

        Args:
            model_name: Name of the model to use (default: 'openai/gpt-4o-mini')

        Returns:
            dspy.LM: A process-local DSPy LM instance

        Note:
            This method creates a new LM instance for each process/thread on first call,
            then reuses it for subsequent calls within the same process/thread.
        """
        if not hasattr(self._process_local, 'lm') or self._process_local.lm is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is not set")
            self._process_local.lm = dspy.LM(model_name, api_key=api_key)
        return self._process_local.lm


def get_dspy_lm(model_name='openai/gpt-4o-mini'):
    """
    Convenience function to get thread-safe DSPy LM instance.

    This is the recommended way to get a DSPy LM instance in multi-process
    environments like Prefect or ProcessPoolExecutor.

    Args:
        model_name: Name of the model to use (default: 'openai/gpt-4o-mini')

    Returns:
        dspy.LM: A process-local DSPy LM instance

    Example:
        >>> lm = get_dspy_lm()
        >>> with dspy.context(lm=lm):
        ...     result = predictor(input="...")
    """
    return DSPyConfig().get_lm(model_name)

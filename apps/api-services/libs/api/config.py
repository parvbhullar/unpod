"""Shared Settings Configuration Module.

Provides parameterized Settings class that can optionally initialize database connections.
Used by all services in the mono-repo.
"""

import logging
import os
from importlib import import_module
from functools import lru_cache
from starlette.datastructures import State
from libs.core.exceptions import ImproperlyConfigured
from fastapi.templating import Jinja2Templates


class Settings(State):
    """Settings class with optional database connection initialization.

    Args:
        init_db_connections: If True, initialize MySQL/Postgres connections (default: True)
        service_overrides: Dict of service-specific setting overrides
    """

    def __init__(
        self, init_db_connections=True, service_overrides=None, *args, **kwargs
    ):
        SETTINGS_MODULE = os.environ.setdefault("SETTINGS_FILE", "settings.local")
        logging.info("Running Server Using Settings Module: %s", SETTINGS_MODULE)
        settings_module = import_module(SETTINGS_MODULE)
        if not settings_module:
            desc = "setting '%s'" % SETTINGS_MODULE
            raise ImproperlyConfigured(
                "Requested %s, but settings are not configured." % desc
            )
        super().__init__(*args, **kwargs)
        self._state["SETTINGS_MODULE"] = SETTINGS_MODULE
        self._state["ENV_NAME"] = SETTINGS_MODULE.split(".")[1].upper()
        for key, value in settings_module.__dict__.items():
            self._state[key] = value

        # Apply service-specific overrides if provided
        if service_overrides:
            for key, value in service_overrides.items():
                self._state[key] = value

        # Initialize templates if directory exists
        if "TEMPLATE_DIR" in self._state:
            if not os.path.exists(self._state["TEMPLATE_DIR"]):
                raise ImproperlyConfigured(
                    "Template Dir Provided Does Not Exist, Please First Create the Dir"
                )
            self._state["templates"] = Jinja2Templates(
                directory=self._state["TEMPLATE_DIR"]
            )

        # Initialize database connections if requested
        if init_db_connections:
            if "POSTGRES_CONFIG" in self._state:
                import psycopg2

                self._state["postgres_conn"] = psycopg2.connect(
                    **self._state["POSTGRES_CONFIG"]
                )


@lru_cache()
def get_settings(init_db_connections=True, service_overrides=None):
    """Get cached settings instance.

    Args:
        init_db_connections: If True, initialize database connections
        service_overrides: Dict of service-specific overrides

    Returns:
        Settings instance
    """
    return Settings(
        init_db_connections=init_db_connections, service_overrides=service_overrides
    )

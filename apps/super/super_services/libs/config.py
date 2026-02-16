import os
from importlib import import_module
from functools import lru_cache
from starlette.datastructures import State
from super_services.libs.core.exceptions import ImproperlyConfigured
from fastapi.templating import Jinja2Templates
import psycopg2


class Settings(State):
    def __init__(self, *args, **kwargs):
        SETTINGS_MODULE = os.environ.setdefault(
            "SETTINGS_FILE", "super_services.settings.local"
        )
        print("Running Server Using Settings Module", SETTINGS_MODULE)
        settings_module = import_module(SETTINGS_MODULE)
        if not settings_module:
            desc = "setting '%s'" % SETTINGS_MODULE
            raise ImproperlyConfigured(
                "Requested %s, but settings are not configured." % desc
            )
        super().__init__(*args, **kwargs)
        self._state["SETTINGS_MODULE"] = SETTINGS_MODULE
        self._state["ENV_NAME"] = SETTINGS_MODULE.split(".")[-1].upper()
        for key, value in settings_module.__dict__.items():
            self._state[key] = value
        if "TEMPLATE_DIR" in self._state:
            if not os.path.exists(self._state["TEMPLATE_DIR"]):
                raise ImproperlyConfigured(
                    f"Template Dir Provide Not Exists, Please First Create the Dir"
                )
            self._state["templates"] = Jinja2Templates(
                directory=self._state["TEMPLATE_DIR"]
            )
        # Validate PostgreSQL connection
        if "POSTGRES_CONFIG" in self._state:
            conn = None
            try:
                conn = psycopg2.connect(**self._state["POSTGRES_CONFIG"])
            except psycopg2.OperationalError as e:
                raise ImproperlyConfigured(
                    f"Failed to connect to PostgreSQL: {e}"
                ) from e
            finally:
                if conn:
                    conn.close()


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()

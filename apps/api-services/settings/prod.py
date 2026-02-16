# flake8: noqa

from .base import *

MONGO_DB = os.environ.get("MONGO_DB", "messaging_service_prod")

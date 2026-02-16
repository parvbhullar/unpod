import logging
import logging.config
import os
from datetime import datetime

import yaml

from libs.core.datetime import tz

LOG_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs"
)
LOG_FORMAT = (
    "[%(asctime)s.%(msecs)03dZ] - %(name)s - %(lineno)d - %(levelname)s - %(message)s"
)
LOG_DATEFMT = "%Y-%m-%d %H:%M:%S"
MAX_BYTES = 10485760  # 10MB
BACKUP_COUNT = 5

_config_loaded = False
_registered_loggers = set()


def timetz(*args):
    return datetime.now(tz).timetuple()


def _load_config():
    global _config_loaded
    if _config_loaded:
        return
    config_file = "config.yaml"
    if os.path.exists(config_file):
        with open(config_file) as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
            logging.config.dictConfig(config)
    logging.Formatter.converter = timetz
    os.makedirs(LOG_DIR, exist_ok=True)
    _config_loaded = True


def _setup_logger(service_name):
    """Dynamically register file handlers for a service name."""
    if service_name in _registered_loggers:
        return logging.getLogger(service_name)

    _load_config()

    logger = logging.getLogger(service_name)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATEFMT)
    formatter.converter = timetz

    # Console handler
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # File handler — logs/{service_name}.log (INFO+)
    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(LOG_DIR, f"{service_name}.log"),
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf8",
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Error file handler — logs/{service_name}.error (ERROR+)
    error_handler = logging.handlers.RotatingFileHandler(
        os.path.join(LOG_DIR, f"{service_name}.error"),
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

    logger.propagate = False
    _registered_loggers.add(service_name)
    return logger


def get_logger(service_name="app"):
    """
    Get a logger instance for a service.

    Dynamically creates:
      - Console handler (INFO+)
      - logs/{service_name}.log (INFO+, rotating 10MB x 5)
      - logs/{service_name}.error (ERROR+, rotating 10MB x 5)

    Args:
        service_name: Name of the service (e.g., 'store_service', 'search_service')

    Returns:
        Logger wrapper instance
    """

    class Logger:
        def __init__(self):
            self.logger = _setup_logger(service_name)

        def _format_args(self, *args):
            return " ~ ".join(str(a) for a in args)

        def log(self, *args):
            self.logger.info(self._format_args(*args))

        def info(self, *args):
            self.logger.info(self._format_args(*args))

        def debug(self, *args):
            self.logger.debug(self._format_args(*args))

        def warning(self, *args):
            self.logger.warning(self._format_args(*args))

        def error(self, *args):
            self.logger.error(self._format_args(*args))

        def exception(self, *args):
            self.logger.exception(self._format_args(*args))

    return Logger()

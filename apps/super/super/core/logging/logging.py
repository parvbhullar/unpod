import logging
from datetime import datetime


def configure_third_party_logging() -> None:
    """Suppress verbose logging from third-party libraries."""
    # Suppress verbose PyMongo debug logs
    logging.getLogger("pymongo").setLevel(logging.WARNING)
    logging.getLogger("pymongo.topology").setLevel(logging.WARNING)
    logging.getLogger("pymongo.connection").setLevel(logging.WARNING)
    logging.getLogger("pymongo.command").setLevel(logging.WARNING)
    logging.getLogger("pymongo.serverSelection").setLevel(logging.WARNING)


# Apply third-party logging configuration on module import
configure_third_party_logging()


def get_logger(
    logger_name: str = "application_logger",
    level: int = logging.DEBUG,
    propagate: bool = False,
) -> logging.Logger:
    """Get or create a logger with the specified name.

    This function ensures that handlers are only added once per logger,
    preventing duplicate log entries when the same logger is retrieved
    multiple times.

    Args:
        logger_name: The name of the logger (supports hierarchical names like "a.b.c")
        level: The logging level (default: DEBUG)
        propagate: Whether to propagate to parent loggers (default: False).
                   When False, prevents duplicate logs when both this logger
                   and root/parent loggers have handlers configured.

    Returns:
        Configured logger instance
    """
    client_logger = logging.getLogger(logger_name)
    client_logger.setLevel(level)

    # Only add handler if this logger doesn't already have handlers
    # This prevents duplicate log entries when get_logger is called multiple times
    if not client_logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(formatter)

        client_logger.addHandler(ch)

        # Set propagation - default False to prevent duplicate logs
        # when root logger also has handlers (e.g., from logging.basicConfig)
        client_logger.propagate = propagate

    return client_logger


def print_log(*args):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]", *args)
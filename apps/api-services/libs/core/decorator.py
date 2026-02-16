import functools
import threading
import time

from libs.api.logger import get_logger


def runMethodInThread(fn):
    """
    Decorator to run a function in a daemon thread.

    Args:
        fn: Function to run in thread

    Returns:
        Wrapper function that starts the thread
    """

    @functools.wraps(fn)
    def inner(*args, **kw):
        t = threading.Thread(target=fn, args=args, kwargs=kw)
        t.daemon = True
        t.start()
        return t

    return inner


def logTime(fn=None, logger=None):
    """
    Decorator to log execution time of a function.

    Can be used as @logTime or @logTime(logger=my_logger)

    Args:
        fn: Function to wrap (when used as @logTime)
        logger: Optional logger instance (defaults to module logger)

    Returns:
        Decorated function or decorator
    """

    def decorator(func):
        @functools.wraps(func)
        def inner(*args, **kw):
            nonlocal logger
            if logger is None:
                logger = get_logger(func.__module__)

            t1 = time.time()
            result = func(*args, **kw)
            t2 = time.time()
            logger.debug(
                f"Time Taken in Method {func.__name__}: {round(t2-t1, 4)} Secs"
            )
            return result

        return inner

    # Handle both @logTime and @logTime(logger=...)
    if fn is None:
        return decorator
    else:
        return decorator(fn)

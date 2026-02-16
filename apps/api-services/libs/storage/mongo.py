from mongomantic.core.database import MongomanticClient
from libs.api.logger import get_logger

_default_logger = get_logger("mongo")


def perform_mongo_method(collection, method, query, *args, logger=None, **kwargs):
    """
    Perform a MongoDB method on a collection.

    Args:
        collection: Collection name
        method: Method name to call on the collection
        query: Query to execute
        *args: Additional positional arguments
        logger: Optional logger instance (defaults to module logger)
        **kwargs: Additional keyword arguments

    Returns:
        Result of the method call or None on error
    """
    if logger is None:
        logger = _default_logger

    client = MongomanticClient.db[collection]
    try:
        result = getattr(client, method)(query, *args, **kwargs)
        return result
    except Exception as e:
        logger.error(f"Error performing {method} on {collection}: {e}")
        return None

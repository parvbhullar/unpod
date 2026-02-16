import logging
from django.conf import settings
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from unpod.common.exception import MongoDBQueryNotFound

logger = logging.getLogger(__name__)


class MongoDBQueryManager:
    _client = None
    _db = None

    @classmethod
    def _get_db(cls):
        """Get or create the MongoDB database connection."""
        if cls._db is None:
            try:
                # Create new client with current settings
                cls._client = MongoClient(
                    settings.MONGO_DSN,
                    serverSelectionTimeoutMS=10000,
                    connectTimeoutMS=10000,
                    socketTimeoutMS=30000,  # 30s timeout for query operations
                )
                cls._db = cls._client.get_database(settings.MONGO_DB)
                logger.info(f"MongoDB connected to database: {settings.MONGO_DB}")
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
                raise
        return cls._db

    @classmethod
    def run_query(cls, collection, query_type, query_dict, **kwargs):
        db = cls._get_db()
        if hasattr(db[collection], query_type):
            return getattr(db[collection], query_type)(query_dict, **kwargs)
        raise MongoDBQueryNotFound(f"Invalid query type: {query_type}")

    @classmethod
    def get_collection(cls, collection_name):
        db = cls._get_db()
        return db[collection_name]

    @classmethod
    def reset_connection(cls):
        """Reset the connection (useful for testing or reconnection)."""
        if cls._client:
            cls._client.close()
        cls._client = None
        cls._db = None

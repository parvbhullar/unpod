import sys
from unittest.mock import MagicMock


def pytest_configure(config):
    """Disable the nameko plugin to avoid eventlet issues"""
    config.pluginmanager.set_blocked("nameko")

    # Mock mongomantic to avoid pydantic version conflicts
    mongomantic_mock = MagicMock()
    # Provide mock classes that don't have metaclass conflicts
    mongomantic_mock.MongoDBModel = type("MongoDBModel", (), {})
    mongomantic_mock.BaseRepository = type("BaseRepository", (), {})
    mongomantic_mock.Index = MagicMock()
    mongomantic_mock.connect = MagicMock()
    sys.modules["mongomantic"] = mongomantic_mock

    # Mock bson module for MongoDB dependencies
    bson_mock = MagicMock()
    bson_mock.ObjectId = MagicMock()
    bson_mock.Decimal128 = MagicMock()
    sys.modules["bson"] = bson_mock

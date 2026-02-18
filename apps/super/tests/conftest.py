import sys
import types
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

    # Mock bson module for MongoDB dependencies. Use real module objects so
    # imports like `from bson.objectid import InvalidId` keep working.
    bson_module = types.ModuleType("bson")
    bson_objectid_module = types.ModuleType("bson.objectid")
    bson_decimal128_module = types.ModuleType("bson.decimal128")
    bson_errors_module = types.ModuleType("bson.errors")

    class InvalidId(Exception):
        """Stub bson InvalidId error used by model helpers."""

    bson_objectid_module.InvalidId = InvalidId
    bson_objectid_module.ObjectId = MagicMock()
    bson_decimal128_module.Decimal128 = MagicMock()
    bson_errors_module.InvalidId = InvalidId

    bson_module.ObjectId = bson_objectid_module.ObjectId
    bson_module.Decimal128 = bson_decimal128_module.Decimal128
    bson_module.objectid = bson_objectid_module
    bson_module.decimal128 = bson_decimal128_module
    bson_module.errors = bson_errors_module

    sys.modules["bson"] = bson_module
    sys.modules["bson.objectid"] = bson_objectid_module
    sys.modules["bson.decimal128"] = bson_decimal128_module
    sys.modules["bson.errors"] = bson_errors_module

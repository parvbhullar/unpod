"""
Database abstraction layer.

This module provides a unified interface for database operations,
routing to the PostgreSQL implementation.

For backward compatibility, executeMysqlQuery is aliased to executeQuery.
"""

from super_services.libs.core.postgres import (
    executeQuery,
    get_connection,
    close_pool,
)

# Backward compatibility alias
executeMysqlQuery = executeQuery

__all__ = [
    "executeQuery",
    "executeMysqlQuery",
    "get_connection",
    "close_pool",
]

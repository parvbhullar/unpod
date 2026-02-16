"""
MySQL Connection Pool with process-aware management.

Key optimizations:
- Reduced pool size per process (2 connections)
- Connection timeout and retry logic
- Proper error handling for exhausted pools
- Process-aware pool naming to avoid conflicts
"""

import logging
import os
import time
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Union

from mysql.connector import pooling
from mysql.connector.errors import PoolError, DatabaseError

from super_services.libs.config import settings

logger = logging.getLogger(__name__)

_pool = None
_pool_pid = None  # Track which process owns the pool


def _get_pool():
    """
    Get or create the connection pool for the current process.

    Each process gets its own pool with a small size (2 connections).
    Pool is recreated if accessed from a different process (fork safety).
    """
    global _pool, _pool_pid

    current_pid = os.getpid()

    # Recreate pool if we're in a new process (fork happened)
    if _pool is not None and _pool_pid != current_pid:
        logger.debug(
            f"Process forked (was {_pool_pid}, now {current_pid}), recreating pool"
        )
        _pool = None

    if _pool is None:
        pool_name = f"app_pool_{current_pid}"
        try:
            _pool = pooling.MySQLConnectionPool(
                pool_name=pool_name,
                pool_size=2,  # Minimal per-process (prevents exhaustion)
                pool_reset_session=True,
                connection_timeout=10,  # 10 second connection timeout
                **settings.MYSQL_CONFIG,
            )
            _pool_pid = current_pid
            logger.debug(f"Created MySQL pool '{pool_name}' with size 2")
        except DatabaseError as e:
            logger.error(f"Failed to create MySQL pool: {e}")
            raise

    return _pool


def close_pool():
    """Close the connection pool. Call on process shutdown."""
    global _pool, _pool_pid
    if _pool is not None:
        try:
            # Get and close all available connections
            while True:
                try:
                    conn = _pool.get_connection()
                    conn.close()
                except PoolError:
                    break
        except Exception as e:
            logger.debug(f"Error during pool cleanup: {e}")
        finally:
            _pool = None
            _pool_pid = None
            logger.debug("MySQL pool closed")


@contextmanager
def get_connection(max_retries: int = 3, retry_delay: float = 0.5):
    """
    Get a connection from the pool with retry logic.

    Args:
        max_retries: Number of times to retry on pool exhaustion
        retry_delay: Seconds to wait between retries

    Yields:
        MySQL connection object

    Raises:
        PoolError: If connection cannot be obtained after retries
    """
    conn = None
    last_error = None

    for attempt in range(max_retries):
        try:
            conn = _get_pool().get_connection()
            break
        except PoolError as e:
            last_error = e
            if attempt < max_retries - 1:
                logger.warning(
                    f"Pool exhausted (attempt {attempt + 1}/{max_retries}), "
                    f"retrying in {retry_delay}s..."
                )
                time.sleep(retry_delay)
                retry_delay *= 1.5  # Exponential backoff
            else:
                logger.error(f"Failed to get connection after {max_retries} attempts")
                raise
        except DatabaseError as e:
            # Connection errors (too many connections, etc.)
            last_error = e
            if "Too many connections" in str(e):
                if attempt < max_retries - 1:
                    logger.warning(
                        f"MySQL too many connections (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {retry_delay}s..."
                    )
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Longer backoff for server-side issues
                else:
                    raise
            else:
                raise

    if conn is None:
        raise last_error or PoolError("Failed to obtain connection")

    try:
        yield conn
    finally:
        try:
            conn.close()
        except Exception as e:
            logger.debug(f"Error closing connection: {e}")


def executeMysqlQuery(
    query: str,
    params: Optional[Dict[str, Any]] = None,
    many: bool = False,
    commit: bool = False,
    multi: bool = False,
) -> Optional[Union[Dict[str, Any], List[Dict[str, Any]]]]:
    """
    Execute a MySQL query with automatic connection management.

    Args:
        query: SQL query string
        params: Query parameters (dict for named params)
        many: If True, return all rows; if False, return first row
        commit: If True, commit the transaction
        multi: If True, execute as multi-statement query

    Returns:
        Query result as dict(s) or None
    """
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            if multi:
                for _ in cursor.execute(query, params, multi=True):
                    pass
            elif params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            if commit:
                conn.commit()
                return None

            result = cursor.fetchall() if many else cursor.fetchone()
            if result:
                return [dict(row) for row in result] if many else dict(result)
            return result
        finally:
            cursor.close()

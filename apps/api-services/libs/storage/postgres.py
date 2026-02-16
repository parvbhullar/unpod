"""
PostgreSQL Connection Pool with process-aware management.

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
from typing import Any

from psycopg2 import pool, OperationalError
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

_pool: pool.SimpleConnectionPool | None = None
_pool_pid: int | None = None


def _get_pool() -> pool.SimpleConnectionPool:
    """
    Get or create the connection pool for the current process.

    Each process gets its own pool with a small size (2 connections).
    Pool is recreated if accessed from a different process (fork safety).
    """
    from libs.api.config import get_settings

    settings = get_settings()
    global _pool, _pool_pid

    current_pid = os.getpid()

    if _pool is not None and _pool_pid != current_pid:
        logger.debug(
            f"Process forked (was {_pool_pid}, now {current_pid}), recreating pool"
        )
        _pool = None

    if _pool is None:
        try:
            _pool = pool.SimpleConnectionPool(
                minconn=1,
                maxconn=2,
                **settings.POSTGRES_CONFIG,
            )
            _pool_pid = current_pid
            logger.debug(f"Created PostgreSQL pool for process {current_pid}")
        except OperationalError as e:
            logger.error(f"Failed to create PostgreSQL pool: {e}")
            raise

    return _pool


def close_pool() -> None:
    """Close the connection pool. Call on process shutdown."""
    global _pool, _pool_pid
    if _pool is not None:
        try:
            _pool.closeall()
        except Exception as e:
            logger.debug(f"Error during pool cleanup: {e}")
        finally:
            _pool = None
            _pool_pid = None
            logger.debug("PostgreSQL pool closed")


@contextmanager
def get_connection(max_retries: int = 3, retry_delay: float = 0.5):
    """
    Get a connection from the pool with retry logic.

    Args:
        max_retries: Number of times to retry on pool exhaustion
        retry_delay: Seconds to wait between retries

    Yields:
        PostgreSQL connection object

    Raises:
        pool.PoolError: If connection cannot be obtained after retries
    """
    conn = None
    last_error: Exception | None = None
    current_pool = _get_pool()

    for attempt in range(max_retries):
        try:
            conn = current_pool.getconn()
            break
        except pool.PoolError as e:
            last_error = e
            if attempt < max_retries - 1:
                logger.warning(
                    f"Pool exhausted (attempt {attempt + 1}/{max_retries}), "
                    f"retrying in {retry_delay}s..."
                )
                time.sleep(retry_delay)
                retry_delay *= 1.5
            else:
                logger.error(f"Failed to get connection after {max_retries} attempts")
                raise
        except OperationalError as e:
            last_error = e
            if "too many connections" in str(e).lower():
                if attempt < max_retries - 1:
                    logger.warning(
                        f"PostgreSQL too many connections "
                        f"(attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {retry_delay}s..."
                    )
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise
            else:
                raise

    if conn is None:
        raise last_error or pool.PoolError("Failed to obtain connection")

    try:
        yield conn
    finally:
        try:
            current_pool.putconn(conn)
        except Exception as e:
            logger.debug(f"Error returning connection to pool: {e}")


def executeQuery(
    query: str,
    params: dict[str, Any] | tuple[Any, ...] | None = None,
    many: bool = False,
    commit: bool = False,
) -> dict[str, Any] | list[dict[str, Any]] | None:
    """
    Execute a PostgreSQL query with automatic connection management.

    Args:
        query: SQL query string
        params: Query parameters (dict for named params, tuple for positional)
        many: If True, return all rows; if False, return first row
        commit: If True, commit the transaction

    Returns:
        Query result as dict(s) or None
    """
    with get_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            if commit:
                conn.commit()
                return None

            if many:
                result = cursor.fetchall()
                return [dict(row) for row in result] if result else []
            else:
                result = cursor.fetchone()
                return dict(result) if result else None
        finally:
            cursor.close()

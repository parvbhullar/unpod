from mysql.connector.errors import OperationalError
import mysql.connector


def executeMysqlQuery(query: str, params=None, many=False, commit=False, settings=None):
    """
    Execute a MySQL query and return results.

    Args:
        query: SQL query string to execute
        params: Query parameters for parameterized queries
        many: If True, fetch all rows; if False, fetch one row
        commit: If True, commit the transaction (for INSERT/UPDATE/DELETE)
        settings: Settings object with MYSQL_CONFIG attribute (optional, will load if not provided)

    Returns:
        dict | list[dict] | None: Query results or None for commit operations

    Raises:
        ValueError: If settings cannot be loaded
    """
    if settings is None:
        # Auto-load settings if not provided
        from libs.api.config import get_settings

        settings = get_settings()

    try:
        settings.mysql_conn = mysql.connector.connect(**settings.MYSQL_CONFIG)
        cursor = settings.mysql_conn.cursor(dictionary=True)
    except OperationalError as e:
        if str(e) == "MySQL Connection not available.":
            settings.mysql_conn = mysql.connector.connect(**settings.MYSQL_CONFIG)
        cursor = settings.mysql_conn.cursor(dictionary=True)
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)
    result = None
    if not commit:
        if many:
            result = cursor.fetchall()
        else:
            result = cursor.fetchone()
        if result:
            if not many:
                return dict(result)
            else:
                return [dict(row) for row in result]
    if commit:
        settings.mysql_conn.commit()
    cursor.close()
    settings.mysql_conn.disconnect()
    return result

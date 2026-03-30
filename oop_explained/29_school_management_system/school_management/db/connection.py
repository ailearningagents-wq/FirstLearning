"""
db/connection.py — MySQL connection context manager.

Usage:
    with DatabaseConnection(config) as db:
        db.execute("INSERT INTO students ...", params)
        row  = db.fetchone("SELECT ...", params)
        rows = db.fetchall("SELECT ...", params)

The context manager automatically commits on clean exit and rolls back
on any exception, then closes the connection in both cases.
"""

from __future__ import annotations

import logging
from typing import List, Optional

try:
    import mysql.connector
    from mysql.connector import Error as _MySQLError
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

    class _MySQLError(Exception):  # type: ignore[no-redef]
        pass

from ..exceptions import DatabaseError

logger = logging.getLogger(__name__)

# Re-export so callers can catch it without importing mysql.connector directly
MySQLError = _MySQLError


class DatabaseConnection:
    """
    Thin context-manager wrapper around a mysql-connector-python connection.

    - Opens connection on __enter__
    - Commits on clean exit, rolls back on exception
    - Closes cursor + connection in finally block
    - Exposes execute / fetchone / fetchall helpers with parameterised queries
      (never interpolate values directly into SQL strings)
    """

    def __init__(self, config: dict) -> None:
        self._config = config
        self._conn   = None
        self._cursor = None

    # ── Context manager ──────────────────────────────────────────────
    def __enter__(self) -> "DatabaseConnection":
        if not MYSQL_AVAILABLE:
            raise DatabaseError(
                "mysql-connector-python is not installed. "
                "Run: pip install mysql-connector-python"
            )
        try:
            self._conn   = mysql.connector.connect(**self._config)
            self._cursor = self._conn.cursor(dictionary=True)
        except _MySQLError as exc:
            raise DatabaseError(f"Could not connect to MySQL: {exc}") from exc
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None:
                self._conn.commit()
                logger.debug("Transaction committed.")
            else:
                self._conn.rollback()
                logger.warning("Transaction rolled back due to: %s", exc_val)
        finally:
            if self._cursor:
                self._cursor.close()
            if self._conn and self._conn.is_connected():
                self._conn.close()
        return False  # always re-raise exceptions

    # ── Query helpers ────────────────────────────────────────────────
    def execute(self, sql: str, params: tuple = ()) -> None:
        """Execute a DML statement (INSERT / UPDATE / DELETE)."""
        logger.debug("SQL: %s | params: %s", sql.strip(), params)
        self._cursor.execute(sql, params)

    def fetchone(self, sql: str, params: tuple = ()) -> Optional[dict]:
        """Return the first matching row as a dict, or None."""
        logger.debug("SQL: %s | params: %s", sql.strip(), params)
        self._cursor.execute(sql, params)
        return self._cursor.fetchone()

    def fetchall(self, sql: str, params: tuple = ()) -> List[dict]:
        """Return all matching rows as a list of dicts."""
        logger.debug("SQL: %s | params: %s", sql.strip(), params)
        self._cursor.execute(sql, params)
        return self._cursor.fetchall()

    @property
    def lastrowid(self) -> Optional[int]:
        return self._cursor.lastrowid

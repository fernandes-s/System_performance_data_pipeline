import sqlite3
from contextlib import contextmanager

import pandas as pd

from utils.config import DB_PATH


@contextmanager
def get_connection():
    """
    Create and safely close a SQLite connection.

    Yields:
        sqlite3.Connection: Active database connection.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def database_exists() -> bool:
    """
    Check whether the SQLite database file exists.

    Returns:
        bool: True if the database file exists, otherwise False.
    """
    return DB_PATH.exists()


def run_query(query: str, params: tuple | None = None) -> pd.DataFrame:
    """
    Run a SELECT query and return the results as a DataFrame.

    Args:
        query (str): SQL query to execute.
        params (tuple | None): Optional query parameters.

    Returns:
        pd.DataFrame: Query results.
    """
    params = params or ()

    with get_connection() as conn:
        return pd.read_sql_query(query, conn, params=params)


def execute_statement(query: str, params: tuple | None = None) -> None:
    """
    Execute a non-SELECT SQL statement such as INSERT, UPDATE, or DELETE.

    Args:
        query (str): SQL statement to execute.
        params (tuple | None): Optional query parameters.
    """
    params = params or ()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()


def table_exists(table_name: str) -> bool:
    """
    Check whether a table exists in the SQLite database.

    Args:
        table_name (str): Name of the table.

    Returns:
        bool: True if the table exists, otherwise False.
    """
    query = """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = ?
    """
    result = run_query(query, (table_name,))
    return not result.empty
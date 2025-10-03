"""Query builder utilities for common database operations."""

from typing import List, Dict, Any, Optional, Tuple


class QueryBuilder:
    """Build SQL queries programmatically with a fluent API."""

    def __init__(self, table: str):
        """
        Initialize query builder.

        Args:
            table: Table name to query
        """
        self.table = table
        self._select_cols: List[str] = []
        self._where_clauses: List[str] = []
        self._where_params: List[Any] = []
        self._joins: List[str] = []
        self._order_by: Optional[str] = None
        self._limit: Optional[int] = None
        self._offset: Optional[int] = None

    def select(self, *columns: str) -> 'QueryBuilder':
        """
        Add columns to SELECT clause.

        Args:
            *columns: Column names to select

        Returns:
            Self for method chaining
        """
        self._select_cols.extend(columns)
        return self

    def where(self, condition: str, *params: Any) -> 'QueryBuilder':
        """
        Add WHERE condition.

        Args:
            condition: SQL condition with ? placeholders
            *params: Parameter values for placeholders

        Returns:
            Self for method chaining
        """
        self._where_clauses.append(condition)
        self._where_params.extend(params)
        return self

    def join(self, table: str, on: str) -> 'QueryBuilder':
        """
        Add JOIN clause.

        Args:
            table: Table to join
            on: JOIN condition

        Returns:
            Self for method chaining
        """
        self._joins.append(f"JOIN {table} ON {on}")
        return self

    def left_join(self, table: str, on: str) -> 'QueryBuilder':
        """
        Add LEFT JOIN clause.

        Args:
            table: Table to join
            on: JOIN condition

        Returns:
            Self for method chaining
        """
        self._joins.append(f"LEFT JOIN {table} ON {on}")
        return self

    def order_by(self, column: str, direction: str = 'ASC') -> 'QueryBuilder':
        """
        Add ORDER BY clause.

        Args:
            column: Column to order by
            direction: Sort direction (ASC or DESC)

        Returns:
            Self for method chaining
        """
        self._order_by = f"{column} {direction}"
        return self

    def limit(self, limit: int) -> 'QueryBuilder':
        """
        Add LIMIT clause.

        Args:
            limit: Maximum number of rows

        Returns:
            Self for method chaining
        """
        self._limit = limit
        return self

    def offset(self, offset: int) -> 'QueryBuilder':
        """
        Add OFFSET clause.

        Args:
            offset: Number of rows to skip

        Returns:
            Self for method chaining
        """
        self._offset = offset
        return self

    def build(self) -> Tuple[str, List[Any]]:
        """
        Build final SQL query and parameter list.

        Returns:
            Tuple of (query string, parameters list)
        """
        # SELECT
        if self._select_cols:
            cols = ", ".join(self._select_cols)
        else:
            cols = "*"

        query = f"SELECT {cols} FROM {self.table}"

        # JOINs
        if self._joins:
            query += " " + " ".join(self._joins)

        # WHERE
        if self._where_clauses:
            query += " WHERE " + " AND ".join(self._where_clauses)

        # ORDER BY
        if self._order_by:
            query += f" ORDER BY {self._order_by}"

        # LIMIT
        if self._limit is not None:
            query += f" LIMIT {self._limit}"

        # OFFSET
        if self._offset is not None:
            query += f" OFFSET {self._offset}"

        return query, self._where_params


def build_insert(table: str, data: Dict[str, Any]) -> Tuple[str, List[Any]]:
    """
    Build INSERT query.

    Args:
        table: Table name
        data: Dictionary of column names to values

    Returns:
        Tuple of (query string, parameters list)

    Example:
        >>> query, params = build_insert('users', {'name': 'Alice', 'age': 30})
        >>> print(query)
        INSERT INTO users (name, age) VALUES (?, ?)
        >>> print(params)
        ['Alice', 30]
    """
    columns = ", ".join(data.keys())
    placeholders = ", ".join(["?" for _ in data])
    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    return query, list(data.values())


def build_update(
    table: str,
    data: Dict[str, Any],
    where: str,
    where_params: List[Any]
) -> Tuple[str, List[Any]]:
    """
    Build UPDATE query.

    Args:
        table: Table name
        data: Dictionary of column names to new values
        where: WHERE clause condition
        where_params: Parameters for WHERE clause

    Returns:
        Tuple of (query string, parameters list)

    Example:
        >>> query, params = build_update('users', {'age': 31}, 'id = ?', [123])
        >>> print(query)
        UPDATE users SET age = ? WHERE id = ?
        >>> print(params)
        [31, 123]
    """
    set_clause = ", ".join([f"{col} = ?" for col in data.keys()])
    query = f"UPDATE {table} SET {set_clause} WHERE {where}"
    params = list(data.values()) + where_params
    return query, params


def build_delete(table: str, where: str, where_params: List[Any]) -> Tuple[str, List[Any]]:
    """
    Build DELETE query.

    Args:
        table: Table name
        where: WHERE clause condition
        where_params: Parameters for WHERE clause

    Returns:
        Tuple of (query string, parameters list)

    Example:
        >>> query, params = build_delete('users', 'id = ?', [123])
        >>> print(query)
        DELETE FROM users WHERE id = ?
        >>> print(params)
        [123]
    """
    query = f"DELETE FROM {table} WHERE {where}"
    return query, where_params

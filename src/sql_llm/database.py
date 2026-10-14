"""SQLite access with strictly read-only execution, security parsing, and schema extraction."""

from __future__ import annotations

import sqlite3
import time
from contextlib import closing
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import sqlglot
from sqlglot import exp

WRITE_KEYWORDS = {"DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "CREATE", "REPLACE", "PRAGMA", "ATTACH"}


@dataclass
class QueryResult:
    """Outcome of executing one SQL statement."""

    success: bool
    sql: str
    columns: list[str] = field(default_factory=list)
    rows: list[tuple[Any, ...]] = field(default_factory=list)
    execution_time_ms: float = 0.0
    error: str | None = None

    @property
    def row_count(self) -> int:
        return len(self.rows)


class SQLiteDatabase:
    """Read-only wrapper around a SQLite file (`mode=ro` + PRAGMA query_only=ON + sqlglot single-SELECT check)."""

    def __init__(self, db_path: str | Path, query_timeout_seconds: float = 3.0):
        self.db_path = Path(db_path).resolve()
        self.query_timeout_seconds = query_timeout_seconds
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found at: {self.db_path}")

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(f"file:{self.db_path.as_posix()}?mode=ro", uri=True)
        conn.execute("PRAGMA query_only=ON;")
        return conn

    def list_tables(self) -> list[str]:
        with closing(self._connect()) as conn:
            cur = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
            return [r[0] for r in cur.fetchall()]

    def get_table_schema(self, table_name: str) -> str:
        """Return the CREATE TABLE statement for `table_name`."""
        with closing(self._connect()) as conn:
            row = conn.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name = ?", (table_name,)
            ).fetchone()
        if not row or not row[0]:
            raise ValueError(f"Table '{table_name}' does not exist.")
        return row[0].strip()

    def get_all_schemas(self, tables: list[str] | None = None) -> str:
        """Concatenated CREATE TABLE statements for all (or the selected) tables."""
        available = self.list_tables()
        selected = [t for t in (tables or available) if t in available]
        return "\n\n".join(self.get_table_schema(t) for t in selected)

    def validate_statement(self, sql: str) -> tuple[bool, str | None]:
        """Verify that sql is exactly one safe SELECT or WITH statement using sqlglot."""
        query = sql.strip().rstrip(";")
        if not query:
            return False, "Query cannot be empty."

        first_word = query.split()[0].upper()
        if first_word in WRITE_KEYWORDS:
            return False, f"Permission denied: '{first_word}' statement is blocked (read-only)."

        try:
            parsed = [p for p in sqlglot.parse(query, read="sqlite") if p is not None]
        except sqlglot.errors.SqlglotError as exc:
            return False, f"SQL parse error: {exc}"

        if len(parsed) != 1:
            return False, "Security violation: Only a single SQL statement is allowed."

        stmt = parsed[0]
        if not isinstance(stmt, (exp.Select, exp.Union)):
            return False, f"Security violation: Only SELECT or WITH statements are allowed (got {type(stmt).__name__})."

        if stmt.find(exp.Pragma) or stmt.find(exp.Command):
            return False, "Security violation: PRAGMA statements are blocked."

        return True, None

    def execute_query(self, sql: str, max_rows: int = 50, timeout: float | None = None) -> QueryResult:
        """Run `sql` strictly read-only with sqlglot AST verification, timeout, and row limits."""
        start = time.perf_counter()

        is_valid, err_msg = self.validate_statement(sql)
        if not is_valid:
            return QueryResult(False, sql, error=err_msg, execution_time_ms=_elapsed_ms(start))

        timeout_sec = timeout if timeout is not None else self.query_timeout_seconds
        deadline = time.time() + timeout_sec

        def _progress_handler() -> int:
            if time.time() > deadline:
                return 1  # Abort query execution
            return 0

        query = sql.strip().rstrip(";")
        try:
            with closing(self._connect()) as conn:
                conn.set_progress_handler(_progress_handler, 1000)
                cur = conn.execute(query)
                columns = [d[0] for d in cur.description] if cur.description else []
                rows = cur.fetchmany(max_rows)
        except sqlite3.OperationalError as exc:
            if "interrupted" in str(exc).lower():
                return QueryResult(
                    False,
                    sql,
                    error=f"Query aborted: execution timed out after {timeout_sec}s.",
                    execution_time_ms=_elapsed_ms(start),
                )
            return QueryResult(False, sql, error=f"SQLite error: {exc}", execution_time_ms=_elapsed_ms(start))
        except sqlite3.Error as exc:
            return QueryResult(False, sql, error=f"SQLite error: {exc}", execution_time_ms=_elapsed_ms(start))

        return QueryResult(True, sql, columns, rows, _elapsed_ms(start))


def _elapsed_ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000.0, 2)

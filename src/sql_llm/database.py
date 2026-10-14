"""SQLite access with strictly read-only execution and schema extraction."""

import sqlite3
import time
from contextlib import closing
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

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
    """Read-only wrapper around a SQLite file (`mode=ro` + keyword guard)."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path).resolve()
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found at: {self.db_path}")

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(f"file:{self.db_path.as_posix()}?mode=ro", uri=True)

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

    def execute_query(self, sql: str, max_rows: int = 50) -> QueryResult:
        """Run `sql` read-only; never raises, errors are returned in the result."""
        query = sql.strip().rstrip(";")
        first = query.split()[0].upper() if query else ""
        if first in WRITE_KEYWORDS:
            return QueryResult(False, sql, error=f"Permission denied: '{first}' is blocked (read-only).")

        start = time.perf_counter()
        try:
            with closing(self._connect()) as conn:
                cur = conn.execute(query)
                columns = [d[0] for d in cur.description] if cur.description else []
                rows = cur.fetchmany(max_rows)
        except sqlite3.Error as exc:
            return QueryResult(False, sql, error=f"SQLite error: {exc}",
                               execution_time_ms=_elapsed_ms(start))
        return QueryResult(True, sql, columns, rows, _elapsed_ms(start))


def _elapsed_ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000.0, 2)

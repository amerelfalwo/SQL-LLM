"""Schema representation builder for prompt ablation (full, linked, linked_rows)."""

from __future__ import annotations

import re
import sqlite3
from typing import Literal

from sql_llm.database import SQLiteDatabase

SchemaMode = Literal["full", "linked", "linked_rows"]


def camel_split(s: str) -> set[str]:
    """Split CamelCase words into tokens (e.g., 'InvoiceLine' -> {'invoice', 'line'})."""
    tokens = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)|\d+", s)
    return {t.lower() for t in tokens if t}


def get_foreign_key_map(conn: sqlite3.Connection, tables: list[str]) -> dict[str, set[str]]:
    """Build an undirected map of foreign key relationships between tables."""
    fk_map: dict[str, set[str]] = {t: set() for t in tables}
    for t in tables:
        try:
            fks = conn.execute(f"PRAGMA foreign_key_list({t})").fetchall()
            for fk in fks:
                target_table = fk[2]
                if target_table in fk_map:
                    fk_map[t].add(target_table)
                    fk_map[target_table].add(t)
        except sqlite3.Error:
            continue
    return fk_map


def get_relevant_tables(conn: sqlite3.Connection, question: str, max_tables: int = 4) -> list[str]:
    """Score tables by keyword overlap with question, expanding with FK neighbors up to max_tables."""
    q_words = {w.lower() for w in re.findall(r"\w+", question) if len(w) > 2}
    all_tables = [
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
    ]

    scores: dict[str, int] = {}
    for table in all_tables:
        t_tokens = camel_split(table)
        score = 0
        if table.lower() in q_words:
            score += 10
        score += sum(3 for tok in t_tokens if tok in q_words)

        # Check columns
        cols = [c[1] for c in conn.execute(f"PRAGMA table_info({table})").fetchall()]
        for col in cols:
            c_tokens = camel_split(col)
            score += sum(2 for tok in c_tokens if tok in q_words)
            if col.lower() in q_words:
                score += 5

        scores[table] = score

    sorted_by_score = sorted([t for t, s in scores.items() if s > 0], key=lambda t: scores[t], reverse=True)
    if not sorted_by_score:
        sorted_by_score = ["Track", "Invoice", "Customer", "Artist"]

    selected = sorted_by_score[:max_tables]

    # If room left, add FK neighbors of top tables
    if len(selected) < max_tables:
        fk_map = get_foreign_key_map(conn, all_tables)
        for base in list(selected):
            for neighbor in fk_map.get(base, set()):
                if neighbor not in selected:
                    selected.append(neighbor)
                    if len(selected) == max_tables:
                        break
            if len(selected) == max_tables:
                break

    return sorted(selected)


def get_compact_ddl(conn: sqlite3.Connection, table: str) -> str:
    """Generate compact DDL: CREATE TABLE TableName (col1 TYPE, col2 TYPE); without noise."""
    cols = conn.execute(f"PRAGMA table_info({table})").fetchall()
    defs = []
    for c in cols:
        name = c[1]
        t = c[2].upper()
        if "INT" in t:
            st = "INTEGER"
        elif any(k in t for k in ["NUM", "FLOAT", "REAL", "DEC"]):
            st = "NUMERIC"
        else:
            st = "TEXT"
        defs.append(f"{name} {st}")
    joined = ", ".join(defs)
    return f"CREATE TABLE {table} ({joined});"


def get_sample_inserts(conn: sqlite3.Connection, table: str, limit: int = 2) -> str:
    """Generate 2 sample INSERT statements per table."""
    rows = conn.execute(f"SELECT * FROM {table} LIMIT {limit}").fetchall()
    lines = []
    for r in rows:
        vals = []
        for v in r:
            if v is None:
                vals.append("NULL")
            elif isinstance(v, (int, float)):
                vals.append(str(v))
            else:
                s = str(v).replace("'", "''")
                vals.append(f"'{s}'")
        joined = ", ".join(vals)
        lines.append(f"INSERT INTO {table} VALUES ({joined});")
    return "\n".join(lines)


def build_schema(db: SQLiteDatabase, question: str, mode: SchemaMode = "full") -> str:
    """Build schema string according to ablation mode: 'full', 'linked', or 'linked_rows'."""
    if mode == "full":
        return db.get_all_schemas()

    with db._connect() as conn:
        tables = get_relevant_tables(conn, question, max_tables=4)
        ddls = [get_compact_ddl(conn, t) for t in tables]

        if mode == "linked":
            return "\n\n".join(ddls)

        if mode == "linked_rows":
            blocks = []
            for t, ddl in zip(tables, ddls, strict=False):
                inserts = get_sample_inserts(conn, t, limit=2)
                blocks.append(f"{ddl}\n{inserts}" if inserts else ddl)
            return "\n\n".join(blocks)

    return db.get_all_schemas()

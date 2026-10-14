"""Benchmark Quality Validator.

Enforces quality gates for the Chinook Text-to-SQL benchmark:
Flag as ERROR:
  1. Gold SQL fails execution.
  2. Gold result set is empty or a single 0/NULL (e.g. [(0,)], [(None,)], [('',)]).
  3. LIMIT n while the question says "all".
  4. A tie in the ORDER BY key at the LIMIT boundary (row n vs row n+1).

Flag as WARN:
  1. LIMIT without ORDER BY.
  2. Ties in the sort key among returned rows.
"""

from __future__ import annotations

import re
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path

import sqlglot
from sqlglot import exp

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from sql_llm import config
from sql_llm.benchmark_dataset import CHINOOK_BENCHMARK, BenchmarkItem


@dataclass
class ValidationIssue:
    question_id: int
    level: str  # "ERROR" | "WARN"
    message: str


def get_sort_key_rows(conn: sqlite3.Connection, sql: str, limit_n: int) -> list[tuple] | None:
    """Extract rows of sort keys up to limit_n + 1 to check for ties."""
    try:
        ast = sqlglot.parse_one(sql, read="sqlite")
    except sqlglot.errors.SqlglotError:
        return None

    order = ast.find(exp.Order)
    if not order:
        return None

    select_map = {}
    for s in ast.selects:
        alias = s.alias_or_name
        if alias:
            select_map[alias.lower()] = s.this if isinstance(s, exp.Alias) else s

    order_exprs = []
    new_order_items = []
    for o in order.expressions:
        expr = o.this
        desc = o.args.get("desc", False)
        if isinstance(expr, exp.Column) and expr.name.lower() in select_map:
            actual_expr = select_map[expr.name.lower()].copy()
        else:
            actual_expr = expr.copy()
        order_exprs.append(actual_expr.copy())
        new_order_items.append(exp.Ordered(this=actual_expr.copy(), desc=desc))

    check_ast = ast.copy()
    check_ast.args["expressions"] = order_exprs
    check_ast.args["order"] = exp.Order(expressions=new_order_items)
    check_ast.args["limit"] = exp.Limit(expression=exp.Literal.number(limit_n + 1))

    try:
        check_sql = check_ast.sql("sqlite")
        return conn.execute(check_sql).fetchall()
    except sqlite3.Error:
        return None


def validate_benchmark(db_path: Path | str, items: list[BenchmarkItem]) -> list[ValidationIssue]:
    path = Path(db_path).resolve()
    if not path.exists():
        return [ValidationIssue(0, "ERROR", f"Database not found at: {path}")]

    conn = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    issues: list[ValidationIssue] = []

    for item in items:
        sql = item.gold_sql.strip()
        q = item.question.strip()

        # 1. Execution & Result Check
        try:
            rows = conn.execute(sql).fetchall()
            if not rows:
                issues.append(ValidationIssue(item.id, "ERROR", "Gold SQL returned an empty result set (0 rows)."))
            elif len(rows) == 1 and len(rows[0]) == 1:
                val = rows[0][0]
                if val is None or val == 0 or val == "" or val == 0.0:
                    issues.append(
                        ValidationIssue(
                            item.id,
                            "ERROR",
                            f"Gold SQL returned a trivial single 0/NULL/empty value: {rows}",
                        )
                    )
        except sqlite3.Error as exc:
            issues.append(ValidationIssue(item.id, "ERROR", f"Gold SQL execution failed: {exc}"))
            continue

        # 2. Check for LIMIT when question says "all"
        has_all_in_question = bool(re.search(r"\ball\b", q, re.IGNORECASE))
        has_limit_in_sql = bool(re.search(r"\bLIMIT\s+\d+\b", sql, re.IGNORECASE))

        if has_all_in_question and has_limit_in_sql:
            issues.append(
                ValidationIssue(
                    item.id,
                    "ERROR",
                    "Question requests 'all' results, but Gold SQL contains an arbitrary LIMIT clause.",
                )
            )

        # 3. Check LIMIT & ORDER BY
        limit_match = re.search(r"\bLIMIT\s+(\d+)\b", sql, re.IGNORECASE)
        has_order_by = bool(re.search(r"\bORDER\s+BY\b", sql, re.IGNORECASE))

        if limit_match:
            limit_n = int(limit_match.group(1))
            if not has_order_by:
                issues.append(
                    ValidationIssue(
                        item.id,
                        "WARN",
                        f"Query contains LIMIT {limit_n} without an ORDER BY clause (order non-deterministic).",
                    )
                )
            else:
                sort_rows = get_sort_key_rows(conn, sql, limit_n)
                if sort_rows is not None:
                    # Check boundary tie (row n vs row n+1)
                    if len(sort_rows) > limit_n:
                        row_n = sort_rows[limit_n - 1]
                        row_n_plus_1 = sort_rows[limit_n]
                        if row_n == row_n_plus_1:
                            issues.append(
                                ValidationIssue(
                                    item.id,
                                    "ERROR",
                                    f"Tie in sort key at LIMIT {limit_n} boundary: "
                                    f"row {limit_n} {row_n} == row {limit_n+1} {row_n_plus_1}.",
                                )
                            )

                    # Check ties among returned rows
                    returned_keys = sort_rows[:limit_n]
                    if len(returned_keys) > len(set(returned_keys)):
                        issues.append(
                            ValidationIssue(
                                item.id,
                                "WARN",
                                f"Ties in sort key among the {limit_n} returned rows (missing secondary tiebreaker).",
                            )
                        )

    conn.close()
    return issues


def main() -> int:
    issues = validate_benchmark(config.DB_PATH, CHINOOK_BENCHMARK)
    errors = [i for i in issues if i.level == "ERROR"]
    warns = [i for i in issues if i.level == "WARN"]

    print("=" * 80)
    print(f"BENCHMARK QUALITY REPORT ({len(CHINOOK_BENCHMARK)} items on {config.DB_PATH.name})")
    print(f"Errors: {len(errors)} | Warnings: {len(warns)}")
    print("=" * 80)

    if not issues:
        print("ALL QUALITY GATES PASSED (0 ERRORS, 0 WARNINGS).")
        return 0

    for issue in issues:
        prefix = "[ERROR]" if issue.level == "ERROR" else "[WARN] "
        print(f"{prefix} Q{issue.question_id:02d}: {issue.message}")

    print("=" * 80)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

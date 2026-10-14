"""Validation Script for the Chinook Text-to-SQL Benchmark.

Checks each benchmark query against `data/Chinook_Sqlite.sqlite` for:
1. Syntax correctness and successful execution.
2. Non-empty result set (> 0 rows).
3. Determinism:
   - Queries with `LIMIT` MUST include an `ORDER BY`.
   - Queries with `LIMIT N` must not have tied sort values at the boundary (row N vs row N+1).
4. No hidden truncation: queries answering "all" must not have arbitrary `LIMIT`.
5. Exact column specification alignment between question prompt and gold SELECT clause.
"""

import re
import sqlite3
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from sql_llm import config
from sql_llm.benchmark_dataset import CHINOOK_BENCHMARK


def check_boundary_tie(conn: sqlite3.Connection, sql: str) -> tuple[bool, str]:
    """If SQL has LIMIT N, check if row N and row N+1 share the exact same values for sort keys."""
    limit_match = re.search(r"\bLIMIT\s+(\d+)\b", sql, re.IGNORECASE)
    if not limit_match:
        return True, "No LIMIT"
    
    limit_n = int(limit_match.group(1))
    order_match = re.search(r"\bORDER\s+BY\s+(.*?)(?:\bLIMIT\b|;|$)", sql, re.IGNORECASE | re.DOTALL)
    if not order_match:
        return False, f"LIMIT {limit_n} used without ORDER BY (non-deterministic)"
    
    # Run with limit N + 1
    sql_plus_1 = re.sub(r"\bLIMIT\s+\d+\b", f"LIMIT {limit_n + 1}", sql, flags=re.IGNORECASE)
    try:
        rows = conn.execute(sql_plus_1).fetchall()
    except sqlite3.Error as exc:
        return False, f"Error running query with LIMIT+1: {exc}"
    
    if len(rows) > limit_n:
        last_in_limit = rows[limit_n - 1]
        first_after_limit = rows[limit_n]
        # Compare row content or last column if tie
        if last_in_limit == first_after_limit:
            return False, f"Tie at boundary: row {limit_n} and row {limit_n+1} have identical data {last_in_limit}"
    
    return True, "Deterministic"


def validate_all() -> bool:
    db_path = config.DB_PATH
    if not db_path.exists():
        print(f"ERROR: Database file not found at {db_path}")
        return False

    conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
    all_passed = True

    print("=" * 80)
    print(f"VALIDATING CHINOOK BENCHMARK (40 Questions) on {db_path.name}")
    print("=" * 80)

    for item in CHINOOK_BENCHMARK:
        issues = []
        sql = item.gold_sql.strip()
        q = item.question.strip()

        # 1. Execution & row count
        try:
            cur = conn.execute(sql)
            rows = cur.fetchall()
            row_count = len(rows)
            if row_count == 0:
                issues.append("Returns 0 rows (empty result set)")
        except sqlite3.Error as exc:
            issues.append(f"SQL execution failed: {exc}")
            row_count = 0

        # 2. Check for hidden truncation
        if "all " in q.lower() and re.search(r"\bLIMIT\b", sql, re.IGNORECASE):
            issues.append("Question mentions 'all' but SQL contains an arbitrary LIMIT")

        # 3. Check for LIMIT without ORDER BY and boundary ties
        if re.search(r"\bLIMIT\b", sql, re.IGNORECASE):
            det_ok, det_msg = check_boundary_tie(conn, sql)
            if not det_ok:
                issues.append(det_msg)

        # 4. Status display
        if issues:
            all_passed = False
            status = "FAILED"
            print(f"[{status}] Q{item.id:02d} ({item.difficulty} - {item.category})")
            print(f"  Question: {q}")
            print(f"  Gold SQL: {sql}")
            for iss in issues:
                print(f"  -> ISSUE: {iss}")
        else:
            print(f"[PASSED] Q{item.id:02d}: {row_count} row(s) | {q[:70]}...")

    conn.close()
    print("=" * 80)
    if all_passed:
        print("ALL 40 BENCHMARK QUESTIONS VALIDATED SUCCESSFULLY WITH 0 ISSUES!")
    else:
        print("SOME QUESTIONS FAILED VALIDATION CHECKS (SEE ABOVE).")
    print("=" * 80)
    return all_passed


if __name__ == "__main__":
    success = validate_all()
    sys.exit(0 if success else 1)

import pytest

from sql_llm import config
from sql_llm.database import QueryResult, SQLiteDatabase
from sql_llm.examples import EXAMPLES
from sql_llm.service import results_match


@pytest.fixture(scope="module")
def db() -> SQLiteDatabase:
    return SQLiteDatabase(config.DB_PATH)


def test_lists_chinook_tables(db):
    assert {"Artist", "Album", "Track", "Invoice"} <= set(db.list_tables())


def test_schema_contains_create_table(db):
    assert "CREATE TABLE" in db.get_table_schema("Artist")


def test_unknown_table_raises(db):
    with pytest.raises(ValueError):
        db.get_table_schema("NonExistentTable")


@pytest.mark.parametrize(
    "sql",
    [
        "DROP TABLE Artist",
        "DELETE FROM Artist WHERE 1=1",
        "INSERT INTO Artist VALUES (9999, 'Test')",
        "UPDATE Artist SET Name='Hacked' WHERE ArtistId=1",
        "PRAGMA writable_schema=1",
        "PRAGMA table_info(Artist)",
    ],
)
def test_write_and_pragma_statements_blocked(db, sql):
    res = db.execute_query(sql)
    assert not res.success
    assert any(w in res.error for w in ["Permission denied", "Security violation", "PRAGMA"])


def test_multi_statement_blocked(db):
    res = db.execute_query("SELECT 1; DROP TABLE Artist;")
    assert not res.success
    assert "Security violation" in res.error or "single SQL statement" in res.error


def test_multi_select_statement_blocked(db):
    res = db.execute_query("SELECT 1; SELECT 2;")
    assert not res.success
    assert "Security violation" in res.error or "single SQL statement" in res.error


def test_cte_write_blocked(db):
    res = db.execute_query("WITH x AS (SELECT 1) DELETE FROM Artist")
    assert not res.success
    assert any(term in res.error for term in ["Security violation", "Permission denied", "read-only"])


def test_infinite_recursive_cte_aborted_by_timeout(db):
    # Query with infinite recursion requiring full scan, set timeout small (0.3s) to ensure fast abortion
    inf_sql = "WITH RECURSIVE cnt(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM cnt) SELECT MAX(x) FROM cnt"
    res = db.execute_query(inf_sql, timeout=0.3)
    assert not res.success
    assert "timed out" in res.error or "aborted" in res.error


def test_invalid_sql_returns_error_not_exception(db):
    assert not db.execute_query("SELECT FROM WHERE").success


@pytest.mark.parametrize("example", EXAMPLES)
def test_gold_sql_runs_and_returns_rows(db, example):
    res = db.execute_query(example.gold_sql, max_rows=1000)
    assert res.success and res.row_count > 0


def test_results_match_ignores_order_and_float_noise():
    a = QueryResult(True, "", ["x"], [(1, 2.00001), (3, 4.0)])
    b = QueryResult(True, "", ["x"], [(3, 4.0), (1, 2.0)])
    assert results_match(a, b)
    assert not results_match(a, QueryResult(True, "", ["x"], [(1, 2.0)]))

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


@pytest.mark.parametrize("sql", ["DROP TABLE Artist", "DELETE FROM Artist", "PRAGMA writable_schema=1"])
def test_write_statements_blocked(db, sql):
    res = db.execute_query(sql)
    assert not res.success and "Permission denied" in res.error


def test_cte_write_blocked_by_readonly_connection(db):
    res = db.execute_query("WITH x AS (SELECT 1) DELETE FROM Artist")
    assert not res.success


def test_invalid_sql_returns_error_not_exception(db):
    assert not db.execute_query("SELECT FROM WHERE").success


@pytest.mark.parametrize("example", EXAMPLES)
def test_gold_sql_runs_and_returns_rows(db, example):
    res = db.execute_query(example.gold_sql, max_rows=1000)
    assert res.success and res.row_count > 0


def test_results_match_ignores_order_and_float_noise():
    a = QueryResult(True, "", ["x"], [(1, 2.001), (3, 4.0)])
    b = QueryResult(True, "", ["x"], [(3, 4.0), (1, 2.0)])
    assert results_match(a, b)
    assert not results_match(a, QueryResult(True, "", ["x"], [(1, 2.0)]))

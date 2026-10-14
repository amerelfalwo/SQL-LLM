"""Unit tests for the Chinook 40-question benchmark dataset."""

import pytest

from sql_llm import config
from sql_llm.benchmark_dataset import CHINOOK_BENCHMARK
from sql_llm.database import SQLiteDatabase


@pytest.fixture(scope="module")
def db() -> SQLiteDatabase:
    return SQLiteDatabase(config.DB_PATH)


def test_benchmark_count():
    assert 30 <= len(CHINOOK_BENCHMARK) <= 50
    assert len(CHINOOK_BENCHMARK) == 40


def test_benchmark_item_structure():
    ids = set()
    for item in CHINOOK_BENCHMARK:
        assert item.id not in ids, f"Duplicate ID: {item.id}"
        ids.add(item.id)
        assert item.category in {
            "Filter & Sort",
            "Aggregation",
            "2-Table Join",
            "Multi-Table Join",
            "Date / Time",
            "Subquery",
            "Self-Join",
            "Grouping & Having",
        }
        assert item.difficulty in {"Easy", "Medium", "Hard"}
        assert len(item.question.strip()) > 10
        assert item.gold_sql.strip().upper().startswith("SELECT") or item.gold_sql.strip().upper().startswith("WITH")


@pytest.mark.parametrize("item", CHINOOK_BENCHMARK, ids=lambda x: f"Q{x.id}_{x.category}")
def test_gold_sql_execution(db: SQLiteDatabase, item):
    result = db.execute_query(item.gold_sql, max_rows=1000)
    assert result.success, f"Gold SQL for Q{item.id} failed: {result.error}"
    assert result.row_count > 0, f"Gold SQL for Q{item.id} returned 0 rows: {item.gold_sql}"

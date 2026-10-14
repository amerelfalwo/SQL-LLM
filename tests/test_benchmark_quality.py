"""Pytest quality gate for the Chinook benchmark."""

import sys
from pathlib import Path

# Ensure scripts can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from validate_benchmark import validate_benchmark

from sql_llm import config
from sql_llm.benchmark_dataset import CHINOOK_BENCHMARK


def test_benchmark_has_no_validation_errors():
    issues = validate_benchmark(config.DB_PATH, CHINOOK_BENCHMARK)
    errors = [f"Q{i.question_id:02d}: {i.message}" for i in issues if i.level == "ERROR"]
    assert not errors, f"Benchmark quality validation failed with {len(errors)} error(s):\n" + "\n".join(errors)

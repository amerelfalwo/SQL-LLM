"""Orchestrates schema extraction, model inference, safe execution and strict/lenient evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import permutations
from typing import Any

from sql_llm.client import ColabSQLClient
from sql_llm.database import QueryResult, SQLiteDatabase


@dataclass
class TextToSQLReport:
    """Full lifecycle of one natural-language question."""

    question: str
    generated_sql: str
    generation_error: str | None
    inference_time_ms: float
    execution_result: QueryResult | None
    success: bool
    summary: str


def _normalize_cell(v: Any) -> Any:
    if isinstance(v, float):
        return round(v, 4)
    if isinstance(v, (int, str)):
        return v
    if v is None:
        return None
    return str(v).strip()


def _normalize_row(row: tuple[Any, ...]) -> tuple[Any, ...]:
    return tuple(_normalize_cell(x) for x in row)


def compare_results(
    gold: QueryResult,
    predicted: QueryResult,
    ordered: bool = False,
) -> tuple[bool, bool]:
    """Compare query result sets.

    Returns:
        (strict_match, lenient_match):
        - strict: exact column count, same column positions, matching row-for-row
          (ordered if requested, multiset otherwise).
        - lenient: accepts extra columns and any column permutation as long as all
          gold column values are present.
    """
    if not gold.success or not predicted.success or predicted.rows is None:
        return False, False

    gold_rows = [_normalize_row(r) for r in gold.rows]
    pred_rows = [_normalize_row(r) for r in predicted.rows]

    if len(gold_rows) != len(pred_rows):
        return False, False

    if not gold_rows and not pred_rows:
        return True, True

    gold_k = len(gold_rows[0])
    pred_m = len(pred_rows[0])

    # 1. Strict Match: same column count, same positions
    strict_match = False
    if gold_k == pred_m:
        if ordered:
            strict_match = (gold_rows == pred_rows)
        else:
            strict_match = (sorted(gold_rows, key=repr) == sorted(pred_rows, key=repr))

    # 2. Lenient Match: any subset/permutation of columns containing all gold columns
    lenient_match = strict_match
    if not lenient_match and pred_m >= gold_k:
        sorted_gold = sorted(gold_rows, key=repr) if not ordered else None
        for perm in permutations(range(pred_m), gold_k):
            proj = [tuple(r[idx] for idx in perm) for r in pred_rows]
            if ordered:
                if proj == gold_rows:
                    lenient_match = True
                    break
            else:
                if sorted(proj, key=repr) == sorted_gold:
                    lenient_match = True
                    break

    return strict_match, lenient_match


def results_match(
    gold: QueryResult,
    predicted: QueryResult,
    ordered: bool = False,
    lenient: bool = False,
) -> bool:
    """Convenience wrapper for test assertions."""
    strict, leni = compare_results(gold, predicted, ordered=ordered)
    return leni if lenient else strict


class TextToSQLService:
    """Question -> SQL -> result, against one read-only database."""

    def __init__(self, db: SQLiteDatabase, client: ColabSQLClient):
        self.db = db
        self.client = client

    def answer_question(
        self,
        question: str,
        target_tables: list[str] | None = None,
        max_result_rows: int = 25,
        use_adapter: bool = True,
        custom_schema_sql: str | None = None,
    ) -> TextToSQLReport:
        """Generate SQL for `question` and execute it, returning a full report."""
        schema = custom_schema_sql if custom_schema_sql is not None else self.db.get_all_schemas(tables=target_tables)
        gen = self.client.generate_sql(
            schema_sql=schema,
            question=question,
            use_adapter=use_adapter,
        )
        if gen.error or not gen.sql:
            error = gen.error or "Model returned an empty query."
            return TextToSQLReport(
                question, "", error, gen.inference_time_ms, None, False, f"Generation failed: {error}"
            )

        result = self.db.execute_query(gen.sql, max_rows=max_result_rows)
        summary = (
            f"Executed: {result.row_count} row(s) in {result.execution_time_ms}ms."
            if result.success
            else f"Generated SQL failed: {result.error}"
        )
        return TextToSQLReport(
            question, gen.sql, None, gen.inference_time_ms, result, result.success, summary
        )

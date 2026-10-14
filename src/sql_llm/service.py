"""Orchestrates schema extraction, model inference and safe execution."""

from dataclasses import dataclass
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


def _normalize(rows: list[tuple[Any, ...]]) -> list[tuple[Any, ...]]:
    """Order-insensitive, float-tolerant representation of a result set."""
    norm = [tuple(round(v, 2) if isinstance(v, float) else v for v in r) for r in rows]
    return sorted(norm, key=repr)


def results_match(gold: QueryResult, predicted: QueryResult) -> bool:
    """Execution accuracy check: same rows (any order) as the gold query."""
    return (
        gold.success
        and predicted.success
        and _normalize(gold.rows) == _normalize(predicted.rows)
    )


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
    ) -> TextToSQLReport:
        """Generate SQL for `question` and execute it, returning a full report."""
        gen = self.client.generate_sql(
            schema_sql=self.db.get_all_schemas(tables=target_tables), question=question
        )
        if gen.error or not gen.sql:
            error = gen.error or "Model returned an empty query."
            return TextToSQLReport(question, "", error, gen.inference_time_ms, None, False,
                                   f"Generation failed: {error}")

        result = self.db.execute_query(gen.sql, max_rows=max_result_rows)
        summary = (
            f"Executed: {result.row_count} row(s) in {result.execution_time_ms}ms."
            if result.success
            else f"Generated SQL failed: {result.error}"
        )
        return TextToSQLReport(question, gen.sql, None, gen.inference_time_ms, result,
                               result.success, summary)

"""Evaluation Harness on the Chinook Database (40 Benchmark Questions).

Evaluates Execution Accuracy and Valid SQL percentage by executing both
the predicted SQL and the Gold SQL against SQLite and comparing their
result sets (order-insensitive, float-tolerant).
"""

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from sql_llm import config
from sql_llm.benchmark_dataset import CHINOOK_BENCHMARK
from sql_llm.client import ColabSQLClient
from sql_llm.database import SQLiteDatabase
from sql_llm.service import TextToSQLService, results_match

console = Console()


@dataclass
class EvalRecord:
    id: int
    category: str
    difficulty: str
    question: str
    gold_sql: str
    predicted_sql: str
    valid_sql: bool
    execution_match: bool
    inference_time_ms: float
    error: str | None = None


@dataclass
class EvalSummary:
    total_questions: int
    execution_accuracy: float
    valid_sql_rate: float
    avg_inference_ms: float
    difficulty_breakdown: dict[str, dict[str, float]]
    category_breakdown: dict[str, dict[str, float]]


def run_evaluation(
    service: TextToSQLService,
    output_path: Path | None = None,
    limit: int | None = None,
) -> EvalSummary:
    """Run full evaluation on Chinook benchmark."""
    items = CHINOOK_BENCHMARK[:limit] if limit else CHINOOK_BENCHMARK
    total = len(items)
    records: list[EvalRecord] = []

    console.print(Panel.fit(
        f"[bold cyan]Chinook Text-to-SQL Benchmark Evaluation[/bold cyan]\n"
        f"[dim]Total Questions: {total} | Database: {config.DB_PATH.name}[/dim]",
        border_style="cyan"
    ))

    passed_exec = 0
    valid_sql_count = 0
    total_time = 0.0

    for idx, item in enumerate(items, 1):
        console.print(f"[bold cyan]Query [{idx}/{total}][/bold cyan] ({item.difficulty} - {item.category}): {item.question}")
        
        # 1. Run Gold SQL
        gold_result = service.db.execute_query(item.gold_sql, max_rows=1000)

        # 2. Get Model Prediction
        report = service.answer_question(item.question, max_result_rows=1000)
        total_time += report.inference_time_ms

        pred_sql = report.generated_sql
        is_valid = bool(report.execution_result and report.execution_result.success)
        is_match = False

        if is_valid and report.execution_result:
            valid_sql_count += 1
            is_match = results_match(gold_result, report.execution_result)
            if is_match:
                passed_exec += 1

        status_text = "[bold green]MATCH[/bold green]" if is_match else (
            "[yellow]VALID (DIFF RESULTS)[/yellow]" if is_valid else "[bold red]INVALID SQL[/bold red]"
        )
        console.print(f"  Result: {status_text} | Pred SQL: [dim]{pred_sql[:90]}...[/dim]")

        records.append(
            EvalRecord(
                id=item.id,
                category=item.category,
                difficulty=item.difficulty,
                question=item.question,
                gold_sql=item.gold_sql,
                predicted_sql=pred_sql,
                valid_sql=is_valid,
                execution_match=is_match,
                inference_time_ms=report.inference_time_ms,
                error=report.generation_error or (report.execution_result.error if report.execution_result else None),
            )
        )

    # Calculate metrics
    exec_acc = round((passed_exec / total) * 100.0, 2)
    valid_rate = round((valid_sql_count / total) * 100.0, 2)
    avg_time = round(total_time / total, 2) if total > 0 else 0.0

    # Breakdowns
    diff_stats: dict[str, dict[str, float]] = {}
    for diff in ["Easy", "Medium", "Hard"]:
        group = [r for r in records if r.difficulty == diff]
        if group:
            diff_match = sum(1 for r in group if r.execution_match)
            diff_stats[diff] = {
                "total": len(group),
                "accuracy": round((diff_match / len(group)) * 100.0, 1),
            }

    cat_stats: dict[str, dict[str, float]] = {}
    for cat in sorted({r.category for r in records}):
        group = [r for r in records if r.category == cat]
        cat_match = sum(1 for r in group if r.execution_match)
        cat_stats[cat] = {
            "total": len(group),
            "accuracy": round((cat_match / len(group)) * 100.0, 1),
        }

    summary = EvalSummary(
        total_questions=total,
        execution_accuracy=exec_acc,
        valid_sql_rate=valid_rate,
        avg_inference_ms=avg_time,
        difficulty_breakdown=diff_stats,
        category_breakdown=cat_stats,
    )

    # Display Rich Summary Table
    table = Table(title="Chinook Evaluation Results Summary", header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Result", justify="right", style="green")

    table.add_row("Total Evaluated Questions", str(total))
    table.add_row("Execution Accuracy", f"{exec_acc}%")
    table.add_row("Valid SQL Rate", f"{valid_rate}%")
    table.add_row("Average Inference Time", f"{avg_time} ms")
    console.print("\n", table)

    # Save to JSON
    if output_path:
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "summary": asdict(summary),
            "records": [asdict(r) for r in records],
        }
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        console.print(f"[bold green]Full report saved to:[/bold green] {out_file}")

    return summary


def main() -> None:
    db = SQLiteDatabase(config.DB_PATH)
    client = ColabSQLClient()
    service = TextToSQLService(db, client)
    run_evaluation(service, output_path=Path("data/chinook_evaluation_results.json"))


if __name__ == "__main__":
    main()

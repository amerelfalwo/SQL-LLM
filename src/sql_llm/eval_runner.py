"""Evaluation Harness on the Chinook Database (40 Benchmark Questions).

Evaluates Execution Accuracy (Strict & Lenient) and Valid SQL percentage by
executing predicted SQL against SQLite and comparing to Gold SQL ground truth.
Supports:
- --no-adapter: evaluate base model without LoRA
- --schema-mode full|linked|linked_rows: prompt schema ablation
- 95% Wilson confidence intervals
- Failure type taxonomy classification
"""

from __future__ import annotations

import argparse
import json
import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from sql_llm import config
from sql_llm.benchmark_dataset import CHINOOK_BENCHMARK
from sql_llm.client import ColabSQLClient
from sql_llm.database import SQLiteDatabase
from sql_llm.schema_builder import SchemaMode, build_schema
from sql_llm.service import TextToSQLService, compare_results

console = Console()


@dataclass
class EvalRecord:
    id: int
    category: str
    difficulty: str
    question: str
    gold_sql: str
    predicted_sql: str
    valid: bool
    strict_match: bool
    lenient_match: bool
    error: str | None
    latency_ms: float
    failure_type: str | None


@dataclass
class EvalSummary:
    total_questions: int
    use_adapter: bool
    schema_mode: str
    strict_accuracy: float
    lenient_accuracy: float
    valid_sql_rate: float
    ci_95_strict: list[float]
    ci_95_lenient: list[float]
    avg_latency_ms: float
    difficulty_breakdown: dict[str, dict[str, float]]
    category_breakdown: dict[str, dict[str, float]]


def wilson_interval(successes: int, total: int, z: float = 1.96) -> list[float]:
    """Calculate 95% Wilson score confidence interval for a binomial proportion."""
    if total == 0:
        return [0.0, 0.0]
    p = successes / total
    denom = 1.0 + (z**2) / total
    center = (p + (z**2) / (2 * total)) / denom
    margin = z * math.sqrt((p * (1 - p)) / total + (z**2) / (4 * (total**2))) / denom
    low = max(0.0, center - margin)
    high = min(1.0, center + margin)
    return [round(low * 100.0, 2), round(high * 100.0, 2)]


def question_asks_for_order(question: str) -> bool:
    """Check if the question explicitly asks for a sorted result."""
    patterns = [
        r"\border(ed)?\s+by\b",
        r"\bsort(ed)?\s+by\b",
        r"\balphabetically\b",
        r"\bhighest\b",
        r"\blongest\b",
    ]
    return any(re.search(p, question, re.IGNORECASE) for p in patterns)


def classify_failure(
    valid: bool,
    error_msg: str | None,
    strict_match: bool,
    lenient_match: bool,
    gold_row_count: int,
    pred_row_count: int,
) -> str | None:
    """Classify failure into standard taxonomy."""
    if strict_match:
        return None

    if not valid:
        err = (error_msg or "").lower()
        if any(k in err for k in ["no such table", "no such column"]):
            return "wrong_table_or_column"
        if any(k in err for k in ["syntax error", "no such function", "unrecognized token", "operationalerror"]):
            return "syntax_or_dialect"
        return "syntax_or_dialect"

    # Valid SQL, but strict_match is False
    if lenient_match:
        return "extra_or_missing_columns"

    # Both false
    if gold_row_count != pred_row_count:
        if pred_row_count == 0:
            return "wrong_logic"
        if abs(gold_row_count - pred_row_count) in [5, 10]:
            return "ordering_or_limit"
        return "wrong_logic"

    return "wrong_logic"


def run_evaluation(
    service: TextToSQLService,
    output_path: Path | None = None,
    limit: int | None = None,
    use_adapter: bool = True,
    schema_mode: SchemaMode = "full",
) -> EvalSummary:
    """Run evaluation on Chinook benchmark."""
    items = CHINOOK_BENCHMARK[:limit] if limit else CHINOOK_BENCHMARK
    total = len(items)
    records: list[EvalRecord] = []

    model_label = "Fine-Tuned Adapter (LoRA)" if use_adapter else "Base Model (No Adapter)"
    console.print(
        Panel.fit(
            f"[bold cyan]Chinook Text-to-SQL Benchmark Evaluation[/bold cyan]\n"
            f"[dim]Model: {model_label} | Schema Mode: {schema_mode} | Questions: {total}[/dim]",
            border_style="cyan",
        )
    )

    passed_strict = 0
    passed_lenient = 0
    valid_sql_count = 0
    total_time = 0.0

    for idx, item in enumerate(items, 1):
        ordered_required = question_asks_for_order(item.question)

        # 1. Run Gold SQL
        gold_result = service.db.execute_query(item.gold_sql, max_rows=1000)

        # 2. Get Custom Schema according to ablation mode
        schema_sql = build_schema(service.db, item.question, mode=schema_mode)

        # 3. Model Inference
        report = service.answer_question(
            item.question,
            max_result_rows=1000,
            use_adapter=use_adapter,
            custom_schema_sql=schema_sql,
        )
        total_time += report.inference_time_ms

        pred_sql = report.generated_sql
        is_valid = bool(report.execution_result and report.execution_result.success)
        strict_m = False
        lenient_m = False

        if is_valid and report.execution_result:
            valid_sql_count += 1
            strict_m, lenient_m = compare_results(gold_result, report.execution_result, ordered=ordered_required)
            if strict_m:
                passed_strict += 1
            if lenient_m:
                passed_lenient += 1

        pred_row_count = report.execution_result.row_count if report.execution_result else 0
        failure = classify_failure(
            is_valid,
            report.generation_error or (report.execution_result.error if report.execution_result else None),
            strict_m,
            lenient_m,
            gold_result.row_count,
            pred_row_count,
        )

        status_text = (
            "[bold green]STRICT MATCH[/bold green]"
            if strict_m
            else ("[cyan]LENIENT MATCH[/cyan]" if lenient_m else ("[yellow]VALID (MISMATCH)[/yellow]" if is_valid else "[bold red]INVALID SQL[/bold red]"))
        )
        console.print(
            f"[{idx:02d}/{total}] ({item.difficulty} - {item.category}) Result: {status_text} | Pred: [dim]{pred_sql[:75]}...[/dim]"
        )

        records.append(
            EvalRecord(
                id=item.id,
                category=item.category,
                difficulty=item.difficulty,
                question=item.question,
                gold_sql=item.gold_sql,
                predicted_sql=pred_sql,
                valid=is_valid,
                strict_match=strict_m,
                lenient_match=lenient_m,
                error=report.generation_error or (report.execution_result.error if report.execution_result else None),
                latency_ms=report.inference_time_ms,
                failure_type=failure,
            )
        )

    # Metrics
    strict_acc = round((passed_strict / total) * 100.0, 2)
    lenient_acc = round((passed_lenient / total) * 100.0, 2)
    valid_rate = round((valid_sql_count / total) * 100.0, 2)
    avg_latency = round(total_time / total, 2) if total > 0 else 0.0

    ci_strict = wilson_interval(passed_strict, total)
    ci_lenient = wilson_interval(passed_lenient, total)

    # Breakdowns
    diff_stats: dict[str, dict[str, float]] = {}
    for diff in ["Easy", "Medium", "Hard"]:
        group = [r for r in records if r.difficulty == diff]
        if group:
            diff_strict = sum(1 for r in group if r.strict_match)
            diff_lenient = sum(1 for r in group if r.lenient_match)
            diff_stats[diff] = {
                "total": len(group),
                "strict_accuracy": round((diff_strict / len(group)) * 100.0, 1),
                "lenient_accuracy": round((diff_lenient / len(group)) * 100.0, 1),
            }

    cat_stats: dict[str, dict[str, float]] = {}
    for cat in sorted({r.category for r in records}):
        group = [r for r in records if r.category == cat]
        cat_strict = sum(1 for r in group if r.strict_match)
        cat_lenient = sum(1 for r in group if r.lenient_match)
        cat_stats[cat] = {
            "total": len(group),
            "strict_accuracy": round((cat_strict / len(group)) * 100.0, 1),
            "lenient_accuracy": round((cat_lenient / len(group)) * 100.0, 1),
        }

    summary = EvalSummary(
        total_questions=total,
        use_adapter=use_adapter,
        schema_mode=schema_mode,
        strict_accuracy=strict_acc,
        lenient_accuracy=lenient_acc,
        valid_sql_rate=valid_rate,
        ci_95_strict=ci_strict,
        ci_95_lenient=ci_lenient,
        avg_latency_ms=avg_latency,
        difficulty_breakdown=diff_stats,
        category_breakdown=cat_stats,
    )

    # Display Rich Table
    table = Table(
        title=f"Chinook Evaluation ({model_label} - Schema: {schema_mode})",
        header_style="bold magenta",
    )
    table.add_column("Metric", style="cyan")
    table.add_column("Result", justify="right", style="green")

    table.add_row("Total Questions", str(total))
    table.add_row("Strict Execution Accuracy", f"{strict_acc}% (95% CI: [{ci_strict[0]}%, {ci_strict[1]}%])")
    table.add_row("Lenient Execution Accuracy", f"{lenient_acc}% (95% CI: [{ci_lenient[0]}%, {ci_lenient[1]}%])")
    table.add_row("Valid SQL Rate", f"{valid_rate}%")
    table.add_row("Average Latency (via ngrok)", f"{avg_latency} ms")
    console.print("\n", table)

    if output_path:
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "summary": asdict(summary),
            "records": [asdict(r) for r in records],
        }
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        console.print(f"[bold green]Report saved to:[/bold green] {out_file}")

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate model on Chinook benchmark")
    parser.add_argument("--no-adapter", action="store_true", help="Disable LoRA adapter (evaluate base model)")
    parser.add_argument(
        "--schema-mode",
        choices=["full", "linked", "linked_rows"],
        default="full",
        help="Prompt schema ablation mode",
    )
    parser.add_argument("--limit", type=int, default=None, help="Limit number of questions to evaluate")
    parser.add_argument("--output", type=str, default=None, help="Custom output JSON path")
    args = parser.parse_args()

    use_adapter = not args.no_adapter
    mode_name = "base" if not use_adapter else f"lora_{args.schema_mode}"
    out_file = Path(args.output) if args.output else Path(f"data/chinook_eval_{mode_name}.json")

    db = SQLiteDatabase(config.DB_PATH)
    client = ColabSQLClient()
    service = TextToSQLService(db, client)

    run_evaluation(
        service=service,
        output_path=out_file,
        limit=args.limit,
        use_adapter=use_adapter,
        schema_mode=args.schema_mode,
    )


if __name__ == "__main__":
    main()

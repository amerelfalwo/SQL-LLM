"""Compare two benchmark evaluation run JSONs.

Outputs:
1. Per-question correctness flips (Run A correct -> Run B wrong, and vice versa)
2. 2x2 Contingency Table
3. McNemar Exact Test p-value (two-tailed binomial test)
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def mcnemar_exact_p_value(b: int, c: int) -> float:
    """Calculate exact two-sided p-value for McNemar test using Binomial distribution.

    b: Number of items where Run A was correct and Run B was incorrect.
    c: Number of items where Run A was incorrect and Run B was correct.
    Under the null hypothesis, flips in either direction are equally likely (p=0.5).
    """
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    # Two-sided binomial test with p = 0.5
    cumulative_prob = sum(math.comb(n, i) * (0.5**n) for i in range(k + 1))
    return min(1.0, 2.0 * cumulative_prob)


def load_run(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_label(data: dict[str, Any], path: Path) -> str:
    summary = data.get("summary", {})
    adapter = "LoRA" if summary.get("use_adapter", True) else "Base"
    schema = summary.get("schema_mode", "custom")
    version = data.get("benchmark_version", summary.get("benchmark_version", "v2"))
    return f"{path.stem} [{adapter} | {schema} | {version}]"


def compare_runs(
    path_a: Path,
    path_b: Path,
    metric: str = "strict_match",
    label_a: str | None = None,
    label_b: str | None = None,
) -> None:
    data_a = load_run(path_a)
    data_b = load_run(path_b)

    name_a = label_a or get_label(data_a, path_a)
    name_b = label_b or get_label(data_b, path_b)

    records_a = {r["id"]: r for r in data_a.get("records", [])}
    records_b = {r["id"]: r for r in data_b.get("records", [])}

    all_ids = sorted(set(records_a.keys()) & set(records_b.keys()))
    if not all_ids:
        console.print("[bold red]Error: No common question IDs found between runs![/bold red]")
        return

    n11 = 0  # Both correct
    n10 = 0  # A correct, B wrong (Degraded)
    n01 = 0  # A wrong, B correct (Improved)
    n00 = 0  # Both wrong

    flips_a_to_b_wrong: list[tuple[dict, dict]] = []
    flips_a_to_b_correct: list[tuple[dict, dict]] = []

    for qid in all_ids:
        rec_a = records_a[qid]
        rec_b = records_b[qid]

        corr_a = bool(rec_a.get(metric, False))
        corr_b = bool(rec_b.get(metric, False))

        if corr_a and corr_b:
            n11 += 1
        elif corr_a and not corr_b:
            n10 += 1
            flips_a_to_b_wrong.append((rec_a, rec_b))
        elif not corr_a and corr_b:
            n01 += 1
            flips_a_to_b_correct.append((rec_a, rec_b))
        else:
            n00 += 1

    total = len(all_ids)
    acc_a = round(((n11 + n10) / total) * 100.0, 1)
    acc_b = round(((n11 + n01) / total) * 100.0, 1)
    delta = round(acc_b - acc_a, 1)

    p_value = mcnemar_exact_p_value(n10, n01)

    # 1. Main Header
    console.print(
        Panel.fit(
            f"[bold cyan]Benchmark Run Comparison ({metric})[/bold cyan]\n"
            f"[yellow]Run A:[/yellow] {name_a} -> [bold]{acc_a}%[/bold] ({n11 + n10}/{total})\n"
            f"[green]Run B:[/green] {name_b} -> [bold]{acc_b}%[/bold] ({n11 + n01}/{total})\n"
            f"[bold]Delta (B - A):[/bold] {'+' if delta >= 0 else ''}{delta}%",
            border_style="cyan",
        )
    )

    # 2. 2x2 Contingency Table
    table = Table(title="Paired 2x2 Contingency Table", header_style="bold magenta")
    table.add_column("", style="bold")
    table.add_column(f"Run B ({path_b.stem}) Correct", justify="center", style="green")
    table.add_column(f"Run B ({path_b.stem}) Wrong", justify="center", style="red")
    table.add_column("Run A Total", justify="center", style="cyan")

    table.add_row(f"Run A ({path_a.stem}) Correct", str(n11), str(n10), str(n11 + n10))
    table.add_row(f"Run A ({path_a.stem}) Wrong", str(n01), str(n00), str(n01 + n00))
    table.add_row("Run B Total", str(n11 + n01), str(n10 + n00), str(total))
    console.print(table)

    # 3. McNemar Test Result
    sig_note = (
        "[bold green]Statistically significant difference (p < 0.05)[/bold green]"
        if p_value < 0.05
        else "[yellow]Not statistically significant (p >= 0.05)[/yellow]"
    )
    console.print(
        Panel(
            f"[bold]McNemar's Test (Exact Binomial, Two-Tailed):[/bold]\n"
            f"Discordant pairs (b={n10}, c={n01}, total={n10 + n01})\n"
            f"Exact p-value: [bold cyan]{p_value:.4f}[/bold cyan] ({p_value:.6f})\n"
            f"Verdict: {sig_note}",
            title="Statistical Significance",
            border_style="magenta",
        )
    )

    # 4. Flips Breakdown
    if flips_a_to_b_wrong:
        flip_table = Table(
            title=f"Degradations: {path_a.stem} Correct -> {path_b.stem} Wrong ({len(flips_a_to_b_wrong)})",
            header_style="bold red",
        )
        flip_table.add_column("ID", style="bold", width=4)
        flip_table.add_column("Cat/Diff", style="cyan", width=18)
        flip_table.add_column("Question", width=36)
        flip_table.add_column(f"Run A SQL ({path_a.stem})", style="green", width=36)
        flip_table.add_column(f"Run B SQL & Failure ({path_b.stem})", style="red", width=36)

        for rec_a, rec_b in flips_a_to_b_wrong:
            flip_table.add_row(
                str(rec_a["id"]),
                f"{rec_a['category']}\n({rec_a['difficulty']})",
                rec_a["question"][:65] + "...",
                rec_a["predicted_sql"][:70] + "...",
                f"{rec_b['predicted_sql'][:50]}...\n[dim]Fail: {rec_b.get('failure_type')}[/dim]",
            )
        console.print(flip_table)

    if flips_a_to_b_correct:
        flip_table = Table(
            title=f"Improvements: {path_a.stem} Wrong -> {path_b.stem} Correct ({len(flips_a_to_b_correct)})",
            header_style="bold green",
        )
        flip_table.add_column("ID", style="bold", width=4)
        flip_table.add_column("Cat/Diff", style="cyan", width=18)
        flip_table.add_column("Question", width=36)
        flip_table.add_column(f"Run A SQL & Failure ({path_a.stem})", style="red", width=36)
        flip_table.add_column(f"Run B SQL ({path_b.stem})", style="green", width=36)

        for rec_a, rec_b in flips_a_to_b_correct:
            flip_table.add_row(
                str(rec_a["id"]),
                f"{rec_a['category']}\n({rec_a['difficulty']})",
                rec_a["question"][:65] + "...",
                f"{rec_a['predicted_sql'][:50]}...\n[dim]Fail: {rec_a.get('failure_type')}[/dim]",
                rec_b["predicted_sql"][:70] + "...",
            )
        console.print(flip_table)

    if not flips_a_to_b_wrong and not flips_a_to_b_correct:
        console.print("[dim]No flips between runs; identical predictions across all questions.[/dim]")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare two benchmark run JSON files")
    parser.add_argument("run_a", type=str, help="Path to Run A JSON (e.g. data/chinook_eval_lora_full.json)")
    parser.add_argument("run_b", type=str, help="Path to Run B JSON (e.g. data/chinook_eval_lora_linked.json)")
    parser.add_argument(
        "--metric",
        choices=["strict_match", "lenient_match", "valid"],
        default="strict_match",
        help="Comparison metric field (default: strict_match)",
    )
    parser.add_argument("--label-a", type=str, default=None, help="Display label for Run A")
    parser.add_argument("--label-b", type=str, default=None, help="Display label for Run B")
    args = parser.parse_args()

    compare_runs(
        path_a=Path(args.run_a),
        path_b=Path(args.run_b),
        metric=args.metric,
        label_a=args.label_a,
        label_b=args.label_b,
    )


if __name__ == "__main__":
    main()

"""Interactive terminal demo and scored benchmark."""

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.syntax import Syntax
from rich.table import Table

from sql_llm import config
from sql_llm.client import ColabSQLClient
from sql_llm.database import SQLiteDatabase
from sql_llm.examples import EXAMPLES
from sql_llm.service import TextToSQLService, results_match

console = Console()


def show_rows(columns: list[str], rows: list, title: str = "Results") -> None:
    table = Table(title=title, show_lines=True, header_style="bold magenta")
    for col in columns:
        table.add_column(str(col))
    for row in rows:
        table.add_row(*["NULL" if v is None else str(v) for v in row])
    console.print(table)


def ask_question(service: TextToSQLService, question: str):
    """Run one question, print SQL and results, return the report."""
    console.print(f"\n[bold cyan]Question:[/bold cyan] {question}")
    with console.status("[yellow]Generating SQL and executing...[/yellow]"):
        report = service.answer_question(question)

    if report.generation_error:
        console.print(f"[bold red]Model error:[/bold red] {report.generation_error}")
        return report

    console.print(Panel(Syntax(report.generated_sql, "sql", theme="monokai"),
                        title=f"Generated SQL ({report.inference_time_ms}ms)", expand=False))
    result = report.execution_result
    if not result.success:
        console.print(f"[bold red]{report.summary}[/bold red]")
    else:
        console.print(f"[bold green]{report.summary}[/bold green]")
        show_rows(result.columns, result.rows) if result.rows else console.print("[dim](0 rows)[/dim]")
    return report


def run_benchmark(service: TextToSQLService) -> None:
    """Score the model by comparing its result sets against gold SQL."""
    passed = 0
    for i, ex in enumerate(EXAMPLES, 1):
        console.rule(f"Case {i}/{len(EXAMPLES)}")
        report = ask_question(service, ex.question)
        gold = service.db.execute_query(ex.gold_sql, max_rows=1000)
        pred = service.db.execute_query(report.generated_sql, max_rows=1000) if report.generated_sql else None
        ok = bool(pred) and results_match(gold, pred)
        passed += ok
        console.print("[bold green]MATCH[/bold green]" if ok else
                      f"[bold red]MISMATCH[/bold red] [dim]gold: {ex.gold_sql}[/dim]")
    console.print(Panel(f"Execution accuracy: {passed}/{len(EXAMPLES)} ({100 * passed / len(EXAMPLES):.0f}%)",
                        style="bold yellow"))


def inspect_schema(db: SQLiteDatabase) -> None:
    tables = db.list_tables()
    listing = Table(title="Tables", header_style="bold cyan")
    listing.add_column("#", justify="right")
    listing.add_column("Name", style="green")
    for i, name in enumerate(tables, 1):
        listing.add_row(str(i), name)
    console.print(listing)
    choice = Prompt.ask("Table name to show DDL (Enter to return)", default="")
    if choice in tables:
        console.print(Panel(Syntax(db.get_table_schema(choice), "sql", theme="monokai"), title=choice))


def main() -> None:
    """CLI entry point."""
    db = SQLiteDatabase(config.DB_PATH)
    client = ColabSQLClient()
    console.print(Panel.fit("[bold cyan]Qwen2.5-Coder-3B Text-to-SQL[/bold cyan]\n"
                            f"[dim]Database: {config.DB_PATH.name}[/dim]", border_style="cyan"))

    if not client.is_configured():
        url = Prompt.ask("Colab public URL (Enter to skip)", default="")
        client = ColabSQLClient(url or None)
    health = client.check_health()
    console.print("[green]Model online[/green]" if health.get("status") == "healthy"
                  else f"[yellow]Model status: {health}[/yellow]")

    service = TextToSQLService(db, client)
    while True:
        console.print("\n1. Ask a question   2. Run benchmark   3. Inspect schema   4. Exit")
        choice = Prompt.ask("Choose", choices=["1", "2", "3", "4"], default="1")
        if choice == "1":
            question = Prompt.ask("Question").strip()
            if question:
                ask_question(service, question)
        elif choice == "2":
            run_benchmark(service)
        elif choice == "3":
            inspect_schema(db)
        else:
            break


if __name__ == "__main__":
    main()

# SQL-LLM — Text-to-SQL Laboratory & Benchmark

A Text-to-SQL playground and benchmark powered by a fine-tuned LoRA adapter ([`amer003100/qwen2.5-coder-3b-text-to-sql-lora`](https://huggingface.co/amer003100/qwen2.5-coder-3b-text-to-sql-lora), built on `Qwen/Qwen2.5-Coder-3B-Instruct`). Translates natural language questions into verified, executable SQL against the 11-table [Chinook](https://github.com/lerocha/chinook-database) sample relational database.

---

## 📊 Evaluation & Benchmarks

To ensure rigorous evaluation, metrics are separated into two distinct, unmixed benchmarks: the in-distribution test set and a real multi-table sample database.

### 1. In-Distribution Held-Out Test Set (Gretel Synthetic, $n=200$)
Evaluated on 200 held-out prompts from `gretelai/synthetic_text_to_sql` (SQLite dialect):

| Model Configuration | Valid SQL Rate | Execution Accuracy | 95% Wilson Confidence Interval | Notes |
|---|---|---|---|---|
| **Base Model (`Qwen2.5-Coder-3B-Instruct`)** | 89.5% | 57.0% | [50.1%, 63.7%] | Zero-shot prompting |
| **Fine-Tuned Adapter (LoRA $r=16$)** | **97.5%** (+8.0%) | **69.5%** (+12.5%) | [62.8%, 75.5%] | 1 epoch, 6,330 gold pairs |

---

### 2. Chinook Database Benchmark v2 ($n=40$, Sample Database)
Evaluated on a curated, quality-gated suite of 40 questions spanning single-table queries, aggregations, 2-to-4-table JOINs, and subqueries against `data/Chinook_Sqlite.sqlite` (sample database, not in the fine-tuning data; $n=40$, 95% Wilson CI $\pm \sim 13$ points).

> **Benchmark Version Notice:** Benchmark v1 (which produced 57.5%) was revised after the first run to eliminate invalid evaluation artifacts (such as empty result sets, arbitrary `LIMIT` clauses without `ORDER BY`, and untied boundary sort keys). The current canonical benchmark is **Benchmark v2** (`BENCHMARK_VERSION="v2"`), and v1 results are not comparable.

All 40 questions pass strict automated quality validation (`scripts/validate_benchmark.py`), ensuring complete determinism, absence of ties at LIMIT boundaries, and unambiguous column contracts.

#### Headline Performance (Fine-Tuned Adapter, Full Schema)
| Metric | Result | 95% Wilson Confidence Interval | Notes |
|---|---|---|---|
| **Strict Execution Accuracy** | **77.5%** (31 / 40) | **[62.5%, 87.7%]** | Exact columns, exact positions, result match |
| **Lenient Execution Accuracy** | **77.5%** (31 / 40) | **[62.5%, 87.7%]** | Permuted / superset column acceptance |
| **Valid SQL Rate** | **85.0%** (34 / 40) | **[70.9%, 93.3%]** | Syntactically correct & executable by SQLite |
| **End-to-End Latency** | **3.80 s** | — | End-to-end latency via ngrok (Colab T4 GPU) |

#### Difficulty Breakdown ($n=40$)
Difficulty counts strictly reflect the canonical benchmark definitions:

| Difficulty | Questions | Strict Match Count | Strict Accuracy | Lenient Accuracy |
|---|---|---|---|---|
| **Easy** | 8 | 8 | **100.0%** | 100.0% |
| **Medium** | 19 | 16 | **84.2%** | 84.2% |
| **Hard** (Multi-Table JOINs / Subqueries) | 13 | 7 | **53.8%** | 53.8% |
| **Total** | 40 | 31 | **77.5%** | 77.5% |

#### Category Breakdown
*(Per evaluation standards, categories with $n < 5$ report exact counts $k/n$ without misleading pseudo-precise percentages.)*

| Category | Total Questions ($n$) | Strict Match ($k/n$) | Strict Accuracy | Key Patterns Tested |
|---|---|---|---|---|
| **Single-Table Aggregations** | 7 | 7 / 7 | **100.0%** | `COUNT`, `SUM`, `AVG`, `MIN`, `MAX` |
| **Filter & Sort** | 9 | 9 / 9 | **100.0%** | `WHERE`, `ORDER BY`, `LIMIT` |
| **2-Table JOINs** | 8 | 6 / 8 | **75.0%** | `Artist ⇄ Album`, `Genre ⇄ Track`, `Invoice ⇄ Customer` |
| **Multi-Table JOINs (3–4 Tables)** | 10 | 6 / 10 | **60.0%** | `Invoice ⇄ InvoiceLine ⇄ Track ⇄ Album ⇄ Artist` |
| **Date & Time Operations** | 2 | 1 / 2 | — *(n < 5)* | Year extraction (`strftime`) and date filtering |
| **Subqueries & CTEs** | 2 | 1 / 2 | — *(n < 5)* | Correlated / uncorrelated subqueries |
| **Grouping & Having** | 1 | 1 / 1 | — *(n < 5)* | `GROUP BY ... HAVING COUNT(*) > 5` |
| **Self-Join & Hierarchy** | 1 | 0 / 1 | — *(n < 5)* | Employee-to-manager hierarchical join |

---

### 3. Prompt Schema Ablation Study ($n=40$)

We evaluated the fine-tuned model under three schema representation strategies:
- **Config A (`full`):** Full DDL schema for all 11 database tables (standard baseline).
- **Config B (`linked`):** Only tables relevant to the question (max 4, scored by keyword overlap and CamelCase split, plus foreign key neighbors), formatted as compact DDL (`CREATE TABLE Artist (ArtistId INTEGER, Name TEXT);` without noise).
- **Config C (`linked_rows`):** Config B + 2 sample rows per table formatted as `INSERT INTO Table VALUES (...);`.

| Schema Mode | Strict Accuracy (95% CI) | Lenient Accuracy | Valid SQL Rate | Avg End-to-End Latency (ngrok) |
|---|---|---|---|---|
| **Config A (`full`)** | **77.5%** [62.5%, 87.7%] (31/40) | 77.5% | 85.0% | 3.80 s |
| **Config B (`linked`)** | 70.0% [54.6%, 81.9%] (28/40) | 70.0% | 90.0% | 3.62 s |
| **Config C (`linked_rows`)** | **77.5%** [62.5%, 87.7%] (31/40) | 77.5% | **95.0%** | **3.59 s** |

> **Statistical Significance Note:** Differences across all three ablation configurations (in execution accuracy, valid SQL rate, and latency) are **not statistically significant** at $n=40$ using McNemar's exact two-tailed binomial test:
> - Config A vs Config B: $b=6, c=3, p = 0.5078$ ($\ge 0.05$)
> - Config A vs Config C: $b=3, c=3, p = 1.0000$ ($\ge 0.05$)
> - Config B vs Config C: $b=0, c=3, p = 0.2500$ ($\ge 0.05$)
> 
> At $n=40$, observed variations in latency and valid SQL rate cannot be claimed as statistically meaningful improvements or efficiencies; a larger sample size ($n \ge 200$) is required to detect small effect sizes.



---

### 4. Real Failure Mode Analysis

From the 9 failed queries in the benchmark results (`data/chinook_eval_lora_full.json`), representative failure modes are classified into standard taxonomies:

| Question ID | Category | Question Prompt | Model Prediction (Snippet) | Failure Type | Root Cause |
|---|---|---|---|---|---|
| **#16** | 2-Table Join | First 10 albums with artist name | `SELECT a.Title, a.Name FROM Album a ...` | `wrong_table_or_column` | Model omitted joining the `Artist` table inside a subquery; `Album` has no `Name` column. |
| **#21** | 2-Table Join | Media type used by most tracks | `... ORDER BY TrackCount DESC;` (no LIMIT) | `wrong_logic` | Model omitted `LIMIT 1`, returning all media types instead of only the top one. |
| **#23** | Multi-Join | Top 5 customers by total spent | `SELECT CustomerId, FirstName ... FROM InvoiceLine JOIN Invoice` | `wrong_table_or_column` | Model omitted joining the `Customer` table when selecting `FirstName` and `LastName`. |
| **#24** | Multi-Join | Tracks composed by Miles Davis | `FROM Track T JOIN Album A ... JOIN Artist A` | `syntax_or_dialect` | Model assigned alias `A` to both `Album` and `Artist`, triggering `ambiguous column name`. |
| **#30** | Multi-Join | Items purchased in first 5 invoices | `... WHERE InvoiceId IN (SELECT TOP 5 ...)` | `syntax_or_dialect` | Dialect leak: used SQL Server T-SQL `TOP 5` inside subquery instead of SQLite `LIMIT 5`. |
| **#32** | Date/Time | Total annual sales revenue | `SELECT YEAR(InvoiceDate) ...` | `syntax_or_dialect` | Dialect leak: used MySQL `YEAR()` instead of SQLite `strftime('%Y', InvoiceDate)`. |

---

### 5. Benchmark Quality Gate (`scripts/validate_benchmark.py`)

All benchmark questions must satisfy automated quality checks enforced by `scripts/validate_benchmark.py` and wrapped in `tests/test_benchmark_quality.py`:
- **Syntax & Execution:** Gold queries must execute without error on `data/Chinook_Sqlite.sqlite`.
- **Non-Trivial Results:** Rejects queries returning empty sets (`0 rows`) or trivial single zeros/NULLs (`[(0,)]`, `[(None,)]`).
- **Determinism:** Any query with `LIMIT N` must include an `ORDER BY` with secondary tiebreakers; flags an error if row $N$ and row $N+1$ share identical sort keys.
- **No Hidden Truncation:** Prohibits `LIMIT` clauses when the question prompt specifies "all".
- **Column Specification:** Prompts explicitly specify target columns (`Return only ...`) to prevent ambiguous `SELECT *`.

```bash
# Run the quality validator
uv run python scripts/validate_benchmark.py

# Run quality gate via pytest
uv run pytest tests/test_benchmark_quality.py
```

---

## 🏛️ System Architecture

```
┌────────────────────────────────┐         ┌─────────────────────────────────────┐
│  Next.js 15 Web Application    │         │  FastAPI Backend Service            │
│  Port :3000 (Editorial UI)     │──proxy─►│  Port :8000                         │
│  - Natural warm bone palette   │         │  - Schema & DDL extraction          │
│  - Live SQL Editor & Re-run    │         │  - Read-only SQLite Sandbox         │
│  - CSV Export & JSON copy      │         │  - Result-set comparison engine     │
└────────────────────────────────┘         └──────────────────┬──────────────────┘
                                                              │
                                            ┌─────────────────┴─────────────────┐
                                            │                                   │
                                            ▼                                   ▼
                                ┌───────────────────────┐           ┌───────────────────────┐
                                │ Local SQLite Database │           │ Remote GPU Inference  │
                                │ (mode=ro + AST guard  │           │ (Colab + ngrok)       │
                                │  + progress timeout)  │           │ Qwen2.5-Coder-3B-LoRA │
                                └───────────────────────┘           └───────────────────────┘
```

---

## 🛡️ Database Execution Security

Execution against SQLite is protected server-side through four independent security layers:
1. **Engine-Level Read-Only Mode:** SQLite connection opened with `file:...?mode=ro` and reinforced with `PRAGMA query_only=ON;`.
2. **AST Parsing via SQLGlot:** Parses incoming queries with `sqlglot` (SQLite dialect); strictly accepts only a single `exp.Select` or `exp.Union` statement. Blocks multiple statements, comments injection, and any `exp.Pragma`, `exp.Drop`, `exp.Delete`, `exp.Insert`, or `exp.Update`.
3. **Execution Timeout Handler:** Configured via `conn.set_progress_handler` checking elapsed time against a deadline (default 3.0 seconds). Automatically aborts runaway queries or infinite recursive CTEs.
4. **Row Truncation:** Results capped at `max_rows` (default 50 for interactive UI, 1000 for benchmarks).

---

## 🔬 Reproducing the Benchmark Runs

```bash
# Full Schema (Config A, Baseline)
uv run python -m sql_llm.eval_runner --schema-mode full --output data/chinook_eval_lora_full.json

# Linked Compact DDL (Config B)
uv run python -m sql_llm.eval_runner --schema-mode linked --output data/chinook_eval_lora_linked.json

# Linked Compact DDL + Sample Rows (Config C)
uv run python -m sql_llm.eval_runner --schema-mode linked_rows --output data/chinook_eval_lora_linked_rows.json

# Base Model (Disable LoRA adapter)
uv run python -m sql_llm.eval_runner --no-adapter --output data/chinook_eval_base.json
```

---

## 🧪 Testing & Code Quality

```bash
# Run all unit tests (DB safety, AST validator, quality gate, benchmark suite)
uv run pytest

# Python linter and formatter check
uv run ruff check src tests scripts

# Frontend TypeScript check
cd web && npx tsc --noEmit
```
All 64 tests pass with zero warnings.

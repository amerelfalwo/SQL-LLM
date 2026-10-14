# SQL-LLM — Text-to-SQL Laboratory & Benchmark

A specialized Text-to-SQL system powered by a fine-tuned LoRA adapter ([`amer003100/qwen2.5-coder-3b-text-to-sql-lora`](https://huggingface.co/amer003100/qwen2.5-coder-3b-text-to-sql-lora), built on `Qwen/Qwen2.5-Coder-3B-Instruct`). Translates natural language into verified, executable SQL against the multi-table [Chinook](https://github.com/lerocha/chinook-database) relational database.

---

## 📊 Key Results & Benchmarks

The benchmark that matters most is performance on an **actual, unseen relational database** (`Chinook_Sqlite.sqlite` — 11 tables with foreign key constraints), not just held-out synthetic test prompts.

### 1. Real-World Database Benchmark (Chinook — 40 Curated Questions)
Evaluated end-to-end on 40 curated questions spanning single-table queries, aggregations, 2-to-4-table JOINs, subqueries, and date manipulations against `data/Chinook_Sqlite.sqlite`. Execution accuracy is measured using the notebook's exact `results_match` protocol (order-insensitive set comparison with float tolerance).

| Metric | Result | Context / Details |
|---|---|---|
| **Execution Accuracy** | **57.5%** (23 / 40) | Exact result-set match against SQLite ground-truth |
| **Valid SQL Rate** | **95.0%** (38 / 40) | Syntactically correct & successfully executed by SQLite |
| **Average Inference Time** | **3.54 s** | Measured on Colab T4 GPU via FastAPI/ngrok |
| **Evaluated Questions** | **40** | Full spectrum across 11 relational tables |

#### Breakdown by Query Difficulty
| Difficulty | Total Questions | Exact Match Count | Execution Accuracy |
|---|---|---|---|
| **Easy** | 8 | 6 | **75.0%** |
| **Medium** | 19 | 13 | **68.4%** |
| **Hard** (Multi-Joins / Subqueries) | 13 | 4 | **30.8%** |

#### Breakdown by Query Category
| Category | Questions | Execution Accuracy | Key Patterns Tested |
|---|---|---|---|
| **Single-Table Aggregations** | 7 | **85.7%** | `COUNT`, `SUM`, `AVG`, `MIN`, `MAX` |
| **2-Table JOINs** | 8 | **75.0%** | `Artist ⇄ Album`, `Genre ⇄ Track`, `Invoice ⇄ Customer` |
| **Filter & Sort** | 9 | **66.7%** | `WHERE`, `ORDER BY`, `LIMIT` |
| **Date & Time Operations** | 2 | **50.0%** | Date range filters, year extractions |
| **Multi-Table JOINs (3–4 Tables)** | 10 | **40.0%** | `Invoice ⇄ InvoiceLine ⇄ Track ⇄ Album ⇄ Artist` |
| **Subqueries & Grouping / Having** | 4 | **0.0%** | Correlated subqueries and complex HAVING clauses |

---

### 2. Generalization Comparison: Synthetic vs. Real Database

| Evaluation Stage | Dataset Nature | Target Schema | Valid SQL Rate | Execution Accuracy |
|---|---|---|---|---|
| **Real Database (Chinook)** | Unseen Production Database | 11 Relational Tables | **95.0%** | **57.5%** |
| **Fine-Tuned Adapter (Held-out)** | Synthetic (`gretelai`) | In-Distribution Prompts | **97.5%** | **69.5%** (+12.5% vs Base) |
| **Base Model (`Qwen2.5-Coder-3B`)** | Synthetic (`gretelai`) | In-Distribution Prompts | 89.5% | 57.0% |

> **Key Finding:** Moving from in-distribution synthetic test questions (69.5%) to an unseen 11-table real database (57.5%) confirms strong zero-shot cross-schema generalization, with an impressive 95.0% syntax validity on complex relational SQLite queries.

---

## 🔬 Reproducing the Chinook Benchmark

To execute the 40-question benchmark suite against your running model and recalculate execution accuracy:

```bash
uv run sql-llm-eval
```

This runs `src/sql_llm/eval_runner.py`:
1. Executes each question through the model pipeline (`question → schema DDL → generated SQL`).
2. Executes both the generated SQL and the verified Gold SQL against `data/Chinook_Sqlite.sqlite`.
3. Compares result sets with `results_match(gold, predicted)`.
4. Prints the detailed summary table and saves full per-query logs to `data/chinook_evaluation_results.json`.

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
                                │ (mode=ro + keyword    │           │ (Colab + ngrok)       │
                                │  protection guard)    │           │ Qwen2.5-Coder-3B-LoRA │
                                └───────────────────────┘           └───────────────────────┘
```

The system uses a clean separation of concerns:
- **Local Client / Backend:** Native Python 3.12, strict read-only SQLite connections, FastAPI REST endpoints, and Next.js frontend.
- **Remote Model Service:** Colab T4/L4 GPU running `colab/server.py` via ngrok tunnel (serving the LoRA adapter without requiring local CUDA hardware).

---

## 📁 Repository Structure

```
SQL-LLM/
├── colab/
│   ├── server.py              # Model API (FastAPI + ngrok) running on Colab GPU
│   └── notebook.ipynb         # Jupyter launcher for server.py
├── data/
│   ├── Chinook_Sqlite.sqlite  # 11-table relational SQLite database
│   └── chinook_evaluation_results.json # Full benchmark results log
├── src/sql_llm/
│   ├── config.py              # Environment variables & configuration
│   ├── database.py            # SQLite wrapper (mode=ro, schema extraction, safe execution)
│   ├── client.py              # HTTP client for the Colab inference endpoint
│   ├── service.py             # Pipeline: schema → model → execution → results_match
│   ├── benchmark_dataset.py   # 40 curated Chinook questions & gold SQL
│   ├── eval_runner.py         # Automated evaluation harness
│   ├── examples.py            # Quick example questions for UI and CLI
│   ├── api.py                 # REST API endpoints (/api/v1/...)
│   ├── runner.py              # Concurrent launcher (backend + frontend)
│   └── cli.py                 # Interactive terminal runner
├── tests/
│   ├── test_database.py       # DB safety, schemas, and query execution tests
│   └── test_benchmark.py      # Automated validation of all 40 benchmark questions
└── web/                       # Next.js frontend (TypeScript, Tailwind, Minimalist UI)
```

---

## 🚀 Quick Start

### Prerequisites
- Python ≥ 3.12 with [uv](https://docs.astral.sh/uv/) installed.
- Node.js ≥ 20.
- A free Google Colab account (for GPU execution).

### 1. Launch the Model on Google Colab
1. Open Google Colab and set **Runtime → Change runtime type → T4 GPU**.
2. Upload and open [`colab/notebook.ipynb`](colab/notebook.ipynb).
3. Upload [`colab/server.py`](colab/server.py) and provide your [ngrok authtoken](https://dashboard.ngrok.com/get-started/your-authtoken).
4. Run the notebook cells; copy the public tunnel URL (`https://xxxx.ngrok-free.dev`).

### 2. Configure Environment
Create a `.env` file in the project root:
```env
COLAB_API_URL=https://xxxx.ngrok-free.dev
```

### 3. Launch with One Command
```bash
uv sync
uv run dev
```
This runs the FastAPI backend on `http://localhost:8000` and the Next.js frontend on `http://localhost:3000`.

---

## 🛡️ Safety & Execution Security

1. **Strict Read-Only Enforcement:** SQLite connections use URI mode `file:...?mode=ro`, physically preventing any write, update, or schema alteration.
2. **Statement Blocklist:** All incoming queries are inspected before execution to block state-altering statements (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `ATTACH`, `PRAGMA`).
3. **Execution Timeouts:** Query execution is guarded with strict timeout boundaries to prevent long-running table lockups.
4. **Credential Isolation:** API keys and ngrok tokens remain exclusively in local environment files (`.env`), which are permanently git-ignored.

---

## 🧪 Testing & Code Quality

```bash
# Run all unit tests (DB safety + 40 benchmark gold queries)
uv run pytest

# Python linter and formatter check
uv run ruff check src tests

# Frontend TypeScript check
cd web && npx tsc --noEmit
```
All 57 unit tests pass with zero warnings.

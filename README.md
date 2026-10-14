# SQL-LLM — Text-to-SQL Playground

Demo for a LoRA adapter fine-tuned on `gretelai/synthetic_text_to_sql`
([`amer003100/qwen2.5-coder-3b-text-to-sql-lora`](https://huggingface.co/amer003100/qwen2.5-coder-3b-text-to-sql-lora),
base `Qwen/Qwen2.5-Coder-3B-Instruct`). Ask a question in plain language, get SQL, run it against the
[Chinook](https://github.com/lerocha/chinook-database) SQLite database and check whether the answer is right.

> Reported on 200 held-out questions (SQLite, execution accuracy): base 57.0% → with adapter **69.5%**
> (valid SQL 89.5% → 97.5%). Small test set, SQLite only.

## Architecture

```
Browser ──► Next.js (web/, :3000) ──proxy /api/v1──► FastAPI (src/sql_llm/api.py, :8000)
                                                        │            │
                                         read-only SQLite (data/)    └─► ngrok ─► Colab GPU (colab/server.py)
                                                                              Qwen2.5-Coder-3B + LoRA
```

The model runs on a Colab GPU because the Hugging Face serverless API cannot serve LoRA adapters
and this machine has no CUDA GPU. Everything else runs locally.

```
SQL-LLM/
├── colab/
│   ├── server.py          # Model API (FastAPI + ngrok) — runs on Colab
│   └── notebook.ipynb     # Thin launcher for server.py
├── data/Chinook_Sqlite.sqlite
├── src/sql_llm/
│   ├── config.py          # .env loading, paths, CORS origins
│   ├── database.py        # Read-only SQLite, schema (DDL) extraction, safe execution
│   ├── client.py          # HTTP client for the Colab model API
│   ├── service.py         # question → schema → SQL → execution; result-set comparison
│   ├── examples.py        # Example questions + gold SQL (shared by UI and benchmark)
│   ├── api.py             # REST API for the frontend (/api/v1/...)
│   └── cli.py             # Terminal demo + scored benchmark
├── tests/                 # pytest
└── web/                   # Next.js (App Router, TypeScript)
```

## Setup

Requirements: Python ≥ 3.12 with [uv](https://docs.astral.sh/uv/), Node.js ≥ 20, a Google account for Colab.

### 1. Start the model on Colab
1. Open Colab, upload [`colab/notebook.ipynb`](colab/notebook.ipynb), set **Runtime → GPU**.
2. Run the cells; upload [`colab/server.py`](colab/server.py) when asked and paste your
   [ngrok token](https://dashboard.ngrok.com/get-started/your-authtoken).
3. Copy the printed `https://….ngrok-free.dev` URL.

### 2. Configure
Create `.env` in the project root (never commit it; it is git-ignored):
```env
COLAB_API_URL=https://xxxx.ngrok-free.dev
# optional
# DB_PATH=data/Chinook_Sqlite.sqlite
# ALLOWED_ORIGINS=http://localhost:3000
```
You can also paste the URL into the web UI instead.

### 3. Run (One Command)
```bash
uv sync
uv run dev   # Starts both FastAPI backend (:8000) and Next.js frontend (:3000)
```
Open **http://localhost:3000** in your browser.

Or run components individually if preferred:
- Backend only: `uv run sql-llm-api`
- Frontend only: `npm run dev --prefix web`
- Terminal CLI: `uv run sql-llm`

## Checking correctness
- **Web:** pick an example chip or type a question; edit the generated SQL and re-run it to compare.
- **CLI benchmark (`uv run sql-llm` → option 2):** runs the questions in
  [`examples.py`](src/sql_llm/examples.py) and compares each result set with the gold SQL
  (order-insensitive, floats rounded to 2 decimals). Questions name the expected columns so the
  comparison is fair. This is a quick sanity check, not a replacement for the 200-question evaluation above.

## API (`/api/v1`)
| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Backend + model status |
| GET | `/schema` | Tables and DDL |
| GET | `/examples` | Example questions |
| POST | `/ask` | `{question}` → generated SQL + execution result |
| POST | `/execute` | `{sql}` → run (edited) SQL read-only |
| POST | `/config` | `{colab_api_url}` → set model URL at runtime |

Errors use `{code, message, details, traceId}`.

## Safety
- The database is opened with SQLite `mode=ro`, plus a keyword guard (`DROP`, `DELETE`, `PRAGMA`, …).
- Generated SQL is never trusted: it only ever runs through the read-only connection.
- Secrets live in `.env` only. Rotate any token that has been shared.

## Development
```bash
uv run pytest -q
uv run ruff check src tests
cd web && npm run lint && npx tsc --noEmit
```

## Limitations
Evaluated on SQLite only, on a small test set; not tested on other dialects. Follow the base model's license.

"""REST API consumed by the Next.js frontend.

Run: uv run sql-llm-api   (or: uv run uvicorn sql_llm.api:app --port 8000)
"""

import uuid
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from sql_llm import config
from sql_llm.client import ColabSQLClient
from sql_llm.database import QueryResult, SQLiteDatabase
from sql_llm.examples import EXAMPLES
from sql_llm.service import TextToSQLService

app = FastAPI(title="SQL-LLM API", version="1.0.0")
app.add_middleware(
    CORSMiddleware, allow_origins=config.ALLOWED_ORIGINS, allow_methods=["GET", "POST"], allow_headers=["*"]
)

db = SQLiteDatabase(config.DB_PATH)
_runtime_url: dict[str, str | None] = {"value": None}  # set from the UI, overrides COLAB_API_URL


def _client() -> ColabSQLClient:
    return ColabSQLClient(_runtime_url["value"])


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    max_rows: int = Field(default=25, ge=1, le=200)


class ExecuteRequest(BaseModel):
    sql: str = Field(min_length=1, max_length=5000)
    max_rows: int = Field(default=50, ge=1, le=200)


class ConfigRequest(BaseModel):
    colab_api_url: str = Field(pattern=r"^https?://")


class ExecutionOut(BaseModel):
    success: bool
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    execution_time_ms: float
    error: str | None = None

    @classmethod
    def from_result(cls, res: QueryResult) -> "ExecutionOut":
        return cls(success=res.success, columns=res.columns, rows=[list(r) for r in res.rows],
                   row_count=res.row_count, execution_time_ms=res.execution_time_ms, error=res.error)


class AskResponse(BaseModel):
    question: str
    sql: str
    success: bool
    summary: str
    generation_error: str | None = None
    inference_time_ms: float
    execution: ExecutionOut | None = None


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception) -> JSONResponse:
    trace_id = uuid.uuid4().hex
    print(f"[{trace_id}] unhandled error: {exc!r}")
    return JSONResponse(
        status_code=500,
        content={"code": "internal_error", "message": "Internal server error", "details": None, "traceId": trace_id},
    )


@app.get("/api/v1/health")
def health() -> dict:
    client = _client()
    return {"api": "ok", "database": config.DB_PATH.name, "model": client.check_health(),
            "colab_configured": client.is_configured()}


@app.get("/api/v1/schema")
def schema() -> dict:
    return {"tables": [{"name": t, "ddl": db.get_table_schema(t)} for t in db.list_tables()]}


@app.get("/api/v1/examples")
def examples() -> dict:
    return {"examples": [e.question for e in EXAMPLES]}


@app.post("/api/v1/config")
def set_config(req: ConfigRequest) -> dict:
    _runtime_url["value"] = req.colab_api_url.rstrip("/")
    return {"model": _client().check_health()}


@app.post("/api/v1/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    client = _client()
    if not client.is_configured():
        raise HTTPException(503, detail={"code": "model_unconfigured", "message": "Colab API URL is not configured."})
    report = TextToSQLService(db, client).answer_question(req.question, max_result_rows=req.max_rows)
    return AskResponse(
        question=report.question,
        sql=report.generated_sql,
        success=report.success,
        summary=report.summary,
        generation_error=report.generation_error,
        inference_time_ms=report.inference_time_ms,
        execution=ExecutionOut.from_result(report.execution_result) if report.execution_result else None,
    )


@app.post("/api/v1/execute", response_model=ExecutionOut)
def execute(req: ExecuteRequest) -> ExecutionOut:
    """Run user-edited SQL (read-only enforced by the database layer)."""
    return ExecutionOut.from_result(db.execute_query(req.sql, max_rows=req.max_rows))


def serve() -> None:
    """Console-script entry point."""
    uvicorn.run("sql_llm.api:app", host="127.0.0.1", port=8000)

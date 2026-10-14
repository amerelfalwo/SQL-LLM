"""HTTP client for the Colab-hosted text-to-SQL model."""

from dataclasses import dataclass
from typing import ClassVar

import requests

from sql_llm import config


@dataclass
class GenerationResult:
    """Result of one model call; `error` is set on failure."""

    sql: str = ""
    raw_output: str = ""
    inference_time_ms: float = 0.0
    error: str | None = None


class ColabSQLClient:
    """Talks to `colab/server.py` through its ngrok URL."""

    # Free ngrok domains serve an interstitial page to non-browser clients.
    HEADERS: ClassVar[dict[str, str]] = {"ngrok-skip-browser-warning": "1"}

    def __init__(self, api_url: str | None = None, timeout: int = 120):
        self.api_url = (api_url or config.COLAB_API_URL).rstrip("/")
        self.timeout = timeout

    def is_configured(self) -> bool:
        return self.api_url.startswith("http")

    def check_health(self) -> dict:
        if not self.is_configured():
            return {"status": "unconfigured", "error": "COLAB_API_URL is not set"}
        try:
            resp = requests.get(f"{self.api_url}/health", headers=self.HEADERS, timeout=10)
        except requests.RequestException as exc:
            return {"status": "unreachable", "error": str(exc)}
        if resp.status_code == 200:
            return resp.json()
        return {"status": "error", "code": resp.status_code, "text": resp.text}

    def generate_sql(
        self, schema_sql: str, question: str, temperature: float = 0.1, max_new_tokens: int = 256
    ) -> GenerationResult:
        if not self.is_configured():
            return GenerationResult(error="COLAB_API_URL is not configured.")

        payload = {
            "schema_sql": schema_sql,
            "question": question,
            "temperature": temperature,
            "max_new_tokens": max_new_tokens,
        }
        try:
            resp = requests.post(
                f"{self.api_url}/generate_sql", json=payload, headers=self.HEADERS, timeout=self.timeout
            )
        except requests.Timeout:
            return GenerationResult(error=f"Request timed out after {self.timeout}s.")
        except requests.RequestException as exc:
            return GenerationResult(error=f"Connection error: {exc}. Is the Colab tunnel running?")

        if resp.status_code != 200:
            return GenerationResult(error=f"API error ({resp.status_code}): {resp.text}")
        data = resp.json()
        return GenerationResult(
            sql=data.get("sql", "").strip(),
            raw_output=data.get("raw_output", ""),
            inference_time_ms=data.get("inference_time_ms", 0.0),
        )

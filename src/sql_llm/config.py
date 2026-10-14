"""Central configuration: loads `.env` once and exposes typed settings."""

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

DB_PATH = PROJECT_ROOT / os.getenv("DB_PATH", "data/Chinook_Sqlite.sqlite")
COLAB_API_URL = os.getenv("COLAB_API_URL", "")
API_KEY = os.getenv("API_KEY", os.getenv("SQL_LLM_API_KEY", ""))
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")]


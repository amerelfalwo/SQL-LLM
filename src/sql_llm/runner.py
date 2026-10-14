"""Unified development runner to launch both FastAPI backend and Next.js frontend with one command."""

import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
WEB_DIR = ROOT_DIR / "web"


def run_all() -> None:
    """Launch FastAPI on :8000 and Next.js on :3000 concurrently."""
    print("=" * 60)
    print("🚀 Starting SQL-LLM Fullstack Development Environment...")
    print("=" * 60)

    # 1. Start FastAPI backend
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "sql_llm.api:app", "--port", "8000"],
        cwd=ROOT_DIR
    )

    # 2. Start Next.js frontend
    frontend_proc = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=WEB_DIR
    )

    print("\n✅ Services running:")
    print("   🌐 Web UI:       http://localhost:3000")
    print("   ⚡ REST API:     http://localhost:8000")
    print("   📊 API Docs:     http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop both servers.\n")

    def shutdown(sig, frame):
        print("\nStopping services...")
        backend_proc.terminate()
        frontend_proc.terminate()
        backend_proc.wait()
        frontend_proc.wait()
        print("All services stopped.")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Keep runner alive
    try:
        while True:
            time.sleep(1)
            if backend_proc.poll() is not None or frontend_proc.poll() is not None:
                break
    except KeyboardInterrupt:
        shutdown(None, None)


if __name__ == "__main__":
    run_all()

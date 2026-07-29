"""Optional web entrypoint for platforms that require a long-running web app.

Start command:
  uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

try:
    from fastapi import FastAPI
except Exception as exc:  # pragma: no cover
    raise RuntimeError("Install fastapi and uvicorn or use the CLI entrypoint main.py") from exc

app = FastAPI(title="ACMF Pipeline")

@app.get("/")
def root():
    return {"status": "ok", "service": "ACMF", "default_task": os.getenv("TASK", "v2_4_9")}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/run/{task}")
def run_task(task: str):
    root_dir = Path(__file__).resolve().parent
    cmd = [sys.executable, str(root_dir / "main.py"), "--task", task]
    proc = subprocess.run(cmd, cwd=root_dir, text=True, capture_output=True, timeout=600)
    return {"task": task, "returncode": proc.returncode, "stdout": proc.stdout[-4000:], "stderr": proc.stderr[-4000:]}

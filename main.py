"""ACMF deployment entrypoint.

Use this as the root Python entrypoint for batch/worker deployments.
Examples:
  python main.py --task v2_4_9
  TASK=v2_4_9 python main.py
"""
from __future__ import annotations

import argparse
import importlib
import os
import sys
from pathlib import Path

TASKS = {
    "v2_4_7": "empirical.scripts.run_v2_4_7_regional_regime_explanation",
    "v2_4_8": "empirical.scripts.run_v2_4_8_quebec_70_74_case_study",
    "v2_4_9": "empirical.scripts.run_v2_4_9_quebec_70_74_alpha_sensitivity",
}


def run_task(task: str) -> int:
    if task == "health":
        print("ACMF entrypoint OK")
        return 0
    if task not in TASKS:
        print(f"Unknown task: {task}", file=sys.stderr)
        print("Available tasks: " + ", ".join(sorted(TASKS)), file=sys.stderr)
        return 2
    repo_root = Path(__file__).resolve().parent
    sys.path.insert(0, str(repo_root))
    module = importlib.import_module(TASKS[task])
    if not hasattr(module, "main"):
        print(f"Task module has no main(): {TASKS[task]}", file=sys.stderr)
        return 3
    module.main()
    return 0


def cli() -> int:
    parser = argparse.ArgumentParser(description="ACMF pipeline entrypoint")
    parser.add_argument("--task", default=os.getenv("TASK", "v2_4_9"), help="Task to run: v2_4_7, v2_4_8, v2_4_9, health")
    args = parser.parse_args()
    return run_task(args.task)


if __name__ == "__main__":
    raise SystemExit(cli())


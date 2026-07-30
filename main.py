from __future__ import annotations
import argparse, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))
from acmf.task_runner import run_task
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--task', default='health')
    raise SystemExit(run_task(ap.parse_args().task))

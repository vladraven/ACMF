"""ACMF deployment entrypoint.

Use this as the root Python entrypoint for batch/worker deployments.
Examples:
  python main.py --task health
  python main.py --task v2_4_9
  python main.py --task world_profile
  python main.py --task world_ident
"""
from __future__ import annotations
import argparse, importlib, os, sys, subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
SRC = REPO_ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

TASKS = {
    'v2_4_9': 'empirical.scripts.run_v2_4_9_quebec_70_74_alpha_sensitivity',
}
SCRIPT_TASKS = {
    'empirical_canada': ['scripts/run_empirical_canada.py'],
    'synthetic_ladder': ['scripts/run_synthetic_tests.py'],
    'world_profile': ['scripts/run_world_panel_profile.py'],
    'world_ident': ['scripts/run_identifiability_world_panel.py', '--top-n', '5'],
    'data_list_indicators': ['scripts/build_panel_dataset.py', '--list-indicators'],
    'data_fisher_rank': ['scripts/build_panel_dataset.py', '--fisher-rank'],
    'data_build_minimal': ['scripts/build_panel_dataset.py', '--budget', 'minimal'],
    'data_build_standard': ['scripts/build_panel_dataset.py', '--budget', 'standard'],
}

def run_task(task: str) -> int:
    if task == 'health':
        import acmf
        print(f'ACMF entrypoint OK: {acmf.__version__}')
        return 0
    if task in SCRIPT_TASKS:
        env = os.environ.copy(); env['PYTHONPATH'] = str(SRC) + os.pathsep + env.get('PYTHONPATH','')
        return subprocess.call([sys.executable] + SCRIPT_TASKS[task], cwd=REPO_ROOT, env=env)
    if task not in TASKS:
        print(f'Unknown task: {task}', file=sys.stderr)
        print('Available tasks: ' + ', '.join(sorted(['health'] + list(TASKS) + list(SCRIPT_TASKS))), file=sys.stderr)
        return 2
    module = importlib.import_module(TASKS[task])
    if not hasattr(module, 'main'):
        print(f'Task module has no main(): {TASKS[task]}', file=sys.stderr)
        return 3
    module.main()
    return 0

def cli() -> int:
    parser=argparse.ArgumentParser(description='ACMF pipeline entrypoint')
    parser.add_argument('--task', default=os.getenv('TASK','health'), help='Task to run')
    args=parser.parse_args(); return run_task(args.task)
if __name__ == '__main__':
    raise SystemExit(cli())

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import os, subprocess, sys

@dataclass(frozen=True)
class TaskSpec:
    name: str
    argv: tuple[str, ...]
    timeout_seconds: int = 300
    stdout_limit: int = 50000

REPO_ROOT = Path(__file__).resolve().parents[2]
TASKS = {
    'empirical_validate_canada': TaskSpec('empirical_validate_canada', ('scripts/run_empirical_validation.py','--mode','country','--country','Canada','--seeds','0','1','--max-nfev','35')),
    'empirical_validate_core5': TaskSpec('empirical_validate_core5', ('scripts/run_empirical_validation.py','--mode','core5','--countries','Canada','Germany','Japan','Australia','Korea, Rep.','--seeds','0','--train-start','2010','--train-end','2015','--validation-start','2016','--validation-end','2020','--max-nfev','25')),
    'empirical_indicator_ablation': TaskSpec('empirical_indicator_ablation', ('scripts/run_empirical_validation.py','--mode','ablation','--country','Canada','--seeds','0','--train-start','2010','--train-end','2015','--validation-start','2016','--validation-end','2020')),
    'empirical_backtest_2008': TaskSpec('empirical_backtest_2008', ('scripts/run_empirical_validation.py','--mode','backtest-2008','--country','Canada','--seeds','0')),
    'synthetic_forecast_benchmark_volatility': TaskSpec('synthetic_forecast_benchmark_volatility', ('scripts/run_synthetic_forecast_benchmark.py','--scenario','high_volatility','--seed','42','--horizon','30')),
    'synthetic_forecast_benchmark_trend': TaskSpec('synthetic_forecast_benchmark_trend', ('scripts/run_synthetic_forecast_benchmark.py','--scenario','low_stress_trend','--seed','42','--horizon','30')),
    'synthetic_forecast_benchmark_regime': TaskSpec('synthetic_forecast_benchmark_regime', ('scripts/run_synthetic_forecast_benchmark.py','--scenario','regime_switch','--seed','42','--horizon','30')),
    'synthetic_forecast_benchmark_nonlinear': TaskSpec('synthetic_forecast_benchmark_nonlinear', ('scripts/run_synthetic_forecast_benchmark.py','--scenario','nonlinear_transform','--seed','42','--horizon','30')),
    'synthetic_forecast_benchmark_response': TaskSpec('synthetic_forecast_benchmark_response', ('scripts/run_synthetic_forecast_benchmark.py','--scenario','all_diagnostics','--mode','response','--seed','42','--horizon','30','--output-dir','artifacts/diagnostics')),
    'dynamics_mechanism_diagnostics': TaskSpec('dynamics_mechanism_diagnostics', ('scripts/run_dynamics_mechanism_diagnostics.py','--steps','120','--dt','0.5','--output-dir','artifacts/diagnostics')),
}

def available_tasks():
    return sorted(['health'] + list(TASKS))

def run_task(task: str) -> int:
    if task == 'health':
        import acmf
        print(f'ACMF entrypoint OK: {acmf.__version__}')
        return 0
    spec = TASKS.get(task)
    if spec is None:
        print('Available tasks:', *available_tasks())
        return 2
    env=os.environ.copy(); env['PYTHONPATH']=str(REPO_ROOT/'src')+os.pathsep+env.get('PYTHONPATH','')
    return subprocess.call([sys.executable]+list(spec.argv), cwd=REPO_ROOT, env=env, timeout=spec.timeout_seconds)

def run_task_captured(task: str) -> dict:
    if task == 'health':
        import acmf
        return {'returncode':0, 'stdout':f'ACMF entrypoint OK: {acmf.__version__}\n', 'stderr':''}
    spec = TASKS.get(task)
    if spec is None:
        return {'returncode':2, 'stdout':'', 'stderr':f'Unknown task: {task}'}
    env=os.environ.copy(); env['PYTHONPATH']=str(REPO_ROOT/'src')+os.pathsep+env.get('PYTHONPATH','')
    proc = subprocess.run([sys.executable]+list(spec.argv), cwd=REPO_ROOT, env=env, capture_output=True, text=True, timeout=spec.timeout_seconds)
    return {'returncode':proc.returncode, 'stdout':proc.stdout[:spec.stdout_limit], 'stderr':proc.stderr[:spec.stdout_limit], 'truncated':len(proc.stdout)>spec.stdout_limit or len(proc.stderr)>spec.stdout_limit}

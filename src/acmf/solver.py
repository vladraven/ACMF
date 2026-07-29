"""Scenario-oriented RK4 solver for ACMF.

This is intended for demos and scenario visualization. It applies projection to the
state domain after each step and is not a replacement for calibration-grade ODE
solvers when exact continuous dynamics are required.
"""
from __future__ import annotations
import numpy as np
from .core import rhs, default_params, ACMFParams


def project_state(x):
    y = np.asarray(x, dtype=float).copy()
    y[:8] = np.clip(y[:8], 0.0, 1.0)
    y[8] = np.clip(y[8], 0.0, 4.0)
    y[9] = max(y[9], 0.0)
    return y


def rk4_step(x, dt, params: ACMFParams | None = None, project: bool = False):
    p = params or default_params()
    x = np.asarray(x, dtype=float)
    k1 = rhs(x, p)
    k2 = rhs(x + 0.5 * dt * k1, p)
    k3 = rhs(x + 0.5 * dt * k2, p)
    k4 = rhs(x + dt * k3, p)
    y = x + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)
    return project_state(y) if project else y


def simulate(x0, t_span, dt: float = 0.1, params: ACMFParams | None = None, project: bool = True):
    p = params or default_params()
    t0, tf = t_span
    times = np.arange(float(t0), float(tf) + dt, dt)
    traj = np.zeros((len(times), 10), dtype=float)
    traj[0] = project_state(x0) if project else np.asarray(x0, dtype=float)
    for i in range(1, len(times)):
        traj[i] = rk4_step(traj[i - 1], dt, p, project=project)
    return times, traj


def scenario_run(scenario_name: str, x0=None, t_span=(0, 100), dt=0.1, **param_overrides):
    p = default_params(**param_overrides)
    if x0 is None:
        x0 = np.array([0.3, 0.4, 0.5, 0.5, 0.5, 0.3, 0.6, 0.5, 2.0, 500.0])
    times, traj = simulate(x0, t_span, dt, p)
    return {"scenario": scenario_name, "times": times, "trajectory": traj, "params": p}

"""Интегратор и визуализация ACMF."""
from __future__ import annotations
import numpy as np
from .core import rhs, default_params, ACMFParams


def rk4_step(x, dt, params: ACMFParams | None = None):
    """Один шаг Рунге-Кутты 4-го порядка."""
    p = params or default_params()
    k1 = rhs(x, p)
    k2 = rhs(x + 0.5 * dt * k1, p)
    k3 = rhs(x + 0.5 * dt * k2, p)
    k4 = rhs(x + dt * k3, p)
    return x + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)


def simulate(x0, t_span, dt: float = 0.1, params: ACMFParams | None = None):
    """Интегрирование ACMF методом RK4."""
    p = params or default_params()
    t0, tf = t_span
    times = np.arange(t0, tf + dt, dt)
    n_steps = len(times)
    traj = np.zeros((n_steps, 10), dtype=float)
    traj[0] = np.asarray(x0, dtype=float)
    for i in range(1, n_steps):
        traj[i] = rk4_step(traj[i - 1], dt, p)
        # Жесткая проекция на инвариантное множество
        traj[i, :8] = np.clip(traj[i, :8], 0.0, 1.0)
        traj[i, 8] = np.clip(traj[i, 8], 0.0, 4.0)
        traj[i, 9] = max(traj[i, 9], 0.0)
    return times, traj


def scenario_run(scenario_name: str, x0=None, t_span=(0, 100), dt=0.1, **param_overrides):
    """Запуск сценария с переопределением параметров."""
    p = default_params(**param_overrides)
    if x0 is None:
        x0 = np.array([0.3, 0.4, 0.5, 0.5, 0.5, 0.3, 0.6, 0.5, 2.0, 500.0])
    times, traj = simulate(x0, t_span, dt, p)
    return {"scenario": scenario_name, "times": times, "trajectory": traj, "params": p}

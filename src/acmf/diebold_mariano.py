"""Diebold-Mariano predictive-accuracy test utilities."""
from __future__ import annotations
from typing import Callable
import numpy as np
from scipy.stats import t as t_dist


def dm_test(actual: np.ndarray, forecast1: np.ndarray, forecast2: np.ndarray,
            loss_fn: Callable | None = None, h: int = 1, one_sided: bool = False) -> dict:
    """Compare two forecasts with the Diebold-Mariano test.

    The loss differential is d_t = L(e1_t) - L(e2_t). Negative mean favors
    forecast1; positive mean favors forecast2.
    """
    actual = np.asarray(actual, dtype=float)
    f1 = np.asarray(forecast1, dtype=float)
    f2 = np.asarray(forecast2, dtype=float)
    if actual.shape != f1.shape or actual.shape != f2.shape:
        raise ValueError("actual, forecast1, and forecast2 must have identical shape")
    if loss_fn is None:
        loss_fn = lambda a, f: (a - f) ** 2
    d = np.asarray(loss_fn(actual, f1), dtype=float) - np.asarray(loss_fn(actual, f2), dtype=float)
    n = len(d)
    if n < 2:
        return {"DM_stat": np.nan, "p_value": 1.0, "better_model": "insufficient_data", "loss_diff_mean": 0.0, "stderr": np.nan, "n": n}
    d_bar = float(np.mean(d))
    gamma0 = float(np.var(d, ddof=1))
    if h > 1 and n > h:
        autocov = 0.0
        for k in range(1, h):
            if k < n:
                autocov += 2.0 * (1.0 - k / h) * np.cov(d[:-k], d[k:])[0, 1]
        var_d = (gamma0 + autocov) / n
    else:
        var_d = gamma0 / n
    stderr = float(np.sqrt(max(var_d, 1e-300)))
    dm_stat = float(d_bar / stderr)
    df = max(n - 1, 1)
    if one_sided:
        # H1: model 1 has larger loss than model 2.
        p_value = float(1.0 - t_dist.cdf(dm_stat, df=df))
    else:
        p_value = float(2.0 * (1.0 - t_dist.cdf(abs(dm_stat), df=df)))
    better = "Model1" if d_bar < 0 else "Model2"
    if abs(dm_stat) < 1.96:
        better = "No significant difference"
    return {"DM_stat": dm_stat, "p_value": p_value, "better_model": better, "loss_diff_mean": d_bar, "stderr": stderr, "n": n}


def compare_acmf_vs_benchmarks(actual: np.ndarray, acmf_forecast: np.ndarray, benchmark_forecasts: dict, h: int = 1) -> dict:
    """Compare one ACMF forecast with each benchmark forecast."""
    return {name: dm_test(actual, acmf_forecast, forecast, h=h) for name, forecast in benchmark_forecasts.items()}

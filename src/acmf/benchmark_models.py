"""ACMF Phase II benchmark econometric forecast models.

Benchmarks:
- Persistence / Random Walk: Y(t+1) = Y(t)
- Linear Trend: Y(t) = a + b*t
- ARIMA(1,1,0): dY(t) = c + phi*dY(t-1) + eps
- VAR(1): dY(t) = c + Phi*dY(t-1) + eps
"""
from __future__ import annotations

from typing import Dict, Tuple
import numpy as np


def _as_1d(y, name: str = "array"):
    arr = np.asarray(y, dtype=float)
    if arr.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional")
    if len(arr) == 0:
        raise ValueError(f"{name} must not be empty")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} contains non-finite values")
    return arr


def random_walk_forecast(y_train: np.ndarray, n_steps: int) -> np.ndarray:
    """Persistence forecast: repeat the last observed value."""
    y = _as_1d(y_train, "y_train")
    if n_steps < 0:
        raise ValueError("n_steps must be non-negative")
    return np.full(int(n_steps), y[-1], dtype=float)


def linear_trend_fit(y_train: np.ndarray, t_train: np.ndarray) -> Tuple[float, float]:
    """Fit Y = a + b*t by OLS and return (a, b)."""
    y = _as_1d(y_train, "y_train")
    t = _as_1d(t_train, "t_train")
    if len(t) != len(y):
        raise ValueError("t_train and y_train must have equal length")
    X = np.column_stack([np.ones(len(t)), t])
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    return float(coef[0]), float(coef[1])


def linear_trend_forecast(a: float, b: float, t_forecast: np.ndarray) -> np.ndarray:
    """Forecast by fitted linear trend."""
    return float(a) + float(b) * np.asarray(t_forecast, dtype=float)


def arima_110_fit(y_train: np.ndarray, t_train: np.ndarray | None = None) -> Tuple[float, float, float]:
    """Fit ARIMA(1,1,0) as AR(1) on first differences.

    Returns (c, phi, sigma2) for dY(t) = c + phi*dY(t-1) + eps.
    """
    y = _as_1d(y_train, "y_train")
    dy = np.diff(y)
    n = len(dy)
    if n == 0:
        return 0.0, 0.0, 1.0
    if n < 3:
        return float(np.mean(dy)), 0.0, float(np.var(dy) if n > 1 else 1.0)
    X = np.column_stack([np.ones(n - 1), dy[:-1]])
    coef, *_ = np.linalg.lstsq(X, dy[1:], rcond=None)
    c, phi = float(coef[0]), float(coef[1])
    resid = dy[1:] - (c + phi * dy[:-1])
    sigma2 = float(np.var(resid)) if len(resid) > 0 else 1.0
    return c, phi, sigma2


def arima_110_forecast(y_train: np.ndarray, c: float, phi: float, n_steps: int) -> np.ndarray:
    """Forecast ARIMA(1,1,0)."""
    y = _as_1d(y_train, "y_train")
    if n_steps < 0:
        raise ValueError("n_steps must be non-negative")
    dy = np.diff(y)
    current_dy = float(dy[-1]) if len(dy) > 0 else 0.0
    current_y = float(y[-1])
    forecast = np.zeros(int(n_steps), dtype=float)
    for i in range(int(n_steps)):
        current_dy = float(c) + float(phi) * current_dy
        current_y += current_dy
        forecast[i] = current_y
    return forecast


def var1_fit(data_train: Dict[str, np.ndarray], t_train: np.ndarray | None = None) -> Dict:
    """Fit VAR(1) on first differences for a dictionary of series."""
    if not data_train:
        raise ValueError("data_train must contain at least one variable")
    var_names = sorted(data_train.keys())
    y_mat = np.column_stack([_as_1d(data_train[v], v) for v in var_names])
    if len({len(data_train[v]) for v in var_names}) != 1:
        raise ValueError("all variables must have equal length")
    dy = np.diff(y_mat, axis=0)
    n, k = dy.shape
    if n < 3:
        return {"c": np.zeros(k), "Phi": np.eye(k) * 0.1, "sigma": np.eye(k), "names": var_names}
    X = np.column_stack([np.ones(n - 1), dy[:-1]])
    coef = np.zeros((k, k + 1), dtype=float)
    for i in range(k):
        coef[i], *_ = np.linalg.lstsq(X, dy[1:, i], rcond=None)
    c = coef[:, 0]
    Phi = coef[:, 1:]
    resid = dy[1:] - (c + dy[:-1] @ Phi.T)
    sigma = np.cov(resid.T) if resid.shape[0] > 1 else np.eye(k)
    sigma = np.atleast_2d(sigma)
    if sigma.shape != (k, k):
        sigma = np.eye(k) * float(np.squeeze(sigma))
    return {"c": c, "Phi": Phi, "sigma": sigma, "names": var_names}


def var1_forecast(data_train: Dict[str, np.ndarray], var_params: Dict, n_steps: int) -> Dict[str, np.ndarray]:
    """Forecast all variables with fitted VAR(1)."""
    if n_steps < 0:
        raise ValueError("n_steps must be non-negative")
    var_names = list(var_params["names"])
    c = np.asarray(var_params["c"], dtype=float)
    Phi = np.asarray(var_params["Phi"], dtype=float)
    y_mat = np.column_stack([_as_1d(data_train[v], v) for v in var_names])
    dy = np.diff(y_mat, axis=0)
    current_dy = dy[-1].copy() if len(dy) > 0 else np.zeros(len(var_names), dtype=float)
    current_y = y_mat[-1].copy()
    forecasts = {v: np.zeros(int(n_steps), dtype=float) for v in var_names}
    for i in range(int(n_steps)):
        current_dy = c + Phi @ current_dy
        current_y = current_y + current_dy
        for j, v in enumerate(var_names):
            forecasts[v][i] = current_y[j]
    return forecasts


def fit_all_benchmarks(data_train: Dict[str, np.ndarray], t_train: np.ndarray) -> Dict:
    """Fit all benchmark models. The first insertion-order variable is the target."""
    if not data_train:
        raise ValueError("data_train must contain at least one variable")
    target_var = next(iter(data_train.keys()))
    y = _as_1d(data_train[target_var], target_var)
    a, b = linear_trend_fit(y, t_train)
    c_ar, phi_ar, sigma2_ar = arima_110_fit(y, t_train)
    var_params = var1_fit(data_train, t_train)
    return {
        "target_var": target_var,
        "linear_trend": {"a": a, "b": b},
        "arima_110": {"c": c_ar, "phi": phi_ar, "sigma2": sigma2_ar},
        "var1": var_params,
    }


def forecast_all_benchmarks(data_train: Dict[str, np.ndarray], t_train: np.ndarray,
                            t_forecast: np.ndarray, fitted: Dict) -> Dict[str, np.ndarray]:
    """Forecast the target variable with all benchmark models."""
    target = fitted["target_var"]
    y = _as_1d(data_train[target], target)
    n_steps = len(t_forecast)
    rw = random_walk_forecast(y, n_steps)
    lt = linear_trend_forecast(fitted["linear_trend"]["a"], fitted["linear_trend"]["b"], t_forecast)
    ar = arima_110_forecast(y, fitted["arima_110"]["c"], fitted["arima_110"]["phi"], n_steps)
    var_f = var1_forecast(data_train, fitted["var1"], n_steps)
    return {"RandomWalk": rw, "LinearTrend": lt, "ARIMA(1,1,0)": ar, f"VAR(1)_{target}": var_f.get(target, rw)}

"""ACMF Phase II calibration pipeline.

This module is intentionally lightweight: it implements a practical DE -> L-BFGS-B
-> adaptive random-walk MCMC pipeline for observed ACMF variables. It is a model-
calibration scaffold, not a claim of completed empirical validation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List
import warnings

import numpy as np
from scipy.interpolate import interp1d
from scipy.optimize import differential_evolution, minimize

from .core import ACMFParams, default_params, rhs


def huber_loss(residual, delta: float = 1.0) -> float:
    r = np.asarray(residual, dtype=float)
    abs_r = np.abs(r)
    loss = np.where(abs_r <= delta, 0.5 * r**2, delta * (abs_r - 0.5 * delta))
    return float(np.mean(loss))


def compute_derivative(y, t):
    y = np.asarray(y, dtype=float)
    t = np.asarray(t, dtype=float)
    if y.ndim != 1 or t.ndim != 1 or len(y) != len(t):
        raise ValueError("y and t must be one-dimensional arrays of equal length")
    if len(y) < 2:
        return np.zeros_like(y)
    dydt = np.zeros_like(y, dtype=float)
    dydt[0] = (y[1] - y[0]) / (t[1] - t[0])
    dydt[-1] = (y[-1] - y[-2]) / (t[-1] - t[-2])
    for i in range(1, len(y) - 1):
        dydt[i] = (y[i + 1] - y[i - 1]) / (t[i + 1] - t[i - 1])
    return dydt


@dataclass
class LossConfig:
    observed_vars: List[str] = field(default_factory=lambda: ["P", "Prod", "A", "Inst", "F"])
    lambda_deriv: float = 0.5
    delta_huber: float = 1.0
    var_index: Dict[str, int] = field(default_factory=lambda: {
        "A": 0, "Prod": 1, "Ch": 2, "M": 3, "G": 4,
        "V": 5, "Inst": 6, "R": 7, "F": 8, "P": 9,
    })


class ACMFObjective:
    """Objective function for a compact ACMF calibration subset."""

    THETA_NAMES = [
        "alpha7", "K_g", "beta_neg", "NaturalDecay",
        "q1", "q3", "alpha1", "b1", "Ch0", "M0", "G0", "R0",
    ]
    BOUNDS = [
        (0.05, 2.0), (0.1, 0.9), (0.05, 0.5), (0.01, 0.20),
        (0.0, 1.0), (0.0, 1.0), (0.05, 1.0), (0.0, 0.1),
        (0.0, 1.0), (0.0, 1.0), (0.0, 1.0), (0.0, 1.0),
    ]

    def __init__(self, data, config: LossConfig | None = None):
        self.t = np.asarray(data["t"], dtype=float)
        if self.t.ndim != 1 or len(self.t) < 2:
            raise ValueError("data['t'] must contain at least two time points")
        self.data = {k: np.asarray(v, dtype=float) for k, v in data.items() if k != "t"}
        self.config = config or LossConfig()
        self.var_scale = {}
        for var in self.config.observed_vars:
            if var in self.data:
                std = float(np.std(self.data[var]))
                self.var_scale[var] = std if std > 1e-12 else 1.0

    def _theta_to_params(self, theta) -> ACMFParams:
        theta = np.asarray(theta, dtype=float)
        p = default_params()
        p.alpha7, p.K_g, p.beta_neg, p.NaturalDecay = theta[0], theta[1], theta[2], theta[3]
        p.q1, p.q3, p.alpha1, p.b1 = theta[4], theta[5], theta[6], theta[7]
        return p

    def _initial_state(self, theta):
        theta = np.asarray(theta, dtype=float)
        A0 = self.data.get("A", np.array([0.3]))[0]
        Prod0 = self.data.get("Prod", np.array([0.4]))[0]
        Inst0 = self.data.get("Inst", np.array([0.6]))[0]
        F0 = self.data.get("F", np.array([2.0]))[0]
        P0 = self.data.get("P", np.array([500.0]))[0]
        return np.array([A0, Prod0, theta[8], theta[9], theta[10], 0.3, Inst0, theta[11], F0, P0], dtype=float)

    @staticmethod
    def _project_state(x):
        y = np.asarray(x, dtype=float).copy()
        y[:8] = np.clip(y[:8], 0.0, 1.0)
        y[8] = np.clip(y[8], 0.0, 4.0)
        y[9] = max(y[9], 0.0)
        return y

    def _integrate(self, theta):
        p = self._theta_to_params(theta)
        x0 = self._project_state(self._initial_state(theta))
        t0, tf = float(self.t[0]), float(self.t[-1])
        if tf <= t0:
            raise ValueError("observation times must be increasing")
        dt = min(0.5, (tf - t0) / max(len(self.t) * 2, 10))
        n_steps = int(np.ceil((tf - t0) / dt)) + 1
        t_sim = np.linspace(t0, tf, n_steps)
        traj = np.zeros((n_steps, 10), dtype=float)
        traj[0] = x0
        for i in range(1, n_steps):
            h = t_sim[i] - t_sim[i - 1]
            x = traj[i - 1]
            k1 = rhs(x, p)
            k2 = rhs(x + 0.5 * h * k1, p)
            k3 = rhs(x + 0.5 * h * k2, p)
            k4 = rhs(x + h * k3, p)
            traj[i] = self._project_state(x + (h / 6.0) * (k1 + 2*k2 + 2*k3 + k4))
        traj_interp = np.zeros((len(self.t), 10), dtype=float)
        for j in range(10):
            traj_interp[:, j] = interp1d(t_sim, traj[:, j], kind="linear", fill_value="extrapolate")(self.t)
        return traj_interp

    def __call__(self, theta):
        try:
            traj = self._integrate(theta)
        except Exception:
            return 1e10
        if not np.all(np.isfinite(traj)):
            return 1e10
        loss_total = 0.0
        n_vars = 0
        for var in self.config.observed_vars:
            if var not in self.data:
                continue
            idx = self.config.var_index[var]
            y_obs = self.data[var]
            y_sim = traj[:, idx]
            scale = self.var_scale.get(var, 1.0)
            loss_levels = huber_loss((y_obs - y_sim) / scale, self.config.delta_huber)
            dy_obs = compute_derivative(y_obs, self.t)
            dy_sim = compute_derivative(y_sim, self.t)
            loss_derivs = huber_loss((dy_obs - dy_sim) / scale, self.config.delta_huber)
            loss_total += loss_levels + self.config.lambda_deriv * loss_derivs
            n_vars += 1
        return float(loss_total / max(n_vars, 1))


@dataclass
class CalibrationResult:
    theta_opt: np.ndarray
    loss_opt: float
    hessian_inv: np.ndarray | None = None
    cov_matrix: np.ndarray | None = None
    corr_matrix: np.ndarray | None = None
    mcmc_samples: np.ndarray | None = None
    mcmc_acceptance_rate: float = 0.0
    diagnostics: Dict | None = None


def differential_evolution_fit(objective, bounds=None, maxiter=200, popsize=15, workers=1, seed=42, tol=1e-6):
    bounds = bounds or objective.BOUNDS
    result = differential_evolution(
        func=objective,
        bounds=bounds,
        maxiter=maxiter,
        popsize=popsize,
        workers=workers,
        seed=seed,
        tol=tol,
        polish=False,
        disp=False,
    )
    return result.x, float(result.fun)


def lbfgsb_refinement(objective, x0, bounds=None, maxiter=1000):
    bounds = bounds or objective.BOUNDS
    result = minimize(fun=objective, x0=x0, method="L-BFGS-B", bounds=bounds, options={"maxiter": maxiter})
    hess_inv = None
    if hasattr(result, "hess_inv") and result.hess_inv is not None:
        try:
            hess_inv = np.array(result.hess_inv.todense())
        except Exception:
            hess_inv = None
    return result.x, float(result.fun), hess_inv


def estimate_covariance(hess_inv, objective=None):
    if hess_inv is None:
        return None, None
    cov = np.asarray(hess_inv, dtype=float)
    d = np.sqrt(np.maximum(np.diag(cov), 0.0))
    with np.errstate(divide="ignore", invalid="ignore"):
        corr = cov / np.outer(d, d)
    corr = np.nan_to_num(corr, nan=0.0, posinf=0.0, neginf=0.0)
    if corr.size:
        tri = corr[np.triu_indices_from(corr, k=1)]
        if tri.size:
            max_corr = float(np.max(np.abs(tri)))
            if max_corr > 0.85:
                warnings.warn(f"Multicollinearity detected: max|R|={max_corr:.3f}")
    return cov, corr


def dram_mcmc(objective, theta_map, cov_proposal=None, n_samples=10000, burn_in=2000,
              adapt_interval=100, target_acceptance=0.25, seed=42):
    rng = np.random.default_rng(seed)
    theta_map = np.asarray(theta_map, dtype=float)
    n_params = len(theta_map)
    if cov_proposal is None:
        cov_proposal = np.eye(n_params) * 1e-4
    cov_proposal = np.asarray(cov_proposal, dtype=float)
    samples = np.zeros((n_samples, n_params), dtype=float)
    current = theta_map.copy()
    current_energy = 0.5 * objective(current)**2
    n_accepted = 0
    log_scale = 0.0
    for i in range(n_samples):
        if i > 0 and i % adapt_interval == 0:
            recent = n_accepted / i
            log_scale += 0.1 if recent > target_acceptance else -0.1
            log_scale = float(np.clip(log_scale, -5.0, 2.0))
        proposal = current + rng.multivariate_normal(np.zeros(n_params), cov_proposal * np.exp(log_scale))
        for j, (lo, hi) in enumerate(objective.BOUNDS):
            if proposal[j] < lo:
                proposal[j] = lo + (lo - proposal[j])
            if proposal[j] > hi:
                proposal[j] = hi - (proposal[j] - hi)
            proposal[j] = np.clip(proposal[j], lo, hi)
        proposal_loss = objective(proposal)
        if proposal_loss >= 1e9:
            samples[i] = current
            continue
        proposal_energy = 0.5 * proposal_loss**2
        delta = proposal_energy - current_energy
        if delta < 0 or rng.random() < np.exp(-delta):
            current = proposal.copy()
            current_energy = proposal_energy
            n_accepted += 1
        samples[i] = current
    acc_rate = n_accepted / max(n_samples, 1)
    return samples[burn_in:], float(acc_rate)


def model_adequacy(objective, theta):
    traj = objective._integrate(theta)
    metrics = {}
    n_total = 0
    k = len(theta)
    for var in objective.config.observed_vars:
        if var not in objective.data:
            continue
        idx = objective.config.var_index[var]
        y_obs = objective.data[var]
        y_sim = traj[:, idx]
        n = len(y_obs)
        n_total += n
        rmse = float(np.sqrt(np.mean((y_obs - y_sim)**2)))
        mae = float(np.mean(np.abs(y_obs - y_sim)))
        ss_res = float(np.sum((y_obs - y_sim)**2))
        ss_tot = float(np.sum((y_obs - np.mean(y_obs))**2))
        r2 = 1.0 - ss_res / ss_tot if ss_tot > 1e-12 else 0.0
        metrics[var] = {"RMSE": rmse, "MAE": mae, "R2": float(r2)}
    total_sse = sum(metrics[v]["RMSE"]**2 * len(objective.data[v]) for v in metrics)
    if n_total > 0 and total_sse > 0:
        aic = n_total * np.log(total_sse / n_total) + 2 * k
        bic = n_total * np.log(total_sse / n_total) + k * np.log(n_total)
    else:
        aic = bic = float("nan")
    metrics["_overall"] = {"AIC": float(aic), "BIC": float(bic), "n_params": k, "n_obs": n_total}
    return metrics


def run_calibration_pipeline(data, config=None, de_maxiter=200, mcmc_samples=10000,
                             mcmc_burn_in=2000, seed=42):
    objective = ACMFObjective(data, config)
    theta_de, _ = differential_evolution_fit(objective, maxiter=de_maxiter, seed=seed)
    theta_map, loss_map, hess_inv = lbfgsb_refinement(objective, theta_de)
    cov, corr = estimate_covariance(hess_inv, objective)
    samples, acc_rate = dram_mcmc(
        objective,
        theta_map,
        cov_proposal=cov if cov is not None else None,
        n_samples=mcmc_samples,
        burn_in=mcmc_burn_in,
        seed=seed,
    )
    diag = model_adequacy(objective, theta_map)
    return CalibrationResult(theta_map, loss_map, hess_inv, cov, corr, samples, acc_rate, diag)

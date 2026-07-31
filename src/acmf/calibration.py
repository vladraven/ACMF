from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from scipy.optimize import least_squares
from .core import default_params
from .config import load_parameter_config
from .solver import simulate
from .world_panel import STATE_INDEX, state_from_proxy

CALIBRATION_PARAMS = ['alpha7','K_g','beta_neg','NaturalDecay','q1','q3','alpha1','b1']
_CFG = load_parameter_config('baseline')
DEFAULT_THETA = np.array([float(_CFG.parameters[p]) for p in CALIBRATION_PARAMS], dtype=float)
LOWER = np.array([float(_CFG.bounds[p][0]) for p in CALIBRATION_PARAMS], dtype=float)
UPPER = np.array([float(_CFG.bounds[p][1]) for p in CALIBRATION_PARAMS], dtype=float)

@dataclass
class CalibrationResult:
    country: str
    theta: np.ndarray
    parameter_names: list[str]
    converged: bool
    loss_initial: float
    loss_final: float
    nfev: int
    message: str
    bounds_hit: list[str]
    predicted: dict

def params_from_theta(theta):
    return default_params(**dict(zip(CALIBRATION_PARAMS, map(float, theta))))

def predict_from_theta(data: dict, theta, start_idx=0, steps: int|None=None) -> dict:
    x0 = state_from_proxy(data, start_idx)
    t0 = int(data['t'][start_idx]); n = steps if steps is not None else (len(data['t'])-start_idx)
    tf = t0 + n - 1
    times, traj = simulate(x0, (t0, tf), 1.0, params_from_theta(theta))
    out={'t': times.astype(int)}
    traj = np.nan_to_num(traj, nan=0.0, posinf=1e6, neginf=-1e6)
    for v, idx in STATE_INDEX.items(): out[v]=traj[:, idx]
    return out

def residuals(theta, data, variables):
    pred = predict_from_theta(data, theta)
    res=[]
    n=min(len(pred['t']), len(data['t']))
    for v in variables:
        scale = np.nanstd(data[v][:n]) or 1.0
        r=(pred[v][:n]-data[v][:n]) / scale
        res.append(np.nan_to_num(r, nan=1e6, posinf=1e6, neginf=-1e6))
    return np.concatenate(res)

def calibrate_country_proxy(country: str, data: dict, variables=None, seed: int=0, max_nfev: int=80) -> CalibrationResult:
    variables = list(variables or ['P','Prod','A','Inst','F'])
    rng=np.random.default_rng(seed)
    theta0=np.clip(DEFAULT_THETA*(1.0+rng.normal(0,0.15,len(DEFAULT_THETA))), LOWER, UPPER)
    loss_initial=float(0.5*np.sum(residuals(theta0,data,variables)**2))
    fit=least_squares(lambda th: residuals(th,data,variables), theta0, bounds=(LOWER,UPPER), max_nfev=max_nfev, xtol=1e-6, ftol=1e-6)
    pred=predict_from_theta(data, fit.x)
    hits=[n for n,x,l,u in zip(CALIBRATION_PARAMS,fit.x,LOWER,UPPER) if abs(x-l)<1e-5 or abs(x-u)<1e-5]
    return CalibrationResult(country, fit.x, CALIBRATION_PARAMS.copy(), bool(fit.success), loss_initial, float(fit.cost), int(fit.nfev), str(fit.message), hits, pred)

# --- Legacy sensitivity/identifiability support (restored) ---
# Provides LossConfig/ACMFObjective used by identifiability.py, observation_designer.py
# and real_identifiability.py. Kept separate from the newer solver-based
# calibrate_country_proxy() pipeline above, which empirical_validation.py depends on.
from dataclasses import field as _field
from typing import Dict as _Dict, List as _List
import warnings as _warnings
from scipy.interpolate import interp1d as _interp1d
from .core import rhs as _rhs


def huber_loss(residual, delta=1.0):
    r = np.asarray(residual, dtype=float)
    a = np.abs(r)
    return float(np.mean(np.where(a <= delta, 0.5 * r * r, delta * (a - 0.5 * delta))))


def compute_derivative(y, t):
    y = np.asarray(y, dtype=float)
    t = np.asarray(t, dtype=float)
    if len(y) < 2:
        return np.zeros_like(y)
    d = np.zeros_like(y)
    d[0] = (y[1] - y[0]) / (t[1] - t[0])
    d[-1] = (y[-1] - y[-2]) / (t[-1] - t[-2])
    for i in range(1, len(y) - 1):
        d[i] = (y[i + 1] - y[i - 1]) / (t[i + 1] - t[i - 1])
    return d


@dataclass(frozen=True)
class PriorSpec:
    kind: str = 'uniform'
    mu: float = 0.0
    sigma: float = 1.0
    a: float = 2.0
    b: float = 2.0
    weight: float = 1.0

    def penalty(self, value, lower=None, upper=None):
        x = float(value)
        k = self.kind.lower()
        if k == 'uniform':
            return 0.0
        if self.sigma <= 0:
            raise ValueError('sigma must be positive')
        if k == 'normal':
            return float(self.weight * 0.5 * ((x - self.mu) / self.sigma) ** 2)
        if k == 'lognormal':
            if x <= 0:
                return 1e12
            z = (np.log(x) - self.mu) / self.sigma
            return float(self.weight * 0.5 * z * z)
        if k == 'beta':
            if lower is None or upper is None or upper <= lower:
                return 1e12
            u = float(np.clip((x - lower) / (upper - lower), 1e-12, 1 - 1e-12))
            return float(self.weight * (-(self.a - 1) * np.log(u) - (self.b - 1) * np.log(1 - u)))
        raise ValueError(f'Unsupported prior kind: {self.kind}')


def default_prior_specs(theta_names=None):
    priors = {
        'alpha7': PriorSpec('lognormal', mu=np.log(0.5), sigma=0.8, weight=0.2),
        'K_g': PriorSpec('lognormal', mu=np.log(0.4), sigma=0.6, weight=0.2),
        'beta_neg': PriorSpec('lognormal', mu=np.log(0.2), sigma=0.6, weight=0.2),
        'NaturalDecay': PriorSpec('lognormal', mu=np.log(0.04), sigma=0.7, weight=0.2),
        'q1': PriorSpec('beta', a=2, b=2, weight=0.05),
        'q3': PriorSpec('beta', a=2, b=2, weight=0.05),
        'alpha1': PriorSpec('lognormal', mu=np.log(0.4), sigma=0.8, weight=0.2),
        'b1': PriorSpec('lognormal', mu=np.log(0.04), sigma=0.8, weight=0.2),
        'Ch0': PriorSpec('beta', a=2, b=2, weight=0.05),
        'M0': PriorSpec('beta', a=2, b=2, weight=0.05),
        'G0': PriorSpec('beta', a=2, b=2, weight=0.05),
        'R0': PriorSpec('beta', a=2, b=2, weight=0.05),
    }
    return {k: v for k, v in priors.items() if theta_names is None or k in theta_names}


@dataclass
class LossConfig:
    observed_vars: _List[str] = _field(default_factory=lambda: ['P', 'Prod', 'A', 'Inst', 'F'])
    lambda_deriv: float = 0.5
    delta_huber: float = 1.0
    lambda_prior: float = 0.01
    priors: _Dict[str, PriorSpec] = _field(default_factory=dict)
    var_index: _Dict[str, int] = _field(default_factory=lambda: {'A': 0, 'Prod': 1, 'Ch': 2, 'M': 3, 'G': 4, 'V': 5, 'Inst': 6, 'R': 7, 'F': 8, 'P': 9})


class ACMFObjective:
    THETA_NAMES = ['alpha7', 'K_g', 'beta_neg', 'NaturalDecay', 'q1', 'q3', 'alpha1', 'b1', 'Ch0', 'M0', 'G0', 'R0']
    BOUNDS = [(0.05, 2.0), (0.1, 0.9), (0.05, 0.5), (0.01, 0.20), (0, 1), (0, 1), (0.05, 1.0), (0, 0.1), (0, 1), (0, 1), (0, 1), (0, 1)]

    def __init__(self, data, config=None):
        self.t = np.asarray(data['t'], dtype=float)
        self.data = {k: np.asarray(v, dtype=float) for k, v in data.items() if k != 't'}
        self.config = config or LossConfig()
        if not self.config.priors:
            self.config.priors = default_prior_specs(self.THETA_NAMES)
        self.var_scale = {v: (float(np.std(self.data[v])) if v in self.data and np.std(self.data[v]) > 1e-12 else 1.0) for v in self.config.observed_vars}

    def _theta_to_params(self, theta):
        p = default_params()
        p.alpha7, p.K_g, p.beta_neg, p.NaturalDecay = theta[0], theta[1], theta[2], theta[3]
        p.q1, p.q3, p.alpha1, p.b1 = theta[4], theta[5], theta[6], theta[7]
        return p

    def _initial_state(self, theta):
        return np.array([
            self.data.get('A', [0.3])[0], self.data.get('Prod', [0.4])[0], theta[8], theta[9], theta[10], 0.3,
            self.data.get('Inst', [0.6])[0], theta[11], self.data.get('F', [2.0])[0], self.data.get('P', [500.0])[0],
        ], dtype=float)

    @staticmethod
    def _project(x):
        y = np.asarray(x, dtype=float).copy()
        y[:8] = np.clip(y[:8], 0, 1)
        y[8] = np.clip(y[8], 0, 4)
        y[9] = max(y[9], 0.0)
        return y

    def _integrate(self, theta):
        p = self._theta_to_params(theta)
        x0 = self._project(self._initial_state(theta))
        t0, tf = float(self.t[0]), float(self.t[-1])
        dt = min(0.5, (tf - t0) / max(len(self.t) * 2, 10))
        n = int(np.ceil((tf - t0) / dt)) + 1
        tt = np.linspace(t0, tf, n)
        tr = np.zeros((n, 10))
        tr[0] = x0
        for i in range(1, n):
            h = tt[i] - tt[i - 1]
            x = tr[i - 1]
            k1 = _rhs(x, p)
            k2 = _rhs(x + 0.5 * h * k1, p)
            k3 = _rhs(x + 0.5 * h * k2, p)
            k4 = _rhs(x + h * k3, p)
            tr[i] = self._project(x + (h / 6) * (k1 + 2 * k2 + 2 * k3 + k4))
        out = np.zeros((len(self.t), 10))
        for j in range(10):
            out[:, j] = _interp1d(tt, tr[:, j], kind='linear', fill_value='extrapolate')(self.t)
        return out

    def prior_penalty(self, theta):
        return float(sum(self.config.priors[n].penalty(theta[i], *self.BOUNDS[i]) for i, n in enumerate(self.THETA_NAMES) if n in self.config.priors))

    def __call__(self, theta):
        theta = np.asarray(theta, dtype=float)
        try:
            tr = self._integrate(theta)
        except Exception:
            return 1e10
        if not np.all(np.isfinite(tr)):
            return 1e10
        loss = 0.0
        n = 0
        for v in self.config.observed_vars:
            if v not in self.data:
                continue
            idx = self.config.var_index[v]
            scale = self.var_scale.get(v, 1.0)
            y = self.data[v]
            s = tr[:, idx]
            loss += huber_loss((y - s) / scale, self.config.delta_huber) + self.config.lambda_deriv * huber_loss((compute_derivative(y, self.t) - compute_derivative(s, self.t)) / scale, self.config.delta_huber)
            n += 1
        return float(loss / max(n, 1) + self.config.lambda_prior * self.prior_penalty(theta))

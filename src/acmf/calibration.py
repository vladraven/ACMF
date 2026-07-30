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

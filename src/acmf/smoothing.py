"""Numerically hardened smoothing operators for ACMF."""
import numpy as np

EPSILON = 1e-9
_MAX_ABS = 1e150

def _finite_array(x):
    return np.nan_to_num(np.asarray(x, dtype=float), nan=0.0, posinf=_MAX_ABS, neginf=-_MAX_ABS)

def smax(x, y, epsilon=EPSILON):
    x = _finite_array(x); y = _finite_array(y)
    d = np.clip(x - y, -_MAX_ABS, _MAX_ABS)
    return 0.5 * (x + y + np.sqrt(d * d + epsilon))

def smin(x, y, epsilon=EPSILON):
    x = _finite_array(x); y = _finite_array(y)
    d = np.clip(x - y, -_MAX_ABS, _MAX_ABS)
    return 0.5 * (x + y - np.sqrt(d * d + epsilon))

def sigmoid(z):
    z = np.clip(_finite_array(z), -700.0, 700.0)
    out = np.empty_like(z, dtype=float)
    pos = z >= 0
    out[pos] = 1.0 / (1.0 + np.exp(-z[pos]))
    ez = np.exp(z[~pos])
    out[~pos] = ez / (1.0 + ez)
    return float(out) if out.ndim == 0 else out

def dsmax_dx(x, y, epsilon=EPSILON):
    x = _finite_array(x); y = _finite_array(y); d=np.clip(x-y, -_MAX_ABS, _MAX_ABS)
    return 0.5 * (1.0 + d / np.sqrt(d*d + epsilon))

def dsmax_dy(x, y, epsilon=EPSILON):
    x = _finite_array(x); y = _finite_array(y); d=np.clip(x-y, -_MAX_ABS, _MAX_ABS)
    return 0.5 * (1.0 - d / np.sqrt(d*d + epsilon))

def dsmin_dx(x, y, epsilon=EPSILON):
    return dsmax_dy(x, y, epsilon)

def dsmin_dy(x, y, epsilon=EPSILON):
    return dsmax_dx(x, y, epsilon)

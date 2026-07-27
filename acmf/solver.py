from __future__ import annotations
import numpy as np
from scipy.integrate import solve_ivp
from acmf_core import rhs_acmf

def solve_acmf(y0, t_span, p, Distance, *, method="Radau", rtol=1e-6, atol=1e-8, max_step=1.0):
    return solve_ivp(lambda t, y: rhs_acmf(t, y, p, Distance), t_span, np.asarray(y0, dtype=float).reshape(-1), method=method, rtol=rtol, atol=atol, max_step=max_step)

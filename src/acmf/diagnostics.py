"""Diagnostics for ACMF: Jacobian, signs, spectrum, decoupling, invariance."""
from __future__ import annotations
import numpy as np
from .core import rhs, default_params, ACMFParams

STATE_NAMES = ["A", "Prod", "Ch", "M", "G", "V", "Inst", "R", "F", "P"]


def _step_for(value: float, h_abs: float = 1e-6, h_rel: float = 1e-6) -> float:
    return max(h_abs, h_rel * max(1.0, abs(float(value))))


def numerical_jacobian(x, params: ACMFParams | None = None, h: float | None = None):
    """Central finite-difference Jacobian of rhs at x."""
    p = params or default_params()
    x = np.asarray(x, dtype=float)
    n = len(x)
    J = np.zeros((n, n), dtype=float)
    for j in range(n):
        hj = h if h is not None else _step_for(x[j])
        xp = x.copy(); xm = x.copy()
        xp[j] += hj; xm[j] -= hj
        if j == n - 1 and xm[j] < 0.0:
            f0 = rhs(x, p); fp = rhs(xp, p)
            J[:, j] = (fp - f0) / hj
        else:
            J[:, j] = (rhs(xp, p) - rhs(xm, p)) / (2.0 * hj)
    return J


def sign_matrix(J, tol: float = 1e-10):
    """Integer sign matrix: +1, 0, -1."""
    S = np.zeros_like(J, dtype=int)
    S[J > tol] = 1
    S[J < -tol] = -1
    return S


def check_demographic_decoupling(x, params: ACMFParams | None = None, tol: float = 1e-6):
    """Check dF_i/dP ~= 0 for i=0..8 at a given state."""
    p = params or default_params()
    x = np.asarray(x, dtype=float)
    J = numerical_jacobian(x, p)
    derivs = J[:-1, -1]
    max_abs = float(np.max(np.abs(derivs)))
    return {
        "dFi_dP": derivs,
        "max_abs": max_abs,
        "passed": bool(max_abs < tol),
        "note": "Expected away from the smoothing layer; near P~epsilon soft terms may dominate.",
    }


def check_P_invariance(P_candidates, params: ACMFParams | None = None, other_state=None):
    """Evaluate dP/dt for candidate P values with fixed non-demographic state."""
    p = params or default_params()
    if other_state is None:
        other_state = np.array([0.5, 0.5, 0.5, 0.5, 0.5, 0.3, 0.6, 0.5, 2.0])
    results = []
    for p_val in P_candidates:
        x = np.concatenate([np.asarray(other_state, dtype=float), [float(p_val)]])
        results.append((float(p_val), float(rhs(x, p)[9])))
    return results


def spectrum_analysis(x, params: ACMFParams | None = None):
    """Local linear spectrum of the numerical Jacobian at x."""
    J = numerical_jacobian(x, params)
    eigvals = np.linalg.eigvals(J)
    return {
        "eigenvalues": eigvals,
        "max_real": float(np.max(eigvals.real)),
        "locally_stable": bool(np.all(eigvals.real < 0)),
        "decoupling_block_eigenvalues": np.linalg.eigvals(J[:9, :9]),
        "P_mode_eigenvalue": float(J[9, 9]),
    }


def feedback_loops_summary(x, params: ACMFParams | None = None):
    """Human-readable sign matrix for feedback-loop inspection."""
    J = numerical_jacobian(x, params)
    S = sign_matrix(J)
    lines = ["Jacobian sign matrix J_ij = dF_i/dX_j:", "    " + "  ".join(f"{n:>4}" for n in STATE_NAMES)]
    for i, name in enumerate(STATE_NAMES):
        row = " ".join(f"{S[i, j]:>+4d}" for j in range(len(STATE_NAMES)))
        lines.append(f"{name:>4} [{row}]")
    return "\n".join(lines)

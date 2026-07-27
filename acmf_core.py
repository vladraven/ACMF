"""ACMF core ODE/RHS, complete-system compatibility entrypoint.

State layout per province is 12 variables:
A, Prod, Ch, M, G, V, Inst, R, F, P1, P2, P3.

Important v2.1 change:
- This legacy RHS is retained for compatibility and scenario experiments.
- Historical demographic validation should use acmf/demography_age_structured.py.
- P1/P2/P3 are no longer considered sufficient internal demographic state for
  empirical validation; they are reporting aggregates.
"""
from __future__ import annotations
import numpy as np

STATE_NAMES = ["A", "Prod", "Ch", "M", "G", "V", "Inst", "R", "F", "P1", "P2", "P3"]


def _clip01(x):
    return np.clip(x, 0.0, 1.0)


def dependency_ratio(P1, P2, P3):
    return (P1 + P3) / np.maximum(P2, 1.0)


def migration_pressure(X, p):
    # pressure increases with vulnerability/stress and low productivity/resilience.
    Prod = X[:, 1]
    V = X[:, 5]
    R = X[:, 7]
    dep = dependency_ratio(X[:, 9], X[:, 10], X[:, 11])
    pressure = 0.35 * V + 0.25 * (1.0 - Prod) + 0.20 * (1.0 - R) + 0.20 * dep / (1.0 + dep)
    return np.clip(pressure, 0.0, 2.0)


def migration_matrix(X, p, Distance):
    N = X.shape[0]
    D = np.asarray(Distance, dtype=float)
    if D.shape != (N, N):
        D = np.ones((N, N), dtype=float)
        np.fill_diagonal(D, 0.0)
    press = migration_pressure(X, p)
    attractiveness = np.clip(X[:, 1] + X[:, 7] - X[:, 5], -2.0, 2.0)
    flows = np.zeros((N, N), dtype=float)
    sigma = float(p.get("sigma_dist", 1.0))
    coeff = float(p.get("migration_rate_coeff", 0.02))
    for i in range(N):
        for j in range(N):
            if i == j:
                continue
            pull = max(0.0, attractiveness[j] - attractiveness[i] + press[i])
            aff = np.exp(-D[i, j] / max(sigma, 1e-9))
            flows[i, j] = coeff * pull * aff
    return flows


def rhs_acmf(t, y, p, Distance):
    N = int(p.get("N", len(y) // 12))
    X = np.asarray(y, dtype=float).reshape(N, 12)
    d = np.zeros_like(X)

    A, Prod, Ch, M, G, V, Inst, R, F, P1, P2, P3 = [X[:, i] for i in range(12)]
    Ptot = np.maximum(P1 + P2 + P3, 1.0)
    dep = dependency_ratio(P1, P2, P3)

    # latent/system dynamics
    d[:, 0] = p.get("rA", 0.04) * A * (1 - A / max(p.get("A_max", 0.95), 1e-9)) + 0.01 * Ch - 0.01 * V
    d[:, 1] = p.get("eta_prod_A", 0.08) * A + p.get("eta_prod_ch", 0.03) * Ch - p.get("delta_prod_stress", 0.03) * V
    d[:, 2] = p.get("r_ch", 0.03) * (Inst - Ch) + 0.01 * Prod
    d[:, 3] = p.get("r_mob", 0.02) * (Prod - M) - 0.01 * V
    d[:, 4] = p.get("r_gov", 0.02) * (Inst - G)
    d[:, 5] = 0.03 * (p.get("s1", 1.5) * dep / (1 + dep) + p.get("s2", 1.2) * (1 - Prod) - V)
    d[:, 6] = p.get("r_inst", 0.02) * (G + Ch - 2 * Inst)
    d[:, 7] = p.get("r_res", 0.02) * (Ch + Inst - V - R)

    # fertility state dynamics
    fertility_target = p.get("k_sat", 18.0) / 10.0
    d[:, 8] = p.get("lambda_fert", 0.05) * (fertility_target - F) - p.get("beta_fert_stress", 0.10) * V * F

    # legacy P1/P2/P3 demographic block retained for scenarios/back-compat.
    births = np.maximum(0.0, (p.get("b0", 0.005) + p.get("b1", 0.015) * F / 4.0) * 0.49 * 0.56 * P2)
    mig = migration_matrix(X, p, Distance)
    out_rate = np.clip(mig.sum(axis=1), 0.0, p.get("k_out", 0.05))
    in_rate = mig.sum(axis=0)
    net = (in_rate - out_rate) * Ptot
    # simple age allocation for legacy state; empirical engine should replace this
    net1, net2, net3 = 0.20 * net, 0.70 * net, 0.10 * net
    d[:, 9] = births - (p.get("mu1", 0.002) + p.get("gamma1", 1/15)) * P1 + net1
    d[:,10] = p.get("gamma1", 1/15) * P1 - (p.get("mu2", 0.005) + p.get("gamma2", 1/48)) * P2 + net2
    d[:,11] = p.get("gamma2", 1/48) * P2 - p.get("mu3", 0.035) * P3 + net3

    # keep fractions bounded implicitly by restorative clipping terms
    for idx in range(8):
        d[:, idx] += -0.05 * np.maximum(0, X[:, idx] - 1.0) + 0.05 * np.maximum(0, -X[:, idx])
    return d.reshape(-1)

#!/usr/bin/env python3
"""Run ACMF diagnostics and a short scenario simulation."""
from __future__ import annotations
import numpy as np

from acmf import (
    default_params, rhs, algebraic_layer, adaptive_dynamics_layer,
    simulate, numerical_jacobian, check_demographic_decoupling,
    check_P_invariance, spectrum_analysis, feedback_loops_summary,
)


def print_header(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def main():
    x0 = np.array([0.3, 0.4, 0.5, 0.5, 0.5, 0.3, 0.6, 0.5, 2.0, 500.0])
    p = default_params()

    print_header("ACMF 3.3.1.2 diagnostics")
    print("rhs(x0) =", rhs(x0, p))
    a = algebraic_layer(x0, p)
    print("algebraic keys:", sorted(k for k in a if not k.startswith("__"))[:12], "...")

    print_header("Adaptive dynamics")
    print(adaptive_dynamics_layer(x0, p))

    print_header("Jacobian")
    J = numerical_jacobian(x0, p)
    print("shape:", J.shape, "max_abs:", float(np.max(np.abs(J))))
    print(feedback_loops_summary(x0, p))

    print_header("Decoupling and P invariance")
    print(check_demographic_decoupling(np.array([*x0[:9], 1e6]), p, tol=1e-4))
    print(check_P_invariance([1e6, 1e7], p))

    print_header("Local spectrum")
    spec = spectrum_analysis(x0, p)
    print("max_real:", spec["max_real"], "locally_stable:", spec["locally_stable"])

    print_header("Short simulation")
    t, traj = simulate(x0, (0, 2), dt=0.1, params=p)
    print("steps:", len(t), "final:", traj[-1])


if __name__ == "__main__":
    main()

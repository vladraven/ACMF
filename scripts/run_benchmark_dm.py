#!/usr/bin/env python3
"""Compare ACMF synthetic forecast against econometric benchmarks with DM tests."""
from __future__ import annotations
import numpy as np

from acmf import (
    default_params, simulate, fit_all_benchmarks, forecast_all_benchmarks,
    compare_acmf_vs_benchmarks,
)


def generate_synthetic_data(true_p, t_span=(1970, 2025), dt=1.0, noise=0.01, seed=42):
    rng = np.random.default_rng(seed)
    x0 = np.array([0.3, 0.4, 0.5, 0.5, 0.5, 0.3, 0.6, 0.5, 2.0, 500.0])
    t, traj = simulate(x0, t_span, dt, true_p)
    data = {"t": t}
    for name, idx in [("P", 9), ("Prod", 1), ("A", 0), ("Inst", 6), ("F", 8)]:
        scale = np.std(traj[:, idx]) or 1.0
        data[name] = traj[:, idx] + rng.normal(0.0, noise * scale, size=len(t))
    return data, traj


def main():
    print("=" * 60)
    print("  ACMF Phase II benchmark + Diebold-Mariano demo")
    print("=" * 60)
    true_p = default_params(alpha7=0.8, K_g=0.5, beta_neg=0.3, NaturalDecay=0.08, q1=0.2, q3=0.4, alpha1=0.6, b1=0.03)
    data, true_traj = generate_synthetic_data(true_p)
    mask_train = data["t"] <= 2010
    mask_test = data["t"] > 2010
    t_train = data["t"][mask_train]
    t_test = data["t"][mask_test]
    # Put P first so single-series models target population.
    names = ["P", "Prod", "A", "Inst", "F"]
    data_train = {k: data[k][mask_train] for k in names}
    data_test = {k: data[k][mask_test] for k in names}
    fitted = fit_all_benchmarks(data_train, t_train)
    benchmarks = forecast_all_benchmarks(data_train, t_train, t_test, fitted)
    # Synthetic demo: ACMF forecast uses the known generating model over full horizon.
    acmf_forecast = true_traj[mask_test, 9]
    actual = data_test["P"]
    print("Out-of-sample length:", len(t_test))
    print("\nRMSE:")
    for name, forecast in benchmarks.items():
        rmse = float(np.sqrt(np.mean((actual - forecast) ** 2)))
        print(f"  {name:>16}: {rmse:.4f}")
    acmf_rmse = float(np.sqrt(np.mean((actual - acmf_forecast) ** 2)))
    print(f"  {'ACMF':>16}: {acmf_rmse:.4f}")
    print("\nDiebold-Mariano tests:")
    for name, result in compare_acmf_vs_benchmarks(actual, acmf_forecast, benchmarks).items():
        print(f"  {name:>16}: DM={result['DM_stat']:+.3f}, p={result['p_value']:.4f}, better={result['better_model']}")


if __name__ == "__main__":
    main()

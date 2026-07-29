#!/usr/bin/env python3
"""Run a small ACMF Phase II calibration demo on synthetic data."""
from __future__ import annotations
import os
import numpy as np

from acmf import default_params, simulate, LossConfig, run_calibration_pipeline, ACMFObjective


def generate_synthetic_data(true_params=None, t_span=(1970, 1975), dt=1.0, noise_std=0.01, seed=42):
    rng = np.random.default_rng(seed)
    p = true_params or default_params()
    x0 = np.array([0.3, 0.4, 0.5, 0.5, 0.5, 0.3, 0.6, 0.5, 2.0, 500.0])
    times, traj = simulate(x0, t_span, dt, p)
    data = {"t": times}
    obs_map = {"P": 9, "Prod": 1, "A": 0, "Inst": 6, "F": 8}
    for name, idx in obs_map.items():
        scale = np.std(traj[:, idx]) or 1.0
        data[name] = traj[:, idx] + rng.normal(0, noise_std * scale, size=len(times))
    return data, p, traj


def main():
    true_p = default_params(alpha7=0.8, K_g=0.5, beta_neg=0.3, NaturalDecay=0.08, q1=0.2, q3=0.4, alpha1=0.6, b1=0.03)
    data, _, _ = generate_synthetic_data(true_p)
    config = LossConfig(observed_vars=["P", "Prod", "A", "Inst", "F"], lambda_deriv=0.5)
    result = run_calibration_pipeline(data, config=config, de_maxiter=2, mcmc_samples=200, mcmc_burn_in=50, seed=42)
    print("theta names:", ACMFObjective.THETA_NAMES)
    print("theta_opt:", result.theta_opt)
    print("loss_opt:", result.loss_opt)
    print("mcmc_acceptance_rate:", result.mcmc_acceptance_rate)
    os.makedirs("output", exist_ok=True)
    np.savez("output/calibration_result.npz", theta_opt=result.theta_opt, mcmc_samples=result.mcmc_samples, loss_opt=result.loss_opt)
    print("saved: output/calibration_result.npz")


if __name__ == "__main__":
    main()

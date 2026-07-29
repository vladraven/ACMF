#!/usr/bin/env python3
"""ACMF Phase III Digital Twin demo with EnKF assimilation."""
from __future__ import annotations
import os
import numpy as np

from acmf import default_params, simulate, DigitalTwin


def generate_noisy_observations(true_p, years, dt=1.0, noise=0.02, seed=42):
    rng = np.random.default_rng(seed)
    x0 = np.array([0.3, 0.4, 0.5, 0.5, 0.5, 0.3, 0.6, 0.5, 2.0, 500.0])
    t, traj = simulate(x0, (years[0], years[-1]), dt, true_p)
    obs = []
    for year in years:
        idx = int(np.argmin(np.abs(t - year)))
        y = traj[idx]
        y_obs = np.array([y[9], y[1], y[0], y[6], y[8]])
        scale = np.std(y_obs) or 1.0
        y_obs = y_obs + rng.normal(0.0, noise * scale, size=5)
        obs.append((float(year), y_obs))
    return obs


def main():
    print("=" * 60)
    print("  ACMF Phase III Digital Twin demo")
    print("=" * 60)
    true_p = default_params(alpha7=0.8, beta_neg=0.3)
    years = np.arange(1970, 1981)
    observations = generate_noisy_observations(true_p, years, noise=0.01)
    twin = DigitalTwin(params=true_p, enkf_ensemble_size=30, dt_enkf=1.0, seed=42)
    for year, y_obs in observations:
        twin.assimilate(year, y_obs)
    report = twin.get_state_report()
    print("Current time:", report["time"])
    print("Latent:", report["latent"])
    t_forecast, traj_forecast = twin.forecast(n_years=5, dt=0.5)
    print("Forecast final P:", float(traj_forecast[-1, 9]))
    scenario = twin.scenario_forecast(5, {"U_corr": 0.9, "NaturalDecay": 0.01}, dt=0.5)
    print("Scenario final Inst:", float(scenario["trajectory"][-1, 6]))
    os.makedirs("output", exist_ok=True)
    np.savez("output/digital_twin_forecast.npz", t_forecast=t_forecast, traj_forecast=traj_forecast)
    print("saved: output/digital_twin_forecast.npz")


if __name__ == "__main__":
    main()

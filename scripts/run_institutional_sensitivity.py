#!/usr/bin/env python3
"""ACMF 4.2.1 â€” Institutional sensitivity grid: alpha_pos x beta_neg x beta_sd."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))

from acmf.core import default_params, rhs, STATE_NAMES
from acmf.solver import rk4_step
from scripts.run_synthetic_forecast_benchmark import ForecastBenchmark

SENSITIVITY_SCENARIOS = (
    "level_shift_shock_recovery",
    "saturation_curve",
    "regime_change_stress",
    "low_stress_trend",
)

DT = 0.5


def _run_scenario(scenario: str, p, steps: int) -> dict:
    """Integrate one scenario and return computed behavioral metrics."""
    bench = ForecastBenchmark(scenario_name=scenario)
    synth_steps = max(200, steps + 20)
    data = bench.generate_synthetic_data(n_steps=synth_steps)
    x = bench._build_state(data, 0)

    inst_vals: list[float] = []
    dInst_vals: list[float] = []

    for _ in range(steps):
        A, Prod, Ch, M, G, V, Inst, R, F, P_ = x
        dx = rhs(x, p)
        inst_vals.append(float(Inst))
        dInst_vals.append(float(dx[6]))

        x = rk4_step(x, DT, p)
        x[:8] = np.clip(x[:8], 0.0, 1.0)
        x[8] = np.clip(x[8], 0.0, 4.0)
        x[9] = max(float(x[9]), 0.0)

    inst_arr = np.array(inst_vals)
    dInst_arr = np.array(dInst_vals)

    mean_dInst = float(np.mean(dInst_arr))
    inst_at_end = inst_arr[-1]
    inst_min = float(np.min(inst_arr))
    inst_max = float(np.max(inst_arr))

    signs = np.sign(dInst_arr)
    sign_flip_count = int(np.sum(np.diff(signs) != 0))

    recovery_detected = False
    if scenario == "level_shift_shock_recovery":
        drop_threshold = 0.05
        for i in range(1, len(inst_arr) - 1):
            if inst_arr[i] < inst_arr[i - 1] - drop_threshold:
                if np.max(inst_arr[i:]) > inst_arr[i] + drop_threshold:
                    recovery_detected = True
                    break

    # recovery_window_exists: consecutive dInst > 0 in level_shift post-midpoint
    recovery_window_exists = False
    if scenario == "level_shift_shock_recovery":
        mid = steps // 2
        post_mid = dInst_arr[mid:]
        count = 0
        for v in post_mid:
            if v > 0:
                count += 1
                if count >= 3:
                    recovery_window_exists = True
                    break
            else:
                count = 0

    # artificial_growth: Inst > 0.9 for >20% of steps
    artificial_growth = bool(np.mean(inst_arr > 0.9) > 0.20)

    # persistent_deg: Inst monotonically declined (regime_change scenario)
    persistent_deg = False
    if scenario == "regime_change_stress":
        diffs = np.diff(inst_arr)
        persistent_deg = bool(np.all(diffs <= 0))

    return {
        "mean_dInst": mean_dInst,
        "sign_flip_count": sign_flip_count,
        "inst_at_end": float(inst_at_end),
        "inst_min": inst_min,
        "inst_max": inst_max,
        "recovery_detected": recovery_detected,
        "recovery_window_exists": recovery_window_exists,
        "artificial_growth": artificial_growth,
        "persistent_deg": persistent_deg,
    }


def _scenario_balance_score(metrics_by_scenario: dict[str, dict]) -> int:
    """Compute scenario balance score.

    +1  low_stress:    mean_dInst in [-0.002, +0.01]  (quasi-equilibrium)
    +2  level_shift:   recovery_window_exists (dInst > 0 for >=3 consecutive steps)
    +1  regime_change: mean_dInst < -0.001 (persistent degradation works)
    -1  ANY scenario:  artificial_growth == True
    -1  ANY scenario:  unstable_oscillation (sign_flip_count > 30)
    Range: -2 to +4
    """
    score = 0
    low = metrics_by_scenario.get("low_stress_trend", {})
    level = metrics_by_scenario.get("level_shift_shock_recovery", {})
    regime = metrics_by_scenario.get("regime_change_stress", {})

    low_dInst = low.get("mean_dInst", -1.0)
    if -0.002 <= low_dInst <= 0.01:
        score += 1

    if level.get("recovery_window_exists", False):
        score += 2

    if regime.get("mean_dInst", 0) < -0.001:
        score += 1

    for sc_metrics in metrics_by_scenario.values():
        if sc_metrics.get("artificial_growth", False):
            score -= 1
            break

    for sc_metrics in metrics_by_scenario.values():
        if sc_metrics.get("sign_flip_count", 0) > 30:
            score -= 1
            break

    return score


def run_sensitivity_grid(
    alpha_pos_values: list[float] | None = None,
    beta_neg_values: list[float] | None = None,
    beta_sd_fixed: float | None = None,
    output_dir: Path = Path("artifacts/diagnostics"),
    steps: int = 120,
) -> pd.DataFrame:
    """Grid sensitivity over alpha_pos x beta_neg (beta_sd fixed at default or beta_sd_fixed)."""
    if alpha_pos_values is None:
        alpha_pos_values = [0.10, 0.25, 0.50, 1.00]
    if beta_neg_values is None:
        beta_neg_values = [0.05, 0.10, 0.20, 0.40]

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    overrides: dict = {}
    if beta_sd_fixed is not None:
        overrides["beta_sd"] = beta_sd_fixed

    rows: list[dict] = []

    for alpha_pos in alpha_pos_values:
        for beta_neg in beta_neg_values:
            p = default_params(alpha_pos=alpha_pos, beta_neg=beta_neg, **overrides)
            metrics_by_sc: dict[str, dict] = {}

            for scenario in SENSITIVITY_SCENARIOS:
                m = _run_scenario(scenario, p, steps)
                metrics_by_sc[scenario] = m
                rows.append({
                    "alpha_pos": alpha_pos,
                    "beta_neg": beta_neg,
                    "beta_sd": p.beta_sd,
                    "scenario": scenario,
                    **m,
                    "scenario_balance_score": None,
                })

            balance = _scenario_balance_score(metrics_by_sc)
            for row in rows:
                if row["alpha_pos"] == alpha_pos and row["beta_neg"] == beta_neg:
                    row["scenario_balance_score"] = balance

    df = pd.DataFrame(rows)
    outpath = output_dir / "institutional_sensitivity_grid.csv"
    df.to_csv(outpath, index=False)

    pivot = (
        df.drop_duplicates(subset=["alpha_pos", "beta_neg"])[["alpha_pos", "beta_neg", "scenario_balance_score"]]
        .pivot(index="alpha_pos", columns="beta_neg", values="scenario_balance_score")
    )
    print("\n" + "=" * 80)
    print("Sensitivity Pivot: alpha_pos x beta_neg -> scenario_balance_score")
    print("=" * 80)
    print(pivot.to_string())

    best_row = df.drop_duplicates(subset=["alpha_pos", "beta_neg"]).sort_values("scenario_balance_score", ascending=False).iloc[0]
    print(f"\nBest (alpha_pos={best_row['alpha_pos']}, beta_neg={best_row['beta_neg']}): score={int(best_row['scenario_balance_score'])}")
    print(f"Saved: {outpath}")
    return df


def run_beta_sd_sensitivity(
    beta_sd_values: list[float] | None = None,
    alpha_pos_fixed: float = 0.25,
    beta_neg_fixed: float = 0.20,
    output_dir: Path = Path("artifacts/diagnostics"),
    steps: int = 120,
) -> pd.DataFrame:
    """Grid sensitivity over beta_sd with alpha_pos and beta_neg fixed.

    Answers: is there a beta_sd range where recoverable_shock recovers
    but persistent_degradation still works?
    """
    if beta_sd_values is None:
        beta_sd_values = [0.03, 0.08, 0.15, 0.25]

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []

    for beta_sd in beta_sd_values:
        p = default_params(alpha_pos=alpha_pos_fixed, beta_neg=beta_neg_fixed, beta_sd=beta_sd)
        metrics_by_sc: dict[str, dict] = {}

        for scenario in SENSITIVITY_SCENARIOS:
            m = _run_scenario(scenario, p, steps)
            metrics_by_sc[scenario] = m
            rows.append({
                "beta_sd": beta_sd,
                "scenario": scenario,
                **m,
                "scenario_balance_score": None,
            })

        balance = _scenario_balance_score(metrics_by_sc)
        for row in rows:
            if row["beta_sd"] == beta_sd:
                row["scenario_balance_score"] = balance

    df = pd.DataFrame(rows)
    outpath = output_dir / "institutional_beta_sd_sensitivity.csv"
    df.to_csv(outpath, index=False)

    print("\n" + "=" * 80)
    print(f"beta_sd Sensitivity (alpha_pos={alpha_pos_fixed}, beta_neg={beta_neg_fixed})")
    print("=" * 80)
    agg = df.groupby("beta_sd")[["mean_dInst", "recovery_detected", "artificial_growth", "scenario_balance_score"]].agg(
        {"mean_dInst": "mean", "recovery_detected": "any", "artificial_growth": "any", "scenario_balance_score": "first"}
    )
    print(agg.to_string())
    print(f"\nSaved: {outpath}")
    return df


def run_gate_amp_sensitivity(
    gate_amp_values: list[float] | None = None,
    alpha_pos_fixed: float = 0.25,
    beta_neg_fixed: float = 0.20,
    beta_sd_fixed: float = 0.08,
    output_dir: Path = Path("artifacts/diagnostics"),
    steps: int = 120,
) -> pd.DataFrame:
    """Grid sensitivity over gate_amp with alpha_pos, beta_neg, beta_sd fixed.

    Answers: at what gate_amp does recovery gate become functionally significant
    (>=5% of pull) without triggering artificial growth?
    """
    if gate_amp_values is None:
        gate_amp_values = [1.0, 3.0, 5.0, 10.0, 20.0]

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []

    for gate_amp in gate_amp_values:
        p = default_params(
            alpha_pos=alpha_pos_fixed,
            beta_neg=beta_neg_fixed,
            beta_sd=beta_sd_fixed,
            gate_amp=gate_amp,
        )
        metrics_by_sc: dict[str, dict] = {}

        for scenario in SENSITIVITY_SCENARIOS:
            m = _run_scenario(scenario, p, steps)
            metrics_by_sc[scenario] = m
            rows.append({
                "gate_amp": gate_amp,
                "scenario": scenario,
                **m,
                "scenario_balance_score": None,
            })

        balance = _scenario_balance_score(metrics_by_sc)
        for row in rows:
            if row["gate_amp"] == gate_amp:
                row["scenario_balance_score"] = balance

    df = pd.DataFrame(rows)
    outpath = output_dir / "institutional_gate_amp_sensitivity.csv"
    df.to_csv(outpath, index=False)

    print("\n" + "=" * 80)
    print(f"gate_amp Sensitivity (alpha_pos={alpha_pos_fixed}, beta_neg={beta_neg_fixed}, beta_sd={beta_sd_fixed})")
    print("=" * 80)
    agg = df.groupby("gate_amp")[["mean_dInst", "recovery_detected", "recovery_window_exists", "artificial_growth", "scenario_balance_score"]].agg(
        {"mean_dInst": "mean", "recovery_detected": "any", "recovery_window_exists": "any", "artificial_growth": "any", "scenario_balance_score": "first"}
    )
    print(agg.to_string())
    print(f"\nSaved: {outpath}")
    return df


def main() -> int:
    parser = argparse.ArgumentParser(description="Institutional sensitivity grid diagnostics")
    parser.add_argument("--steps", type=int, default=60)
    parser.add_argument("--output-dir", default="artifacts/diagnostics")
    parser.add_argument("--mode", choices=["alpha_beta", "beta_sd", "gate_amp", "all"], default="all")
    args = parser.parse_args()

    out = Path(args.output_dir)
    if args.mode in ("alpha_beta", "all"):
        run_sensitivity_grid(output_dir=out, steps=args.steps)
    if args.mode in ("beta_sd", "all"):
        run_beta_sd_sensitivity(output_dir=out, steps=args.steps)
    if args.mode in ("gate_amp", "all"):
        run_gate_amp_sensitivity(output_dir=out, steps=args.steps)
    return 0


if __name__ == "__main__":
    sys.exit(main())

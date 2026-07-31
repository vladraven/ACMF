#!/usr/bin/env python3
"""ACMF 4.2.0 — Institutional sensitivity grid over alpha_pos × beta_neg."""
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
    """Integrate one scenario and return computed metrics."""
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

    # sign_flip_count: number of times dInst changes sign
    signs = np.sign(dInst_arr)
    sign_flip_count = int(np.sum(np.diff(signs) != 0))

    # recovery_detected: Inst went up after a drop > 0.05 (for level_shift scenario)
    recovery_detected = False
    if scenario == "level_shift_shock_recovery":
        drop_threshold = 0.05
        for i in range(1, len(inst_arr) - 1):
            if inst_arr[i] < inst_arr[i - 1] - drop_threshold:
                # check if Inst recovers after this point
                if np.max(inst_arr[i:]) > inst_arr[i] + drop_threshold:
                    recovery_detected = True
                    break

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
        "artificial_growth": artificial_growth,
        "persistent_deg": persistent_deg,
    }


def _scenario_balance_score(metrics_by_scenario: dict[str, dict]) -> int:
    """Compute scenario balance score for one (alpha_pos, beta_neg) pair.

    +1  low_stress:      mean_dInst >= -0.001 (stable/growing)
    +1  level_shift:     recovery_detected == True
    +1  regime_change:   mean_dInst < 0 (responds to stress)
    -1  ANY scenario:    artificial_growth == True
    Range: -1 to +3
    """
    score = 0
    low = metrics_by_scenario.get("low_stress_trend", {})
    level = metrics_by_scenario.get("level_shift_shock_recovery", {})
    regime = metrics_by_scenario.get("regime_change_stress", {})

    if low.get("mean_dInst", -1) >= -0.001:
        score += 1
    if level.get("recovery_detected", False):
        score += 1
    if regime.get("mean_dInst", 0) < 0:
        score += 1

    for sc_metrics in metrics_by_scenario.values():
        if sc_metrics.get("artificial_growth", False):
            score -= 1
            break  # penalise once

    return score


def run_sensitivity_grid(
    alpha_pos_values: list[float] | None = None,
    beta_neg_values: list[float] | None = None,
    output_dir: Path = Path("artifacts/diagnostics"),
    steps: int = 120,
) -> pd.DataFrame:
    """Grid sensitivity over alpha_pos × beta_neg for all SENSITIVITY_SCENARIOS."""
    if alpha_pos_values is None:
        alpha_pos_values = [0.10, 0.25, 0.50, 1.00]
    if beta_neg_values is None:
        beta_neg_values = [0.05, 0.10, 0.20, 0.40]

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []

    for alpha_pos in alpha_pos_values:
        for beta_neg in beta_neg_values:
            p = default_params(alpha_pos=alpha_pos, beta_neg=beta_neg)
            metrics_by_sc: dict[str, dict] = {}

            for scenario in SENSITIVITY_SCENARIOS:
                m = _run_scenario(scenario, p, steps)
                metrics_by_sc[scenario] = m
                rows.append({
                    "alpha_pos": alpha_pos,
                    "beta_neg": beta_neg,
                    "scenario": scenario,
                    **m,
                    "scenario_balance_score": None,  # filled below
                })

            balance = _scenario_balance_score(metrics_by_sc)
            # Backfill balance score for all rows of this (alpha_pos, beta_neg) pair
            for row in rows:
                if row["alpha_pos"] == alpha_pos and row["beta_neg"] == beta_neg:
                    row["scenario_balance_score"] = balance

    df = pd.DataFrame(rows)
    outpath = output_dir / "institutional_sensitivity_grid.csv"
    df.to_csv(outpath, index=False)

    # Print pivot table: alpha_pos × beta_neg → scenario_balance_score
    pivot = (
        df.drop_duplicates(subset=["alpha_pos", "beta_neg"])[["alpha_pos", "beta_neg", "scenario_balance_score"]]
        .pivot(index="alpha_pos", columns="beta_neg", values="scenario_balance_score")
    )
    print("\n" + "=" * 80)
    print("Sensitivity Pivot: alpha_pos x beta_neg -> scenario_balance_score")
    print("=" * 80)
    print(pivot.to_string())

    # Best combo
    best_idx = df.drop_duplicates(subset=["alpha_pos", "beta_neg"]).set_index(["alpha_pos", "beta_neg"])["scenario_balance_score"].idxmax()
    print(f"\nBest (alpha_pos={best_idx[0]}, beta_neg={best_idx[1]}): score={pivot.loc[best_idx[0], best_idx[1]]}")
    print(f"Saved: {outpath}")
    return df


def main() -> int:
    parser = argparse.ArgumentParser(description="Institutional sensitivity grid diagnostics")
    parser.add_argument("--steps", type=int, default=60)
    parser.add_argument("--output-dir", default="artifacts/diagnostics")
    args = parser.parse_args()
    run_sensitivity_grid(
        output_dir=Path(args.output_dir),
        steps=args.steps,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

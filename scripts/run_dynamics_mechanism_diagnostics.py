#!/usr/bin/env python3
"""
Mechanism-level diagnostics for ACMF dynamics.
Traces recovery_pull vs recovery_drag, inst_pull vs inst_drag, StructuralLimits,
and bounds-hit counts for each diagnostic scenario.
Outputs: dynamics_mechanism_response.csv, bounds_hit_report.csv
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from acmf.core import STATE_NAMES, algebraic_layer, default_params, rhs
from acmf.solver import rk4_step
from scripts.run_synthetic_forecast_benchmark import ForecastBenchmark

DIAGNOSTIC_SCENARIOS = (
    "level_shift_shock_recovery",
    "saturation_curve",
    "regime_change_stress",
)


def _project(state: np.ndarray) -> np.ndarray:
    s = state.copy()
    s[:8] = np.clip(s[:8], 0.0, 1.0); s[8] = np.clip(s[8], 0.0, 4.0); s[9] = max(s[9], 0.0)
    return s


def _simulate_trace(scenario: str, steps: int, dt: float) -> tuple:
    params = default_params()
    synth = ForecastBenchmark(scenario_name=scenario, seed=42).generate_synthetic_data(n_steps=max(200, steps + 1))
    state = np.array([float(synth["x"][0]), 0.2, float(synth["z"][0]), 0.5, 0.4,
                      float(np.clip(synth["stress"][0], 0.0, 1.0)), 0.5, 0.5, 2.0, 100.0], dtype=float)
    lower = np.array([0.0] * 10); upper = np.array([1.0] * 8 + [4.0, 1e12])
    lower_hits = np.zeros(10, dtype=int); upper_hits = np.zeros(10, dtype=int)

    rows = []
    for t in range(steps):
        mech = algebraic_layer(state, params)
        dx = rhs(state, params)
        stress_signal = float(min(1.0, max(0.0, 0.5 * state[5] + 0.5 * mech["S"])))
        recovery_bell = 4.0 * stress_signal * (1.0 - stress_signal)
        stress_overload = max(0.0, stress_signal - params.stress_overload_threshold)
        row = {"scenario": scenario, "t": t}
        for idx, sn in enumerate(STATE_NAMES):
            row[sn] = float(state[idx]); row[f"d{sn}"] = float(dx[idx])
        row.update({
            "synthetic_x": float(synth["x"][t]),
            "synthetic_stress": float(synth["stress"][t]),
            "synthetic_dy": float(synth["dy"][t]),
            "RecoveryDriver": float(mech["RecoveryDriver"]),
            "S": float(mech["S"]),
            "TechSaturation": float(mech["TechSaturation"]),
            "StructuralLimits": float(mech["StructuralLimits"]),
            "stress_signal": stress_signal,
            "recovery_bell": recovery_bell,
            "stress_overload": stress_overload,
            "recovery_pull": float(params.alpha_rec * mech["RecoveryDriver"] * (recovery_bell + 0.2) * (1.0 - state[7])),
            "recovery_stress_drag": float(params.beta_rec_stress * stress_overload * state[7]),
            "recovery_net": float(dx[7]),
            "inst_pull": float(params.alpha_pos * (state[7] * mech["SocialCapital"] + params.gamma_inst * state[3] * state[4]) * (1.0 - state[6])),
            "inst_drag": float((params.NaturalDecay + params.beta_neg * (mech["Corruption"] * state[5] + mech["StructuralDecay"])) * state[6]),
            "inst_net": float(dx[6]),
        })
        rows.append(row)
        raw_next = rk4_step(state, dt, params)
        lower_hits += (raw_next < lower).astype(int)
        upper_hits += (raw_next > upper).astype(int)
        state = _project(raw_next)

    bounds_rows = []
    for idx, sn in enumerate(STATE_NAMES):
        hits = int(lower_hits[idx] + upper_hits[idx])
        bounds_rows.append({"scenario": scenario, "state": sn,
                             "lower_hits": int(lower_hits[idx]), "upper_hits": int(upper_hits[idx]),
                             "hits_total": hits, "hit_fraction": hits / max(steps, 1)})
    return pd.DataFrame(rows), pd.DataFrame(bounds_rows)


def run_mechanism_diagnostics(output_dir: Path, steps: int = 120, dt: float = 0.5) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    resp_frames, bounds_frames = [], []
    for scenario in DIAGNOSTIC_SCENARIOS:
        resp_df, bounds_df = _simulate_trace(scenario=scenario, steps=steps, dt=dt)
        resp_frames.append(resp_df); bounds_frames.append(bounds_df)
    all_resp = pd.concat(resp_frames, ignore_index=True)
    all_bounds = pd.concat(bounds_frames, ignore_index=True)
    all_resp.to_csv(output_dir / "dynamics_mechanism_response.csv", index=False)
    all_bounds.to_csv(output_dir / "bounds_hit_report.csv", index=False)
    print(f"Saved: {output_dir}/dynamics_mechanism_response.csv")
    print(f"Saved: {output_dir}/bounds_hit_report.csv")
    agg = all_resp.groupby("scenario")[["recovery_pull", "recovery_stress_drag", "recovery_net",
                                        "inst_pull", "inst_drag", "inst_net", "StructuralLimits"]].mean()
    print("\nMechanism means:")
    print(agg.to_string())
    return {"response": all_resp, "bounds": all_bounds}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="artifacts/diagnostics")
    parser.add_argument("--steps", type=int, default=120)
    parser.add_argument("--dt", type=float, default=0.5)
    args = parser.parse_args()
    run_mechanism_diagnostics(output_dir=Path(args.output_dir), steps=args.steps, dt=args.dt)
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""ACMF 4.2.0 — Institutional loop pull/drag decomposition diagnostics."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))

from acmf.core import algebraic_layer, default_params, rhs, STATE_NAMES
from acmf.solver import rk4_step
from acmf.smoothing import smax, smin, EPSILON
from scripts.run_synthetic_forecast_benchmark import ForecastBenchmark

INST_SCENARIOS = (
    "level_shift_shock_recovery",
    "saturation_curve",
    "regime_change_stress",
    "low_stress_trend",
)

DT = 0.5


def _decompose_inst(x: np.ndarray, p) -> dict:
    """Compute full pull/drag decomposition for the institutional equation at state x."""
    A, Prod, Ch, M, G, V, Inst, R, F, P_ = x
    a = algebraic_layer(x, p)

    # Replicate dx[7] computation from core.rhs to get recovery_mode_gate
    stress_signal = smin(1.0, smax(0.0, 0.5 * V + 0.5 * a["S"]))
    recovery_bell = 4.0 * stress_signal * (1.0 - stress_signal)
    stress_overload = smax(0.0, stress_signal - p.stress_overload_threshold)
    dx7 = (
        p.alpha_rec * a["RecoveryDriver"] * (recovery_bell + 0.2) * (1.0 - R)
        - p.beta_rec_stress * stress_overload * R
    )
    recovery_mode_gate = float(smax(0.0, dx7) * p.gate_amp / (p.alpha_rec + EPSILON))

    # Pull decomposition
    pull_resilience = float(p.alpha_pos * R * a["SocialCapital"] * (1.0 - Inst))
    pull_recovery_gate = float(p.alpha_pos * R * a["SocialCapital"] * recovery_mode_gate * (1.0 - Inst))
    pull_mental_agency = float(p.alpha_pos * p.gamma_inst * M * G * (1.0 - Inst))
    pull_total = pull_resilience + pull_recovery_gate + pull_mental_agency

    # Drag decomposition  [4.2.1: structural decay now uses beta_sd, not beta_neg]
    drag_natural_decay = float(p.NaturalDecay * Inst)
    drag_corruption = float(p.beta_neg * a["Corruption"] * V * Inst)
    drag_structural_decay = float(p.beta_sd * a["StructuralDecay"] * Inst)
    drag_total = drag_natural_decay + drag_corruption + drag_structural_decay

    return {
        "pull_total": pull_total,
        "pull_resilience": pull_resilience,
        "pull_recovery_gate": pull_recovery_gate,
        "pull_mental_agency": pull_mental_agency,
        "drag_total": drag_total,
        "drag_natural_decay": drag_natural_decay,
        "drag_corruption": drag_corruption,
        "drag_structural_decay": drag_structural_decay,
        "net_dInst": pull_total - drag_total,
        "Corruption": float(a["Corruption"]),
        "StructuralDecay": float(a["StructuralDecay"]),
        "SocialCapital": float(a["SocialCapital"]),
        "recovery_mode_gate": recovery_mode_gate,
    }


def run_institutional_decomposition(
    output_dir: Path = Path("artifacts/diagnostics"),
    steps: int = 120,
    params=None,
) -> pd.DataFrame:
    """Run per-step institutional decomposition for all INST_SCENARIOS."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    p = params or default_params()
    rows: list[dict] = []

    for scenario in INST_SCENARIOS:
        bench = ForecastBenchmark(scenario_name=scenario)
        synth_steps = max(200, steps + 20)
        data = bench.generate_synthetic_data(n_steps=synth_steps)

        # Initial state from scenario's first data point
        x = bench._build_state(data, 0)

        for step in range(steps):
            t = step * DT
            A, Prod, Ch, M, G, V, Inst, R, F, P_ = x

            decomp = _decompose_inst(x, p)
            dx = rhs(x, p)
            dInst = float(dx[6])

            synth_idx = min(step, len(data["stress"]) - 1)
            synthetic_stress = float(data["stress"][synth_idx])

            rows.append({
                "scenario": scenario,
                "t": t,
                "Inst": float(Inst),
                "dInst": dInst,
                **decomp,
                "synthetic_stress": synthetic_stress,
            })

            # Advance state
            x = rk4_step(x, DT, p)
            x[:8] = np.clip(x[:8], 0.0, 1.0)
            x[8] = np.clip(x[8], 0.0, 4.0)
            x[9] = max(float(x[9]), 0.0)

    df = pd.DataFrame(rows)

    # Add phase labels per scenario
    phase_labels: list[str] = []
    for scenario in INST_SCENARIOS:
        sc_df = df[df["scenario"] == scenario].copy()
        labels = detect_phases(sc_df)
        phase_labels.extend(labels.tolist())
    df["phase_label"] = phase_labels

    outpath = output_dir / "institutional_loop_decomposition.csv"
    df.to_csv(outpath, index=False)

    # Print mean summary
    print("\n" + "=" * 80)
    print("Institutional Loop Decomposition -- Mean Values by Scenario")
    print("=" * 80)
    summary_cols = ["pull_total", "pull_resilience", "pull_recovery_gate",
                    "pull_mental_agency", "drag_total", "drag_natural_decay",
                    "drag_corruption", "drag_structural_decay"]
    agg = df.groupby("scenario")[summary_cols].mean()
    print(agg.round(5).to_string())

    print("\nDominant drag term per scenario:")
    drag_cols = ["drag_natural_decay", "drag_corruption", "drag_structural_decay"]
    for sc, row in agg.iterrows():
        dominant = max(drag_cols, key=lambda c: row[c])
        ratio = row["drag_total"] / (row["pull_total"] + 1e-12)
        print(f"  {sc:35s}: {dominant} (drag/pull ratio={ratio:.3f})")

    # Print per-scenario phase summary
    print("\n" + "=" * 80)
    print("Phase-level decomposition (mean per phase)")
    print("=" * 80)
    ps = phase_summary(df)
    print(ps.round(5).to_string(index=False))

    # Print recovery window stats for level_shift
    rw = recovery_window_stats(df, "level_shift_shock_recovery")
    print("\n" + "=" * 80)
    print("Recovery Window Stats — level_shift_shock_recovery")
    print("=" * 80)
    for k, v in rw.items():
        print(f"  {k}: {v}")

    print(f"\nSaved: {outpath}")
    return df


def recovery_gate_share_by_scenario(df: pd.DataFrame) -> dict[str, float]:
    """Return pull_recovery_gate share of pull_total per scenario (mean over all steps)."""
    result: dict[str, float] = {}
    for scenario, grp in df.groupby("scenario"):
        mean_gate = grp["pull_recovery_gate"].mean()
        mean_pull = grp["pull_total"].mean()
        result[str(scenario)] = float(mean_gate / (mean_pull + 1e-10))
    return result


def recovery_phase_stats(df: pd.DataFrame, scenario: str) -> dict:
    """Return stats for the recovery phase in a level_shift_shock_recovery scenario.

    Recovery phase is defined as steps where synthetic_stress < 0.5 AND t > 10
    (i.e., after the shock has passed).
    """
    grp = df[df["scenario"] == scenario].copy()
    if grp.empty:
        return {}
    recovery_phase = grp[(grp["t"] > 10.0) & (grp["synthetic_stress"] < 0.5)]
    if recovery_phase.empty:
        recovery_phase = grp[grp["t"] > grp["t"].max() * 0.5]  # fallback: second half
    return {
        "mean_dInst": float(recovery_phase["dInst"].mean()),
        "pull_gt_drag_fraction": float((recovery_phase["pull_total"] > recovery_phase["drag_total"]).mean()),
        "mean_gate_share": float(
            recovery_phase["pull_recovery_gate"].mean()
            / (recovery_phase["pull_total"].mean() + 1e-10)
        ),
        "min_drag_pull_ratio": float(
            (recovery_phase["drag_total"] / (recovery_phase["pull_total"] + 1e-10)).min()
        ),
    }


def detect_phases(df_scenario: pd.DataFrame) -> pd.Series:
    """Assign a phase label to each row of a single-scenario DataFrame.

    Columns expected: t, synthetic_stress, dInst, Inst.
    Phase labels:
      pre_shock        — early portion before stress peak
      shock            — from pre_shock end to Inst bottom
      recovery_window  — after Inst bottom, first half of remaining steps
      stabilization    — remaining steps after recovery_window
      quasi_equilibrium — for low-stress / saturation scenarios
    """
    if df_scenario.empty:
        return pd.Series([], dtype=str)

    stress = df_scenario["synthetic_stress"].values
    inst = df_scenario["Inst"].values
    t = df_scenario["t"].values

    # Low-stress / saturation: stress never peaks above 0.4
    if float(np.max(stress)) < 0.4:
        return pd.Series(["quasi_equilibrium"] * len(df_scenario), index=df_scenario.index)

    # Find t_stress_peak and t_inst_bottom
    t_stress_peak = float(t[int(np.argmax(stress))])
    # Look for Inst minimum after the stress peak if possible
    peak_idx = int(np.argmax(stress))
    post_peak_inst = inst[peak_idx:]
    if len(post_peak_inst) > 0:
        bottom_rel = int(np.argmin(post_peak_inst))
        t_inst_bottom = float(t[peak_idx + bottom_rel])
    else:
        t_inst_bottom = float(t[int(np.argmin(inst))])

    t_max = float(t[-1])
    recovery_end = t_inst_bottom + (t_max - t_inst_bottom) * 0.5

    labels = []
    for ti in t:
        if ti < t_stress_peak * 0.3:
            labels.append("pre_shock")
        elif ti <= t_inst_bottom:
            labels.append("shock")
        elif ti <= recovery_end:
            labels.append("recovery_window")
        else:
            labels.append("stabilization")
    return pd.Series(labels, index=df_scenario.index)


def recovery_window_stats(df: pd.DataFrame, scenario: str) -> dict:
    """Return recovery-window statistics for a specific scenario.

    Requires phase_label column to be present in df.
    """
    grp = df[(df["scenario"] == scenario) & (df["phase_label"] == "recovery_window")].copy()
    if grp.empty:
        return {
            "window_exists": False,
            "window_length": 0,
            "mean_dInst_in_window": float("nan"),
            "pull_gt_drag_fraction": 0.0,
            "gate_share_in_window": 0.0,
            "inst_change": 0.0,
        }

    dInst_vals = grp["dInst"].values
    # Count consecutive positive dInst steps
    max_run = 0
    cur_run = 0
    for v in dInst_vals:
        if v > 0:
            cur_run += 1
            max_run = max(max_run, cur_run)
        else:
            cur_run = 0

    window_exists = max_run >= 3
    window_length = int(np.sum(dInst_vals > 0))
    mean_dInst_in_window = float(np.mean(dInst_vals))
    pull_gt_drag = float(np.mean(grp["pull_total"].values > grp["drag_total"].values))
    gate_share = float(
        grp["pull_recovery_gate"].mean() / (grp["pull_total"].mean() + 1e-10)
    )
    inst_change = float(grp["Inst"].iloc[-1] - grp["Inst"].iloc[0])

    return {
        "window_exists": window_exists,
        "window_length": window_length,
        "mean_dInst_in_window": mean_dInst_in_window,
        "pull_gt_drag_fraction": pull_gt_drag,
        "gate_share_in_window": gate_share,
        "inst_change": inst_change,
    }


def phase_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Group by (scenario, phase_label) and return means of key columns."""
    cols = ["pull_total", "drag_total", "dInst", "pull_recovery_gate", "Inst"]
    agg = df.groupby(["scenario", "phase_label"])[cols].mean().reset_index()
    agg["gate_share"] = agg["pull_recovery_gate"] / (agg["pull_total"] + 1e-10)
    return agg


def main() -> int:
    parser = argparse.ArgumentParser(description="Institutional loop decomposition diagnostics")
    parser.add_argument("--steps", type=int, default=120)
    parser.add_argument("--output-dir", default="artifacts/diagnostics")
    args = parser.parse_args()
    run_institutional_decomposition(
        output_dir=Path(args.output_dir),
        steps=args.steps,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

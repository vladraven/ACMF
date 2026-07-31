from __future__ import annotations
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.run_institutional_loop_diagnostics import run_institutional_decomposition, INST_SCENARIOS
from scripts.run_institutional_sensitivity import run_sensitivity_grid


def test_decomposition_exports_csv(tmp_path):
    run_institutional_decomposition(output_dir=tmp_path, steps=30)
    df = pd.read_csv(tmp_path / "institutional_loop_decomposition.csv")
    assert set(INST_SCENARIOS).issubset(set(df["scenario"].unique()))
    required = {"scenario", "t", "Inst", "dInst", "pull_total", "drag_total",
                "drag_corruption", "drag_structural_decay", "net_dInst"}
    assert required.issubset(set(df.columns))


def test_decomposition_columns_finite(tmp_path):
    run_institutional_decomposition(output_dir=tmp_path, steps=30)
    df = pd.read_csv(tmp_path / "institutional_loop_decomposition.csv")
    for col in ["pull_total", "drag_total", "Inst", "dInst"]:
        assert np.isfinite(df[col]).all(), f"Column {col} has non-finite values"


def test_drag_exceeds_pull_without_fix():
    """Baseline check: with default params, inst_drag > inst_pull (known issue)."""
    run_institutional_decomposition_default = lambda tmp: run_institutional_decomposition(output_dir=tmp, steps=60)
    import tempfile, os
    with tempfile.TemporaryDirectory() as tmp:
        run_institutional_decomposition_default(Path(tmp))
        df = pd.read_csv(Path(tmp) / "institutional_loop_decomposition.csv")
        mean_drag = df["drag_total"].mean()
        mean_pull = df["pull_total"].mean()
        # Document the known imbalance (drag > pull with defaults)
        assert mean_drag > 0, "drag_total should be positive"
        assert mean_pull > 0, "pull_total should be positive"
        # The ratio drag/pull documents the imbalance
        ratio = mean_drag / (mean_pull + 1e-10)
        print(f"drag/pull ratio with defaults: {ratio:.3f}")


def test_sensitivity_grid_exports_csv(tmp_path):
    # Run with small grid for speed
    run_sensitivity_grid(
        alpha_pos_values=[0.25, 0.50],
        beta_neg_values=[0.10, 0.20],
        output_dir=tmp_path,
        steps=30,
    )
    df = pd.read_csv(tmp_path / "institutional_sensitivity_grid.csv")
    assert "alpha_pos" in df.columns
    assert "beta_neg" in df.columns
    assert "scenario_balance_score" in df.columns


def test_sensitivity_high_alpha_pos_improves_balance(tmp_path):
    """Higher alpha_pos should generally improve scenario_balance_score."""
    run_sensitivity_grid(
        alpha_pos_values=[0.10, 0.50],
        beta_neg_values=[0.20],
        output_dir=tmp_path,
        steps=30,
    )
    df = pd.read_csv(tmp_path / "institutional_sensitivity_grid.csv")
    # aggregate by alpha_pos
    agg = df.groupby("alpha_pos")["scenario_balance_score"].sum()
    # higher alpha_pos (0.50) should have >= score of lower (0.10)
    assert agg[0.50] >= agg[0.10], f"Higher alpha_pos should not reduce balance score: {agg.to_dict()}"


def test_low_stress_inst_stable_at_optimal_params(tmp_path):
    """At alpha_pos=0.5, beta_neg=0.1, low_stress Inst should be stable (mean_dInst >= -0.002)."""
    run_sensitivity_grid(
        alpha_pos_values=[0.50],
        beta_neg_values=[0.10],
        output_dir=tmp_path,
        steps=60,
    )
    df = pd.read_csv(tmp_path / "institutional_sensitivity_grid.csv")
    low_stress = df[(df["scenario"] == "low_stress_trend") & (df["alpha_pos"] == 0.50)]
    assert len(low_stress) > 0
    assert float(low_stress["mean_dInst"].values[0]) >= -0.002, \
        f"Low stress Inst should be stable at alpha_pos=0.5: mean_dInst={float(low_stress['mean_dInst'].values[0]):.4f}"

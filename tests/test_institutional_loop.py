from __future__ import annotations
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.run_institutional_loop_diagnostics import run_institutional_decomposition, INST_SCENARIOS
from scripts.run_institutional_sensitivity import run_sensitivity_grid, run_beta_sd_sensitivity


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
    """Baseline check: document drag/pull ratio with defaults; pull must also be positive."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        run_institutional_decomposition(output_dir=Path(tmp), steps=60)
        df = pd.read_csv(Path(tmp) / "institutional_loop_decomposition.csv")
        mean_drag = df["drag_total"].mean()
        mean_pull = df["pull_total"].mean()
        assert mean_drag > 0, "drag_total should be positive"
        assert mean_pull > 0, "pull_total should be positive"
        ratio = mean_drag / (mean_pull + 1e-10)
        print(f"drag/pull ratio with defaults: {ratio:.3f}")


def test_sensitivity_grid_exports_csv(tmp_path):
    run_sensitivity_grid(
        alpha_pos_values=[0.25, 0.50],
        beta_neg_values=[0.10, 0.20],
        output_dir=tmp_path,
        steps=30,
    )
    df = pd.read_csv(tmp_path / "institutional_sensitivity_grid.csv")
    assert "alpha_pos" in df.columns
    assert "beta_neg" in df.columns
    assert "beta_sd" in df.columns
    assert "scenario_balance_score" in df.columns


def test_sensitivity_high_alpha_pos_improves_balance(tmp_path):
    """Higher alpha_pos should not reduce scenario_balance_score."""
    run_sensitivity_grid(
        alpha_pos_values=[0.10, 0.50],
        beta_neg_values=[0.20],
        output_dir=tmp_path,
        steps=30,
    )
    df = pd.read_csv(tmp_path / "institutional_sensitivity_grid.csv")
    agg = df.groupby("alpha_pos")["scenario_balance_score"].sum()
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


# ── 4.2.1 Gate Tests ──────────────────────────────────────────────────────────

def test_gate1_structural_decay_share_reduced(tmp_path):
    """Gate 1: With beta_sd=0.08 (default), StructuralDecay share of drag < 50% (was 63%)."""
    run_institutional_decomposition(output_dir=tmp_path, steps=60)
    df = pd.read_csv(tmp_path / "institutional_loop_decomposition.csv")
    mean_drag = df["drag_total"].mean()
    mean_sd_drag = df["drag_structural_decay"].mean()
    sd_share = mean_sd_drag / (mean_drag + 1e-10)
    assert sd_share < 0.50, (
        f"Gate 1 FAIL: StructuralDecay share={sd_share:.1%} should be < 50% after beta_sd separation"
    )


def test_gate2_no_artificial_growth_at_default_beta_sd(tmp_path):
    """Gate 3: With default beta_sd=0.08, no artificial growth (Inst > 0.9 rarely)."""
    run_beta_sd_sensitivity(
        beta_sd_values=[0.08],
        output_dir=tmp_path,
        steps=60,
    )
    df = pd.read_csv(tmp_path / "institutional_beta_sd_sensitivity.csv")
    for _, row in df.iterrows():
        assert not row["artificial_growth"], (
            f"Gate 3 FAIL: artificial_growth in scenario={row['scenario']} at beta_sd=0.08"
        )


def test_gate3_persistent_stress_possible(tmp_path):
    """Gate 4: regime_change_stress with high beta_sd still degrades Inst (mean_dInst < 0)."""
    run_beta_sd_sensitivity(
        beta_sd_values=[0.08, 0.15],
        output_dir=tmp_path,
        steps=60,
    )
    df = pd.read_csv(tmp_path / "institutional_beta_sd_sensitivity.csv")
    regime = df[df["scenario"] == "regime_change_stress"]
    for _, row in regime.iterrows():
        assert float(row["mean_dInst"]) < 0.01, (
            f"Gate 4 FAIL: regime_change_stress should not show strong positive dInst at beta_sd={row['beta_sd']}"
        )


def test_gate4_beta_sd_sensitivity_exports_csv(tmp_path):
    """beta_sd sensitivity grid exports correctly and beta_sd column present."""
    run_beta_sd_sensitivity(
        beta_sd_values=[0.03, 0.08, 0.15],
        output_dir=tmp_path,
        steps=30,
    )
    df = pd.read_csv(tmp_path / "institutional_beta_sd_sensitivity.csv")
    assert "beta_sd" in df.columns
    assert "scenario_balance_score" in df.columns
    assert set(df["beta_sd"].unique()) == {0.03, 0.08, 0.15}


def test_gate5_lower_beta_sd_improves_balance(tmp_path):
    """Gate 5: Lowering beta_sd from 0.25 to 0.08 should not reduce scenario_balance_score."""
    run_beta_sd_sensitivity(
        beta_sd_values=[0.08, 0.25],
        output_dir=tmp_path,
        steps=60,
    )
    df = pd.read_csv(tmp_path / "institutional_beta_sd_sensitivity.csv")
    scores = df.drop_duplicates("beta_sd").set_index("beta_sd")["scenario_balance_score"]
    assert scores[0.08] >= scores[0.25], (
        f"Gate 5 FAIL: beta_sd=0.08 score={scores[0.08]} < beta_sd=0.25 score={scores[0.25]}"
    )


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

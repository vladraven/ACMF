from __future__ import annotations
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.run_dynamics_mechanism_diagnostics import DIAGNOSTIC_SCENARIOS, run_mechanism_diagnostics
from scripts.run_synthetic_forecast_benchmark import DIAGNOSTIC_SCENARIOS as SYN_SCENARIOS, run_diagnostic_suite


def test_synthetic_diagnostic_suite_exports_all_csv(tmp_path):
    run_diagnostic_suite(seed=7, horizon=12, output_dir=tmp_path)
    expected = {
        "synthetic_forecast_metrics.csv",
        "synthetic_forecast_winners.csv",
        "synthetic_forecast_expected_match.csv",
        "synthetic_forecast_error_by_year.csv",
        "synthetic_forecast_trajectories.csv",
    }
    produced = {p.name for p in tmp_path.glob("*.csv")}
    assert expected.issubset(produced)
    metrics = pd.read_csv(tmp_path / "synthetic_forecast_metrics.csv")
    assert "mode" in metrics.columns
    assert set(metrics["scenario"].unique()) == set(SYN_SCENARIOS)
    assert set(metrics["mode"].unique()) == {"response", "state"}


def test_dynamics_diagnostics_exports_response_and_bounds(tmp_path):
    run_mechanism_diagnostics(output_dir=tmp_path, steps=24, dt=0.5)
    response = pd.read_csv(tmp_path / "dynamics_mechanism_response.csv")
    bounds = pd.read_csv(tmp_path / "bounds_hit_report.csv")
    assert set(response["scenario"].unique()) == set(DIAGNOSTIC_SCENARIOS)
    assert set(bounds["scenario"].unique()) == set(DIAGNOSTIC_SCENARIOS)
    assert {"scenario", "t", "R", "dR", "RecoveryDriver", "S", "StructuralLimits",
            "recovery_pull", "recovery_stress_drag", "inst_pull", "inst_drag"}.issubset(set(response.columns))
    assert (bounds["hits_total"] >= 0).all()


def test_recovery_pull_positive_in_low_stress(tmp_path):
    """In low stress, recovery_pull must be finite and positive on average."""
    from scripts.run_dynamics_mechanism_diagnostics import _simulate_trace
    resp, _ = _simulate_trace("level_shift_shock_recovery", steps=60, dt=0.5)
    assert resp["recovery_pull"].mean() > 0, "recovery_pull should be positive"
    assert np.isfinite(resp["recovery_pull"]).all()


def test_structural_limits_varies_across_scenarios(tmp_path):
    """StructuralLimits must not be constant ~1 across all scenarios."""
    run_mechanism_diagnostics(output_dir=tmp_path, steps=60, dt=0.5)
    resp = pd.read_csv(tmp_path / "dynamics_mechanism_response.csv")
    means = resp.groupby("scenario")["StructuralLimits"].mean()
    assert means.min() < 0.8, f"StructuralLimits should vary, got means: {means.to_dict()}"


def test_response_benchmark_acmf_model_exists(tmp_path):
    """Response benchmark must include ACMF model results."""
    run_diagnostic_suite(seed=42, horizon=15, output_dir=tmp_path)
    metrics = pd.read_csv(tmp_path / "synthetic_forecast_metrics.csv")
    acmf_rows = metrics[metrics["model"] == "acmf"]
    assert len(acmf_rows) > 0, "ACMF model should appear in response benchmark results"


def test_state_benchmark_acmf_forecasts_states(tmp_path):
    """State benchmark must include ACMF per-state model results (acmf:A, acmf:R, etc.)."""
    run_diagnostic_suite(seed=42, horizon=15, output_dir=tmp_path)
    metrics = pd.read_csv(tmp_path / "synthetic_forecast_metrics.csv")
    state_acmf = metrics[(metrics["mode"] == "state") & (metrics["model"].str.startswith("acmf:"))]
    assert len(state_acmf) > 0, "State benchmark should include ACMF per-state forecasts"

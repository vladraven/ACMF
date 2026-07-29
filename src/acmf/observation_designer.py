from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Sequence, List
import math
import numpy as np
import pandas as pd

from .calibration import LossConfig
from .identifiability import (
    parameter_sensitivity_matrix,
    fisher_information_matrix,
    fim_diagnostics,
    parameter_correlation_from_fim,
    top_correlated_pairs,
)
from .world_panel import load_world_panel, make_acmf_proxy_panel

DEFAULT_THETA = np.array([0.8, 0.5, 0.3, 0.08, 0.2, 0.4, 0.6, 0.03, 0.5, 0.5, 0.5, 0.5])
DEFAULT_BASE_OBSERVABLES = ["P", "Prod", "A", "Inst", "F"]
DEFAULT_CANDIDATE_OBSERVABLES = ["Ch", "M", "G", "V", "R"]


@dataclass
class ObservationDesignResult:
    selected_observables: List[str]
    candidate_scores: pd.DataFrame
    history: pd.DataFrame
    final_rank: int
    final_condition_number: float
    final_min_eigenvalue: float
    weak_directions: List[Dict]
    top_correlated_pairs: List[Dict]


def _diag_for_observables(data: Dict[str, np.ndarray], theta: Sequence[float], observables: Sequence[str],
                          config: LossConfig | None = None, noise_std: float = 1.0, ridge: float = 1e-12):
    cfg = config or LossConfig(observed_vars=list(observables), lambda_prior=0.0)
    res = parameter_sensitivity_matrix(data, theta, observables, cfg)
    F = fisher_information_matrix(res.S, noise_std=noise_std, ridge=ridge)
    diag = fim_diagnostics(F, res.parameter_names)
    corr = parameter_correlation_from_fim(F)
    return res, F, diag, corr


def _safe_logdet_eig(eigenvalues: np.ndarray, eps: float = 1e-12) -> float:
    vals = np.asarray(eigenvalues, dtype=float)
    vals = vals[np.isfinite(vals)]
    if vals.size == 0:
        return float("-inf")
    vals = np.maximum(vals, eps)
    return float(np.sum(np.log(vals)))


def score_candidate_observables(
    data: Dict[str, np.ndarray],
    theta: Sequence[float],
    base_observables: Sequence[str],
    candidate_observables: Sequence[str],
    config: LossConfig | None = None,
    noise_std: float = 1.0,
    ridge: float = 1e-12,
) -> pd.DataFrame:
    """Score one-step gains from adding each candidate observable.

    The ranking combines model-level practical identifiability metrics:
    rank gain, min-eigenvalue gain, logdet gain, and condition-number gain.
    """
    base_observables = list(dict.fromkeys(base_observables))
    _, _, base_diag, _ = _diag_for_observables(data, theta, base_observables, config, noise_std, ridge)
    base_logdet = _safe_logdet_eig(base_diag.eigenvalues)
    rows = []
    for obs in candidate_observables:
        if obs in base_observables:
            continue
        trial = base_observables + [obs]
        _, _, diag, _ = _diag_for_observables(data, theta, trial, config, noise_std, ridge)
        cond_gain = np.nan
        if np.isfinite(base_diag.condition_number) and np.isfinite(diag.condition_number) and diag.condition_number > 0:
            cond_gain = float(base_diag.condition_number / diag.condition_number)
        min_eig_gain = float(diag.min_eigenvalue - base_diag.min_eigenvalue)
        rank_gain = int(diag.rank - base_diag.rank)
        logdet_gain = float(_safe_logdet_eig(diag.eigenvalues) - base_logdet)
        # Composite score: lexicographic-friendly continuous rank. Rank gain dominates,
        # then logdet/min-eig/condition improvements.
        score = (rank_gain * 1e6) + logdet_gain + math.log1p(max(cond_gain, 0.0) if np.isfinite(cond_gain) else 0.0) + math.log1p(max(min_eig_gain, 0.0))
        rows.append({
            "candidate": obs,
            "trial_observables": trial,
            "rank": diag.rank,
            "rank_gain": rank_gain,
            "condition_number": diag.condition_number,
            "condition_gain": cond_gain,
            "min_eigenvalue": diag.min_eigenvalue,
            "min_eigenvalue_gain": min_eig_gain,
            "logdet": _safe_logdet_eig(diag.eigenvalues),
            "logdet_gain": logdet_gain,
            "score": float(score),
        })
    if not rows:
        return pd.DataFrame(columns=["candidate", "score"])
    return pd.DataFrame(rows).sort_values(["rank_gain", "score", "condition_gain"], ascending=[False, False, False]).reset_index(drop=True)


def greedy_observation_design(
    data: Dict[str, np.ndarray],
    theta: Sequence[float] = DEFAULT_THETA,
    base_observables: Sequence[str] = DEFAULT_BASE_OBSERVABLES,
    candidate_observables: Sequence[str] = DEFAULT_CANDIDATE_OBSERVABLES,
    k: int = 1,
    config: LossConfig | None = None,
    noise_std: float = 1.0,
    ridge: float = 1e-12,
) -> ObservationDesignResult:
    """Greedily select k observables that improve practical identifiability."""
    selected = list(dict.fromkeys(base_observables))
    remaining = [o for o in candidate_observables if o not in selected]
    history_rows = []
    last_scores = pd.DataFrame()
    for step in range(int(k)):
        if not remaining:
            break
        scores = score_candidate_observables(data, theta, selected, remaining, config, noise_std, ridge)
        last_scores = scores
        if scores.empty:
            break
        best = scores.iloc[0].to_dict()
        selected.append(best["candidate"])
        remaining = [o for o in remaining if o != best["candidate"]]
        best["step"] = step + 1
        best["selected_after_step"] = selected.copy()
        history_rows.append(best)
    _, F, final_diag, corr = _diag_for_observables(data, theta, selected, config, noise_std, ridge)
    pairs = top_correlated_pairs(corr, final_diag.parameter_names, threshold=0.85)
    return ObservationDesignResult(
        selected_observables=selected,
        candidate_scores=last_scores,
        history=pd.DataFrame(history_rows),
        final_rank=final_diag.rank,
        final_condition_number=final_diag.condition_number,
        final_min_eigenvalue=final_diag.min_eigenvalue,
        weak_directions=final_diag.weak_directions,
        top_correlated_pairs=pairs,
    )


def minimal_observation_set(
    data: Dict[str, np.ndarray],
    theta: Sequence[float] = DEFAULT_THETA,
    required_observables: Sequence[str] = ("P",),
    candidate_observables: Sequence[str] = ("Prod", "A", "Inst", "F", "Ch", "M", "G", "V", "R"),
    target_rank: int | None = None,
    max_condition_number: float | None = None,
    min_eigenvalue_floor: float | None = None,
    max_observables: int | None = None,
    config: LossConfig | None = None,
    noise_std: float = 1.0,
    ridge: float = 1e-12,
) -> ObservationDesignResult:
    """Find a small observation set satisfying identifiability thresholds if possible."""
    selected = list(dict.fromkeys(required_observables))
    remaining = [o for o in candidate_observables if o not in selected]
    history_rows = []
    target_rank = int(target_rank or len(DEFAULT_THETA))
    limit = max_observables or (len(selected) + len(remaining))
    while len(selected) < limit:
        _, _, diag, corr = _diag_for_observables(data, theta, selected, config, noise_std, ridge)
        cond_ok = max_condition_number is None or (np.isfinite(diag.condition_number) and diag.condition_number <= max_condition_number)
        eig_ok = min_eigenvalue_floor is None or diag.min_eigenvalue >= min_eigenvalue_floor
        if diag.rank >= target_rank and cond_ok and eig_ok:
            break
        if not remaining:
            break
        scores = score_candidate_observables(data, theta, selected, remaining, config, noise_std, ridge)
        if scores.empty:
            break
        best = scores.iloc[0].to_dict()
        selected.append(best["candidate"])
        remaining = [o for o in remaining if o != best["candidate"]]
        best["step"] = len(history_rows) + 1
        best["selected_after_step"] = selected.copy()
        history_rows.append(best)
    final_scores = score_candidate_observables(data, theta, selected, remaining, config, noise_std, ridge) if remaining else pd.DataFrame()
    _, _, final_diag, corr = _diag_for_observables(data, theta, selected, config, noise_std, ridge)
    return ObservationDesignResult(
        selected_observables=selected,
        candidate_scores=final_scores,
        history=pd.DataFrame(history_rows),
        final_rank=final_diag.rank,
        final_condition_number=final_diag.condition_number,
        final_min_eigenvalue=final_diag.min_eigenvalue,
        weak_directions=final_diag.weak_directions,
        top_correlated_pairs=top_correlated_pairs(corr, final_diag.parameter_names, threshold=0.85),
    )


def design_for_world_panel_country(
    country: str,
    data_path: str | None = None,
    start_year: int = 1995,
    end_year: int = 2024,
    k: int = 5,
    base_observables: Sequence[str] = DEFAULT_BASE_OBSERVABLES,
    candidate_observables: Sequence[str] = DEFAULT_CANDIDATE_OBSERVABLES,
    theta: Sequence[float] = DEFAULT_THETA,
) -> ObservationDesignResult:
    """Run greedy observation design on ACMF proxy observations for one country."""
    df = load_world_panel(data_path)
    data = make_acmf_proxy_panel(df, country, start_year=start_year, end_year=end_year)
    return greedy_observation_design(data, theta=theta, base_observables=base_observables, candidate_observables=candidate_observables, k=k)


def result_to_dict(result: ObservationDesignResult) -> dict:
    return {
        "selected_observables": result.selected_observables,
        "history": result.history.to_dict(orient="records"),
        "candidate_scores": result.candidate_scores.to_dict(orient="records") if not result.candidate_scores.empty else [],
        "final_rank": result.final_rank,
        "final_condition_number": result.final_condition_number,
        "final_min_eigenvalue": result.final_min_eigenvalue,
        "weak_directions": result.weak_directions[:5],
        "top_correlated_pairs": result.top_correlated_pairs[:10],
    }

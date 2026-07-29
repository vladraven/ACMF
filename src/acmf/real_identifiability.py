from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Sequence, List
import json
import numpy as np
import pandas as pd

from .calibration import LossConfig
from .identifiability import (
    parameter_sensitivity_matrix,
    fisher_information_matrix,
    fim_diagnostics,
    parameter_correlation_from_fim,
    top_correlated_pairs,
    observation_design_score,
)
from .observation_designer import (
    DEFAULT_THETA,
    DEFAULT_BASE_OBSERVABLES,
    DEFAULT_CANDIDATE_OBSERVABLES,
    greedy_observation_design,
    minimal_observation_set,
    result_to_dict,
)
from .world_panel import load_world_panel, make_acmf_proxy_panel
from .data_fetchers.world_bank import complete_data_year

PARAMETER_NAMES = ['alpha7','K_g','beta_neg','NaturalDecay','q1','q3','alpha1','b1','Ch0','M0','G0','R0']
DEFAULT_REAL_COUNTRIES = ['Canada', 'Germany', 'Japan', 'Korea, Rep.', 'Australia']


@dataclass
class CountryIdentifiabilityReport:
    country: str
    start_year: int
    end_year: int
    observables: List[str]
    rank: int
    condition_number: float
    min_eigenvalue: float
    max_eigenvalue: float
    weak_directions: List[Dict]
    top_correlated_pairs: List[Dict]
    observation_design_gain: List[Dict]
    greedy_design: Dict
    minimal_design: Dict


def _json_safe(value):
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if isinstance(value, tuple):
        return [_json_safe(v) for v in value]
    if isinstance(value, np.ndarray):
        return _json_safe(value.tolist())
    if isinstance(value, (np.floating, float)):
        x = float(value)
        if np.isnan(x):
            return None
        if np.isposinf(x):
            return 'Infinity'
        if np.isneginf(x):
            return '-Infinity'
        return x
    if isinstance(value, (np.integer, int)):
        return int(value)
    return value


def analyze_country_identifiability(
    panel_df: pd.DataFrame,
    country: str,
    start_year: int = 1995,
    end_year: int | None = None,
    theta: Sequence[float] = DEFAULT_THETA,
    base_observables: Sequence[str] = DEFAULT_BASE_OBSERVABLES,
    candidate_observables: Sequence[str] = DEFAULT_CANDIDATE_OBSERVABLES,
    design_k: int = 3,
    target_rank: int | None = None,
    max_observables: int = 10,
    noise_std: float = 1.0,
    ridge: float = 1e-12,
) -> CountryIdentifiabilityReport:
    end_year = int(end_year if end_year is not None else complete_data_year())
    data = make_acmf_proxy_panel(panel_df, country, start_year=start_year, end_year=end_year)
    obs = list(base_observables)
    cfg = LossConfig(observed_vars=obs, lambda_prior=0.0)
    sens = parameter_sensitivity_matrix(data, theta, obs, cfg)
    F = fisher_information_matrix(sens.S, noise_std=noise_std, ridge=ridge)
    diag = fim_diagnostics(F, sens.parameter_names)
    corr = parameter_correlation_from_fim(F)
    design_gain = observation_design_score(data, theta, obs, list(candidate_observables), cfg, noise_std=noise_std)
    greedy = greedy_observation_design(data, theta=theta, base_observables=obs, candidate_observables=candidate_observables, k=design_k, noise_std=noise_std, ridge=ridge)
    minimal = minimal_observation_set(
        data,
        theta=theta,
        required_observables=['P'],
        candidate_observables=['Prod','A','Inst','F','Ch','M','G','V','R'],
        target_rank=target_rank or len(theta),
        max_observables=max_observables,
        noise_std=noise_std,
        ridge=ridge,
    )
    return CountryIdentifiabilityReport(
        country=country,
        start_year=int(data['t'][0]),
        end_year=int(data['t'][-1]),
        observables=obs,
        rank=diag.rank,
        condition_number=diag.condition_number,
        min_eigenvalue=diag.min_eigenvalue,
        max_eigenvalue=diag.max_eigenvalue,
        weak_directions=diag.weak_directions[:5],
        top_correlated_pairs=top_correlated_pairs(corr, sens.parameter_names, threshold=0.85)[:10],
        observation_design_gain=design_gain,
        greedy_design=result_to_dict(greedy),
        minimal_design=result_to_dict(minimal),
    )


def report_to_dict(report: CountryIdentifiabilityReport) -> dict:
    return _json_safe(report.__dict__)


def build_real_identifiability_report(
    countries: Sequence[str] = DEFAULT_REAL_COUNTRIES,
    data_path: str | Path | None = None,
    start_year: int = 1995,
    end_year: int | None = None,
    design_k: int = 3,
    target_rank: int | None = None,
    max_observables: int = 10,
) -> dict:
    end_year = int(end_year if end_year is not None else complete_data_year())
    panel = load_world_panel(data_path)
    reports = []
    errors = []
    for country in countries:
        try:
            rep = analyze_country_identifiability(
                panel,
                country,
                start_year=start_year,
                end_year=end_year,
                design_k=design_k,
                target_rank=target_rank,
                max_observables=max_observables,
            )
            reports.append(report_to_dict(rep))
        except Exception as exc:
            errors.append({'country': country, 'error': str(exc)})
    summary = summarize_real_identifiability(reports)
    return _json_safe({
        'dataset': str(data_path) if data_path else 'bundled world panel',
        'start_year': int(start_year),
        'end_year': int(end_year),
        'countries': list(countries),
        'summary': summary,
        'reports': reports,
        'errors': errors,
    })


def summarize_real_identifiability(reports: Sequence[dict]) -> dict:
    if not reports:
        return {'n_countries': 0}
    rows = []
    weak_counts: Dict[str, int] = {}
    added_counts: Dict[str, int] = {}
    for r in reports:
        rows.append({
            'country': r['country'],
            'rank': r['rank'],
            'condition_number': r['condition_number'],
            'min_eigenvalue': r['min_eigenvalue'],
            'greedy_selected': r.get('greedy_design', {}).get('selected_observables', []),
            'minimal_selected': r.get('minimal_design', {}).get('selected_observables', []),
        })
        for wd in r.get('weak_directions', [])[:3]:
            for load in wd.get('top_loadings', [])[:2]:
                p = load.get('parameter')
                if p:
                    weak_counts[p] = weak_counts.get(p, 0) + 1
        selected = r.get('greedy_design', {}).get('selected_observables', [])
        base = set(DEFAULT_BASE_OBSERVABLES)
        for obs in selected:
            if obs not in base:
                added_counts[obs] = added_counts.get(obs, 0) + 1
    df = pd.DataFrame(rows)
    return {
        'n_countries': int(len(reports)),
        'full_rank_countries': int((df['rank'] >= len(DEFAULT_THETA)).sum()) if 'rank' in df else 0,
        'rank_min': int(df['rank'].min()) if 'rank' in df else None,
        'rank_max': int(df['rank'].max()) if 'rank' in df else None,
        'condition_number_median': float(df['condition_number'].median()) if 'condition_number' in df else None,
        'min_eigenvalue_median': float(df['min_eigenvalue'].median()) if 'min_eigenvalue' in df else None,
        'most_common_weak_parameters': sorted(weak_counts.items(), key=lambda x: x[1], reverse=True),
        'most_common_added_observables': sorted(added_counts.items(), key=lambda x: x[1], reverse=True),
        'country_table': rows,
    }


def save_real_identifiability_report(report: dict, output: str | Path) -> Path:
    p = Path(output)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(_json_safe(report), indent=2), encoding='utf-8')
    return p

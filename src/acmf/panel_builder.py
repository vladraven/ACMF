from __future__ import annotations
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Iterable, Sequence
import json
import pandas as pd
import numpy as np
import yaml

from .data_fetchers.world_bank import complete_data_year, fetch_world_bank

ID_COLUMNS = ['country_name', 'country_code', 'Year']

ID_TO_COLUMN = {
    'POP':'Population','BIRTH':'Birth_rate','DEATH':'Death_rate','MIGR':'Net_migration','GDPC':'GDP_per_capita','GDPG':'GDP_growth','INFL':'Inflation','UNEMP':'Unemployment','LIFE':'Life_expectancy','URBAN':'Urbanization_pct','ENERGY_PC':'Energy_consumption_per_capita','CO2_PC':'CO2_per_capita','INTERNET':'Internet_penetration','ELECTRICITY':'Electricity_access','SCHOOL_ENROLL':'Primary_school_enrollment','PATENTS':'Patent_activity','RD_EXP':'RD_expenditure_pct_GDP',
    # Extended World Bank IDs may be present only after a fresh fetch.
    'HIGHTECH_X':'HIGHTECH_X','SCI_PAPERS':'SCI_PAPERS','RESEARCHERS':'RESEARCHERS','LFPR':'LFPR','YOUTH_UNEMP':'YOUTH_UNEMP','WORKING_AGE_EMP':'WORKING_AGE_EMP','SELF_EMP':'SELF_EMP','NEW_BUS':'NEW_BUS','BUSINESS_FORMATIONS':'BUSINESS_FORMATIONS','EODB':'EODB','GINI':'GINI','FISCAL_BUFFER':'FISCAL_BUFFER','FOREX_RESERVES':'FOREX_RESERVES',
}

BUDGET_ALIASES = {'minimal':'Minimal','standard':'Standard','comprehensive':'Comprehensive','unlimited':'Unlimited'}

@dataclass
class PanelBuildResult:
    panel: pd.DataFrame
    selected_indicators: pd.DataFrame
    quality_report: pd.DataFrame
    metadata: dict
    output_path: Path | None = None


def default_metadata_path() -> Path:
    try:
        return Path(resources.files('acmf.data').joinpath('indicators.yaml'))
    except Exception:
        return Path('data/metadata/indicators.yaml')


def default_level1_data_path() -> Path:
    candidates = [Path('data/world_data_level1_1995_2025.csv'), Path('data/world_data_1995_2025.csv')]
    for c in candidates:
        if c.exists():
            return c
    try:
        return Path(resources.files('acmf.data').joinpath('world_data_level1_1995_2025.csv'))
    except Exception:
        return Path(resources.files('acmf.data').joinpath('world_data_1995_2025.csv'))


def parse_year_range(years: str | tuple[int, int | None] | None, current_year: int | None = None) -> tuple[int, int]:
    if years is None:
        return (1995, complete_data_year(current_year))
    if isinstance(years, tuple):
        start, end = years
        return (int(start), int(end if end is not None else complete_data_year(current_year)))
    if ':' not in years:
        y = int(years)
        return (y, y)
    start_s, end_s = years.split(':', 1)
    start = int(start_s)
    end = complete_data_year(current_year) if end_s.strip().lower() in {'', 'complete', 'auto'} else int(end_s)
    return (start, end)


def load_metadata(path: str | Path | None = None) -> dict:
    p = Path(path) if path is not None else default_metadata_path()
    with open(p, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_indicator_df(metadata: dict) -> pd.DataFrame:
    rows = []
    for ind in metadata.get('indicators', []):
        row = dict(ind)
        row['oed_score'] = compute_oed_score(row)
        row['column'] = ID_TO_COLUMN.get(row['id'], row['id'])
        rows.append(row)
    return pd.DataFrame(rows)


def compute_oed_score(row: dict | pd.Series) -> float:
    return float(row['ovi']) * float(row['coverage']) * (float(row['quality']) / 5.0) / float(row['cost'])


def _budget_value(metadata: dict, budget: str | int | float) -> float:
    if isinstance(budget, (int, float)):
        return float(budget)
    target = BUDGET_ALIASES.get(str(budget).lower(), str(budget))
    for b in metadata.get('experimental_design', {}).get('budget_scenarios', []):
        if b.get('name') == target:
            return float(b['total_budget'])
    raise ValueError(f'Unknown budget scenario: {budget}')


def select_indicators(ind_df: pd.DataFrame, metadata: dict, budget='standard', required_constructs: Sequence[str] | None = None, require_level1=True) -> pd.DataFrame:
    total_budget = _budget_value(metadata, budget)
    df = ind_df.copy().sort_values('oed_score', ascending=False)
    selected = []
    selected_ids = set()
    spent = 0.0
    if require_level1:
        for _, row in df[df['level'] == 1].sort_values('oed_score', ascending=False).iterrows():
            cost = float(row['cost'])
            if spent + cost <= total_budget or not selected:
                selected.append(row); selected_ids.add(row['id']); spent += cost
    required = list(required_constructs or metadata.get('experimental_design', {}).get('constraints', {}).get('min_constructs', []))
    if not required_constructs:
        required = ['Ch','M','G','V','R','Y','I']
    for construct in required:
        if any(r['construct'] == construct for r in selected):
            continue
        candidates = df[(df['construct'] == construct) & (~df['id'].isin(selected_ids))]
        if not candidates.empty:
            row = candidates.iloc[0]
            if spent + float(row['cost']) <= total_budget:
                selected.append(row); selected_ids.add(row['id']); spent += float(row['cost'])
    for _, row in df.iterrows():
        if row['id'] in selected_ids:
            continue
        cost = float(row['cost'])
        if spent + cost <= total_budget:
            selected.append(row); selected_ids.add(row['id']); spent += cost
    out = pd.DataFrame(selected).reset_index(drop=True)
    if not out.empty:
        out['selected_cost_cumulative'] = out['cost'].astype(float).cumsum()
    return out


def load_base_panel(path: str | Path | None = None, years: tuple[int, int] | None = None) -> pd.DataFrame:
    p = Path(path) if path is not None else default_level1_data_path()
    df = pd.read_csv(p)
    df['Year'] = df['Year'].astype(int)
    if years is not None:
        start, end = years
        df = df[df['Year'].between(int(start), int(end))]
    return df.sort_values(['country_name','Year']).reset_index(drop=True)


def build_panel(selected_indicators: pd.DataFrame, years: tuple[int, int], base_data_path: str | Path | None = None, fetch_missing: bool = False, wb_backend: str = 'requests') -> pd.DataFrame:
    panel = load_base_panel(base_data_path, years=years)
    cols = ID_COLUMNS.copy()
    for _, row in selected_indicators.iterrows():
        col = row.get('column') or ID_TO_COLUMN.get(row['id'], row['id'])
        if col in panel.columns and col not in cols:
            cols.append(col)
    panel = panel[cols].copy()
    missing_cols = [row.get('column') or ID_TO_COLUMN.get(row['id'], row['id']) for _, row in selected_indicators.iterrows() if (row.get('column') or ID_TO_COLUMN.get(row['id'], row['id'])) not in panel.columns]
    if fetch_missing and missing_cols:
        # Fetch all selected World Bank API-backed indicators into a supplemental frame.
        api_map = {row['api_code']: row['id'] for _, row in selected_indicators.iterrows() if str(row.get('source','')).lower().startswith('world bank') or row.get('api_code')}
        if api_map:
            fetched = fetch_world_bank(years=years, backend=wb_backend, indicators=api_map)
            panel = panel.merge(fetched, on=ID_COLUMNS, how='left', suffixes=('', '_fetched'))
    return panel


def apply_interpolation(panel: pd.DataFrame, max_year: int | None = None) -> pd.DataFrame:
    df = panel.copy()
    value_cols = [c for c in df.columns if c not in ID_COLUMNS]
    if max_year is not None:
        df.loc[df['Year'] > int(max_year), value_cols] = np.nan
    for _, idx in df.groupby('country_name').groups.items():
        sub = df.loc[idx, value_cols]
        df.loc[idx, value_cols] = sub.interpolate(limit_direction='both')
    return df


def generate_quality_report(panel: pd.DataFrame, selected_indicators: pd.DataFrame) -> pd.DataFrame:
    rows = []
    total = len(panel)
    for _, row in selected_indicators.iterrows():
        col = row.get('column') or ID_TO_COLUMN.get(row['id'], row['id'])
        available = int(panel[col].notna().sum()) if col in panel.columns else 0
        rows.append({
            'id': row['id'], 'name': row.get('name',''), 'construct': row.get('construct',''), 'level': int(row.get('level', 0)),
            'source': row.get('source',''), 'column': col, 'selected': col in panel.columns, 'non_null': available,
            'coverage_actual': available / total if total else 0.0, 'coverage_expected': float(row.get('coverage', 0.0)),
            'cost': float(row.get('cost', 0.0)), 'oed_score': float(row.get('oed_score', compute_oed_score(row))),
        })
    return pd.DataFrame(rows).sort_values(['selected','oed_score'], ascending=[False, False]).reset_index(drop=True)


def build_panel_dataset(budget='standard', years: str | tuple[int, int | None] | None = None, constructs: Sequence[str] | None = None, metadata_path=None, base_data_path=None, output='data/processed/panel_dataset.csv', quality_output='data/processed/quality_report.csv', interpolate=True, current_year: int | None = None) -> PanelBuildResult:
    yr = parse_year_range(years, current_year=current_year)
    metadata = load_metadata(metadata_path)
    ind_df = get_indicator_df(metadata)
    required = list(constructs) if constructs else None
    selected = select_indicators(ind_df, metadata, budget=budget, required_constructs=required, require_level1=True)
    panel = build_panel(selected, yr, base_data_path=base_data_path)
    if interpolate:
        panel = apply_interpolation(panel, max_year=yr[1])
    quality = generate_quality_report(panel, selected)
    out_path = Path(output) if output else None
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        panel.to_csv(out_path, index=False)
    if quality_output:
        qp = Path(quality_output); qp.parent.mkdir(parents=True, exist_ok=True); quality.to_csv(qp, index=False)
    return PanelBuildResult(panel=panel, selected_indicators=selected, quality_report=quality, metadata=metadata, output_path=out_path)


def indicators_as_json(metadata_path=None) -> str:
    return json.dumps(get_indicator_df(load_metadata(metadata_path)).to_dict(orient='records'), indent=2)

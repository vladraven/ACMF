from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import pandas as pd

STATE_INDEX = {'A':0,'Prod':1,'Ch':2,'M':3,'G':4,'V':5,'Inst':6,'R':7,'F':8,'P':9}
OBSERVED_CORE = ['P','Prod','A','Inst','F']
ALL_OBSERVABLES = ['P','Prod','A','Inst','F','Ch','M','G','V','R']
ID_COLUMNS = ['country_name', 'country_code', 'Year']

@dataclass(frozen=True)
class TrainFittedScaler:
    """Min-max scaler fitted on train data only to prevent validation leakage."""
    minimum: float
    maximum: float
    invert: bool = False
    default: float = 0.5

    @classmethod
    def fit(cls, s: pd.Series, invert: bool=False, default: float=0.5) -> 'TrainFittedScaler':
        x = pd.to_numeric(s, errors='coerce').astype(float)
        if x.notna().sum() == 0:
            return cls(default, default, invert=invert, default=default)
        x = x.interpolate(limit_direction='both').fillna(x.median())
        return cls(float(x.min()), float(x.max()), invert=invert, default=default)

    def transform(self, s: pd.Series) -> np.ndarray:
        x = pd.to_numeric(s, errors='coerce').astype(float)
        if x.notna().sum() == 0:
            arr = np.full(len(x), self.default)
        else:
            x = x.interpolate(limit_direction='both').fillna(x.median())
            if abs(self.maximum - self.minimum) < 1e-12:
                arr = np.full(len(x), self.default)
            else:
                arr = ((x - self.minimum) / (self.maximum - self.minimum)).to_numpy(dtype=float)
        if self.invert:
            arr = 1.0 - arr
        return np.clip(arr, 0.0, 1.0)


def load_world_panel(path: str | Path | None = None) -> pd.DataFrame:
    p = Path(path) if path else Path(__file__).resolve().parents[2] / 'data' / 'world_data_level1_1995_2025.csv'
    df = pd.read_csv(p)
    df['Year'] = df['Year'].astype(int)
    return df.sort_values(['country_name','Year']).reset_index(drop=True)


def _fit_scaler(g: pd.DataFrame, column: str, fit_end_year: int, invert: bool=False, default: float=0.5) -> TrainFittedScaler:
    if column not in g.columns:
        raise KeyError(f'Missing required indicator column: {column}')
    train = g[g['Year'] <= fit_end_year]
    if train.empty:
        raise ValueError(f'Cannot fit scaler for {column}: no training rows at or before {fit_end_year}')
    return TrainFittedScaler.fit(train[column], invert=invert, default=default)


def _scaled(g: pd.DataFrame, column: str, fit_end_year: int, invert: bool=False, fallback_column: str|None=None, default: float=0.5) -> np.ndarray:
    actual = column if column in g.columns else fallback_column
    if actual is None or actual not in g.columns:
        raise KeyError(f'Missing required indicator column: {column}')
    return _fit_scaler(g, actual, fit_end_year, invert=invert, default=default).transform(g[actual])


def _population_proxy(g: pd.DataFrame, fit_end_year: int, scale: float=500.0) -> np.ndarray:
    if 'Population' not in g.columns:
        raise KeyError('Missing required indicator column: Population')
    pop = pd.to_numeric(g['Population'], errors='coerce').interpolate(limit_direction='both')
    train = pop[g['Year'] <= fit_end_year]
    if train.dropna().empty:
        raise ValueError(f'Cannot fit population proxy: no training population at or before {fit_end_year}')
    base = float(train.dropna().iloc[0])
    if base <= 0:
        raise ValueError(f'Population base must be positive, got {base}')
    return (pop / base * scale).fillna(scale).clip(lower=1.0).to_numpy(float)


def make_acmf_proxy_panel(df: pd.DataFrame, country: str, start_year: int=1995, end_year: int=2024, fit_end_year: int|None=None) -> dict:
    """Build ACMF proxy panel for one country.

    `fit_end_year` is the last year used to estimate scaling parameters. Pass
    the training end year during validation to avoid train/validation leakage.
    If omitted, scalers are fit through end_year for backwards-compatible demos.
    """
    g = df[(df.country_name == country) & (df.Year.between(start_year, end_year))].copy()
    if g.empty:
        raise ValueError(f'No rows for country={country} years={start_year}:{end_year}')
    g = g.sort_values('Year').reset_index(drop=True)
    fit_end = int(fit_end_year if fit_end_year is not None else end_year)
    return {
        't': g['Year'].to_numpy(int),
        'P': _population_proxy(g, fit_end),
        'Prod': _scaled(g, 'GDP_per_capita', fit_end),
        'A': _scaled(g, 'Internet_penetration', fit_end),
        'Inst': _scaled(g, 'Life_expectancy', fit_end),
        'F': 4.0 * _scaled(g, 'Birth_rate', fit_end),
        'Ch': _scaled(g, 'Patent_activity', fit_end, fallback_column='Internet_penetration'),
        'M': _scaled(g, 'Unemployment', fit_end, invert=True),
        'G': _scaled(g, 'Primary_school_enrollment', fit_end, fallback_column='Life_expectancy'),
        'V': _scaled(g, 'Inflation', fit_end),
        'R': _scaled(g, 'Electricity_access', fit_end, fallback_column='Life_expectancy'),
    }


def world_panel_profile(df: pd.DataFrame) -> dict:
    ind = [c for c in df.columns if c not in ID_COLUMNS]
    cov = [{'indicator': c, 'non_null': int(df[c].notna().sum()), 'coverage_pct': float(df[c].notna().mean() * 100)} for c in ind]
    country_coverage = []
    for country, g in df.groupby('country_name'):
        country_coverage.append({
            'country': country,
            'years': int(g['Year'].nunique()),
            'avg_indicator_coverage_pct': float(g[ind].notna().mean().mean() * 100) if ind else 0.0,
        })
    return {
        'rows': int(len(df)),
        'countries_count': int(df['country_name'].nunique()),
        'year_min': int(df['Year'].min()),
        'year_max': int(df['Year'].max()),
        'indicator_count': len(ind),
        'indicators': ind,
        'indicator_coverage': sorted(cov, key=lambda x: x['coverage_pct'], reverse=True),
        'country_coverage': sorted(country_coverage, key=lambda x: x['avg_indicator_coverage_pct'], reverse=True),
    }


def top_countries_by_coverage(df: pd.DataFrame, n: int = 10, min_years: int = 20) -> list[str]:
    out = []
    for item in world_panel_profile(df)['country_coverage']:
        if item['years'] >= min_years:
            out.append(item['country'])
        if len(out) >= n:
            break
    return out


def state_from_proxy(data: dict, idx: int=0) -> np.ndarray:
    return np.array([data['A'][idx], data['Prod'][idx], data['Ch'][idx], data['M'][idx], data['G'][idx], data['V'][idx], data['Inst'][idx], data['R'][idx], data['F'][idx], data['P'][idx]], dtype=float)

from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

STATE_INDEX = {'A':0,'Prod':1,'Ch':2,'M':3,'G':4,'V':5,'Inst':6,'R':7,'F':8,'P':9}
OBSERVED_CORE = ['P','Prod','A','Inst','F']
ALL_OBSERVABLES = ['P','Prod','A','Inst','F','Ch','M','G','V','R']

def load_world_panel(path: str | Path | None = None) -> pd.DataFrame:
    p = Path(path) if path else Path(__file__).resolve().parents[2] / 'data' / 'world_data_level1_1995_2025.csv'
    df = pd.read_csv(p)
    df['Year'] = df['Year'].astype(int)
    return df.sort_values(['country_name','Year']).reset_index(drop=True)

def _norm(s: pd.Series, invert: bool=False, default: float=0.5) -> np.ndarray:
    x = pd.to_numeric(s, errors='coerce').astype(float)
    if x.notna().sum() == 0:
        arr = np.full(len(x), default)
    else:
        x = x.interpolate(limit_direction='both').fillna(x.median())
        lo, hi = float(x.min()), float(x.max())
        if abs(hi-lo) < 1e-12:
            arr = np.full(len(x), default)
        else:
            arr = ((x-lo)/(hi-lo)).to_numpy(dtype=float)
    if invert:
        arr = 1.0 - arr
    return np.clip(arr, 0.0, 1.0)

def make_acmf_proxy_panel(df: pd.DataFrame, country: str, start_year: int=1995, end_year: int=2024) -> dict:
    g = df[(df.country_name == country) & (df.Year.between(start_year, end_year))].copy()
    if g.empty:
        raise ValueError(f'No rows for country={country} years={start_year}:{end_year}')
    g = g.sort_values('Year').reset_index(drop=True)
    pop = pd.to_numeric(g['Population'], errors='coerce').interpolate(limit_direction='both')
    base = float(pop.dropna().iloc[0]) if pop.notna().any() else 1.0
    p_proxy = (pop / base * 500.0).fillna(500.0).clip(lower=1.0).to_numpy(float)
    data = {
        't': g['Year'].to_numpy(int),
        'P': p_proxy,
        'Prod': _norm(g['GDP_per_capita']),
        'A': _norm(g['Internet_penetration']),
        'Inst': _norm(g['Life_expectancy']),
        'F': 4.0 * _norm(g['Birth_rate']),
        'Ch': _norm(g['Patent_activity'] if 'Patent_activity' in g else g['Internet_penetration']),
        'M': _norm(g['Unemployment'], invert=True),
        'G': _norm(g['Primary_school_enrollment'] if 'Primary_school_enrollment' in g else g['Life_expectancy']),
        'V': _norm(g['Inflation']),
        'R': _norm(g['Electricity_access'] if 'Electricity_access' in g else g['Life_expectancy']),
    }
    return data

def state_from_proxy(data: dict, idx: int=0) -> np.ndarray:
    return np.array([data['A'][idx], data['Prod'][idx], data['Ch'][idx], data['M'][idx], data['G'][idx], data['V'][idx], data['Inst'][idx], data['R'][idx], data['F'][idx], data['P'][idx]], dtype=float)

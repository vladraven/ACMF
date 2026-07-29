from __future__ import annotations
from pathlib import Path
import pandas as pd

VDEM_URL = 'https://v-dem.net/data/the-v-dem-dataset/'
INFORM_URL = 'https://drmkc.jrc.ec.europa.eu/inform-index/INFORM-Risk/Results-and-data'

def _load(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == '.csv':
        return pd.read_csv(path)
    if path.suffix.lower() == '.dta':
        return pd.read_stata(path)
    return pd.read_excel(path)

def fetch_vdem_manual(filepath=None, raw_dir='data/raw/resilience') -> pd.DataFrame:
    raw = Path(raw_dir); raw.mkdir(parents=True, exist_ok=True)
    if filepath is None:
        candidates = list(raw.glob('V-Dem*')) + list(raw.glob('vdem*')) + list(raw.glob('VDEM*'))
        if not candidates:
            print(f'[VDEM] No V-Dem file found. Download manually from {VDEM_URL}')
            return pd.DataFrame()
        filepath = candidates[0]
    return _load(Path(filepath))

def fetch_inform_manual(filepath=None, raw_dir='data/raw/resilience') -> pd.DataFrame:
    raw = Path(raw_dir); raw.mkdir(parents=True, exist_ok=True)
    if filepath is None:
        candidates = list(raw.glob('INFORM*')) + list(raw.glob('inform*'))
        if not candidates:
            print(f'[INFORM] No INFORM file found. Download manually from {INFORM_URL}')
            return pd.DataFrame()
        filepath = candidates[0]
    return _load(Path(filepath))

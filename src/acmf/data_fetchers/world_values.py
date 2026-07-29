from __future__ import annotations
from pathlib import Path
import pandas as pd

WVS_URL = 'https://www.worldvaluessurvey.org/WVSDocumentation.jsp'
ESS_URL = 'https://www.europeansocialsurvey.org/data/download.html'

def _load_csv_stata_or_excel(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == '.csv':
        return pd.read_csv(path)
    if path.suffix.lower() in {'.dta'}:
        return pd.read_stata(path)
    return pd.read_excel(path)

def fetch_wvs_manual(filepath=None, raw_dir='data/raw/world_values_survey') -> pd.DataFrame:
    raw = Path(raw_dir); raw.mkdir(parents=True, exist_ok=True)
    if filepath is None:
        candidates = list(raw.glob('WVS*')) + list(raw.glob('wvs*'))
        if not candidates:
            print(f'[WVS] No WVS file found. Download manually from {WVS_URL}')
            return pd.DataFrame()
        filepath = candidates[0]
    return _load_csv_stata_or_excel(Path(filepath))

def fetch_ess_manual(filepath=None, raw_dir='data/raw/world_values_survey') -> pd.DataFrame:
    raw = Path(raw_dir); raw.mkdir(parents=True, exist_ok=True)
    if filepath is None:
        candidates = list(raw.glob('ESS*')) + list(raw.glob('ess*'))
        if not candidates:
            print(f'[ESS] No ESS file found. Download manually from {ESS_URL}')
            return pd.DataFrame()
        filepath = candidates[0]
    return _load_csv_stata_or_excel(Path(filepath))

def aggregate_trust_by_country(wvs_df: pd.DataFrame, country_col='country', year_col='year', trust_col='V202') -> pd.DataFrame:
    if trust_col not in wvs_df.columns:
        print(f'[WVS] {trust_col} not found')
        return pd.DataFrame()
    df = wvs_df.copy()
    df['WVS_TRUST'] = (df[trust_col] == 1).astype(float)
    return df.groupby([country_col, year_col], as_index=False)['WVS_TRUST'].mean().rename(columns={country_col:'country_name', year_col:'Year'})

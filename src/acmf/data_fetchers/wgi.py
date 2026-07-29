from __future__ import annotations
from pathlib import Path
import pandas as pd

WGI_URL = 'http://info.worldbank.org/governance/wgi/Home/downLoadFile?fileName=wgidataset.xlsx'
WGI_CODES = {'GE.EST':'GOVEFF','RL.EST':'RULELAW','PV.EST':'POLSTAB'}

def fetch_wgi_manual(filepath=None, raw_dir='data/raw/wgi') -> pd.DataFrame:
    raw = Path(raw_dir); raw.mkdir(parents=True, exist_ok=True)
    if filepath is None:
        candidates = list(raw.glob('wgidataset*')) + list(raw.glob('wgi*')) + list(raw.glob('WGI*'))
        if not candidates:
            print(f'[WGI] No local file found. Download manually from {WGI_URL}')
            return pd.DataFrame()
        filepath = candidates[0]
    p = Path(filepath)
    if p.suffix.lower() in {'.xlsx','.xls'}:
        return pd.read_excel(p, sheet_name='Country and Region Ratings')
    return pd.read_csv(p)

def fetch_wgi_wbdata(years=(1995, None), countries=None) -> pd.DataFrame:
    from .world_bank import COUNTRIES, complete_data_year
    try:
        import wbdata
    except Exception as exc:
        raise RuntimeError('wbdata is required for WGI wbdata backend') from exc
    start, end = years
    if end is None:
        end = complete_data_year()
    country_codes = list((countries or COUNTRIES).values()) if isinstance(countries, dict) else (countries or list(COUNTRIES.values()))
    try:
        df = wbdata.get_dataframe(WGI_CODES, country=country_codes, date=(str(start), str(end))).reset_index()
        df = df.rename(columns={'country':'country_name','date':'Year'})
        df['Year'] = df['Year'].astype(int)
        return df[df['Year'].between(int(start), int(end))]
    except Exception as exc:
        print(f'[WGI] wbdata failed: {exc}')
        return pd.DataFrame()

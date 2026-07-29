from __future__ import annotations
from pathlib import Path
import pandas as pd

GII_URL = 'https://www.wipo.int/global_innovation_index/'

def fetch_gii_manual(filepath=None, raw_dir='data/raw/innovation') -> pd.DataFrame:
    raw = Path(raw_dir); raw.mkdir(parents=True, exist_ok=True)
    if filepath is None:
        candidates = list(raw.glob('gii*')) + list(raw.glob('GII*'))
        if not candidates:
            print(f'[GII] No local GII file found. Download manually from {GII_URL}')
            return pd.DataFrame()
        filepath = candidates[0]
    p = Path(filepath)
    return pd.read_csv(p) if p.suffix.lower() == '.csv' else pd.read_excel(p)

def fetch_unesco_rd_template(years=(1995, None)) -> pd.DataFrame:
    print('[UNESCO] R&D API requires registration/API key. Returning empty template frame.')
    return pd.DataFrame(columns=['country_name','country_code','Year','RESEARCHERS','RD_EXP'])

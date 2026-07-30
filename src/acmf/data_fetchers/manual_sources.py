from __future__ import annotations
from pathlib import Path
import pandas as pd
from ..exceptions import ManualDownloadRequired

def fetch_local_table(filepath: str | Path) -> pd.DataFrame:
    p=Path(filepath)
    if not p.exists():
        raise FileNotFoundError(f'Local source file not found: {p}')
    if p.suffix.lower()=='.csv':
        return pd.read_csv(p)
    if p.suffix.lower() in {'.xlsx','.xls'}:
        return pd.read_excel(p)
    if p.suffix.lower()=='.dta':
        return pd.read_stata(p)
    raise ValueError(f'Unsupported table format: {p.suffix}')

def require_manual_source(source: str, url: str, raw_dir: str) -> None:
    raise ManualDownloadRequired(source=source, url=url, raw_dir=raw_dir)

"""
Resilience Proxies Fetcher
Sources:
  - V-Dem (institutional continuity)
  - INFORM (disaster preparedness)
  - IMF (fiscal buffers, forex reserves)
  - OECD (government resilience framework)
"""

import pandas as pd
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent / 'data' / 'raw' / 'resilience'
RAW_DIR.mkdir(parents=True, exist_ok=True)

VDEM_URL = "https://v-dem.net/data/the-v-dem-dataset/"
INFORM_URL = "https://drmkc.jrc.ec.europa.eu/inform-index/INFORM-Risk/Results-and-data"


def fetch_vdem_manual(filepath=None):
    """Load V-Dem dataset for institutional continuity."""
    if filepath is None:
        candidates = list(RAW_DIR.glob('V-Dem*')) + list(RAW_DIR.glob('vdem*'))
        if not candidates:
            print("[VDEM] ⚠️  No V-Dem file found.")
            print("[VDEM]    Download from: https://v-dem.net/data/the-v-dem-dataset/")
            return pd.DataFrame()
        filepath = candidates[0]

    print(f"[VDEM] Loading from {filepath}...")
    df = pd.read_csv(filepath) if filepath.suffix == '.csv' else pd.read_stata(filepath)
    print(f"[VDEM] Loaded {len(df)} rows")
    print("[VDEM] Key variables: v2xnp_regcorr (regime corruption), v2x_regime (regime type)")
    return df


def fetch_inform_manual(filepath=None):
    """Load INFORM risk index."""
    if filepath is None:
        candidates = list(RAW_DIR.glob('INFORM*')) + list(RAW_DIR.glob('inform*'))
        if not candidates:
            print("[INFORM] ⚠️  No INFORM file found.")
            print("[INFORM]    Download from: https://drmkc.jrc.ec.europa.eu/inform-index/")
            return pd.DataFrame()
        filepath = candidates[0]

    print(f"[INFORM] Loading from {filepath}...")
    df = pd.read_csv(filepath) if filepath.suffix == '.csv' else pd.read_excel(filepath)
    print(f"[INFORM] Loaded {len(df)} rows")
    return df


if __name__ == '__main__':
    fetch_vdem_manual()
    fetch_inform_manual()

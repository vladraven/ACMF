"""
Innovation & Creativity Proxies Fetcher
Sources:
  - WIPO Global Innovation Index (GII)
  - UNESCO R&D data
  - World Bank high-tech exports, scientific papers
"""

import pandas as pd
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent / 'data' / 'raw' / 'innovation'
RAW_DIR.mkdir(parents=True, exist_ok=True)

# WIPO GII API endpoint (requires registration for full data)
GII_URL = "https://www.wipo.int/global_innovation_index/"


def fetch_gii_manual(filepath=None):
    """
    Load GII data from local CSV/Excel.
    Download from: https://www.wipo.int/global_innovation_index/
    """
    if filepath is None:
        candidates = list(RAW_DIR.glob('gii_*')) + list(RAW_DIR.glob('GII*'))
        if not candidates:
            print("[GII] ⚠️  No GII file found in data/raw/innovation/")
            print("[GII]    Download from: https://www.wipo.int/global_innovation_index/")
            return pd.DataFrame()
        filepath = candidates[0]

    print(f"[GII] Loading from {filepath}...")
    if filepath.suffix == '.xlsx':
        df = pd.read_excel(filepath)
    else:
        df = pd.read_csv(filepath)

    print(f"[GII] Loaded {len(df)} rows")
    print("[GII] Expected columns: Economy, Score, Rank, KnowledgeCreation, CreativeOutputs, ...")
    return df


def fetch_unesco_rd(years=(1995, 2024)):
    """Fetch UNESCO R&D data via UIS API."""
    print("[UNESCO] Fetching R&D personnel and expenditure...")
    print("[UNESCO] API: http://api.uis.unesco.org/")
    print("[UNESCO] ⚠️  Requires API key. Register at: https://uis.unesco.org/")
    # Template for actual implementation:
    # import requests
    # url = "http://api.uis.unesco.org/sdmx-rest/data/UNESCO,RD,1.0/.RD_PERSONNEL..."
    return pd.DataFrame()


if __name__ == '__main__':
    fetch_gii_manual()
    fetch_unesco_rd()

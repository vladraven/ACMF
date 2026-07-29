"""
World Values Survey / European Social Survey / General Social Survey Fetcher
For Values (V) construct proxies: trust, religiosity, tolerance, civic participation.
"""

import pandas as pd
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent / 'data' / 'raw' / 'world_values_survey'
RAW_DIR.mkdir(parents=True, exist_ok=True)

WVS_URL = "https://www.worldvaluessurvey.org/WVSDocumentation.jsp"
ESS_URL = "https://www.europeansocialsurvey.org/data/download.html"


def fetch_wvs_manual(filepath=None):
    """Load WVS aggregated data."""
    if filepath is None:
        candidates = list(RAW_DIR.glob('WVS*')) + list(RAW_DIR.glob('wvs*'))
        if not candidates:
            print("[WVS] ⚠️  No WVS file found.")
            print("[WVS]    Download from: https://www.worldvaluessurvey.org/WVSDocumentation.jsp")
            return pd.DataFrame()
        filepath = candidates[0]

    print(f"[WVS] Loading from {filepath}...")
    df = pd.read_csv(filepath) if filepath.suffix == '.csv' else pd.read_stata(filepath)
    print(f"[WVS] Loaded {len(df)} rows")
    print("[WVS] Key variables to extract: V202 (trust), V185 (religion importance), V185 (tolerance)")
    return df


def fetch_ess_manual(filepath=None):
    """Load European Social Survey data."""
    if filepath is None:
        candidates = list(RAW_DIR.glob('ESS*')) + list(RAW_DIR.glob('ess*'))
        if not candidates:
            print("[ESS] ⚠️  No ESS file found.")
            print("[ESS]    Download from: https://www.europeansocialsurvey.org/data/download.html")
            return pd.DataFrame()
        filepath = candidates[0]

    print(f"[ESS] Loading from {filepath}...")
    df = pd.read_csv(filepath) if filepath.suffix == '.csv' else pd.read_stata(filepath)
    print(f"[ESS] Loaded {len(df)} rows")
    return df


def aggregate_trust_by_country(wvs_df):
    """Aggregate WVS trust question to country-year means."""
    # V202: "Generally speaking, would you say that most people can be trusted..."
    # 1 = Most people can be trusted, 2 = Can't be too careful
    if 'V202' not in wvs_df.columns:
        print("[WVS] V202 (trust) not found in dataset")
        return pd.DataFrame()

    wvs_df['trust'] = (wvs_df['V202'] == 1).astype(int)
    agg = wvs_df.groupby(['country', 'year'])['trust'].mean().reset_index()
    agg = agg.rename(columns={'trust': 'WVS_TRUST', 'country': 'country_name', 'year': 'Year'})
    return agg


if __name__ == '__main__':
    df = fetch_wvs_manual()
    if len(df) > 0:
        trust = aggregate_trust_by_country(df)
        print(trust.head())

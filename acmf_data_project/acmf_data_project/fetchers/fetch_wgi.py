"""
Worldwide Governance Indicators (WGI) Fetcher
Source: World Bank / Brookings
Note: WGI is NOT in standard WB Open Data API. Requires manual download
or scraping from https://info.worldbank.org/governance/wgi/
"""

import pandas as pd
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent / 'data' / 'raw' / 'wgi'
RAW_DIR.mkdir(parents=True, exist_ok=True)

WGI_URL = "http://info.worldbank.org/governance/wgi/Home/downLoadFile?fileName=wgidataset.xlsx"


def fetch_manual(filepath=None, years=(1995, 2024)):
    """
    Load WGI from local file (manual download required).
    Place wgidecode*.csv or wgidataset.xlsx in data/raw/wgi/
    """
    if filepath is None:
        # Try to find any WGI file
        candidates = list(RAW_DIR.glob('wgidataset*')) + list(RAW_DIR.glob('wgi*'))
        if not candidates:
            print("[WGI] ⚠️  No WGI file found in data/raw/wgi/")
            print("[WGI]    Download from: http://info.worldbank.org/governance/wgi/")
            return pd.DataFrame()
        filepath = candidates[0]

    print(f"[WGI] Loading from {filepath}...")

    if filepath.suffix == '.xlsx':
        df = pd.read_excel(filepath, sheet_name='Country and Region Ratings')
    else:
        df = pd.read_csv(filepath)

    # WGI format: columns like 'Estimate1996', 'StdErr1996', etc.
    # We need to melt to long format
    # This is a template — adjust to actual WGI column names

    print(f"[WGI] Loaded {len(df)} rows. Columns: {list(df.columns[:10])}...")
    print("[WGI] ⚠️  You must manually map WGI columns to our indicator IDs:")
    print("         GE.EST → GOVEFF")
    print("         RL.EST → RULELAW")
    print("         PV.EST → POLSTAB")

    return df


def fetch_from_wbdata(years=(1995, 2024)):
    """Attempt via wbdata (often fails for WGI)."""
    try:
        import wbdata
        wgi_codes = {'GE.EST': 'GOVEFF', 'RL.EST': 'RULELAW', 'PV.EST': 'POLSTAB'}
        df = wbdata.get_dataframe(
            indicators=wgi_codes,
            country=[
                'CA','US','AU','NZ','DE','FR','NL','SE','NO','IT','ES','PT',
                'PL','CZ','RO','HU','JP','KR','SG','CN','IN','BD','BR','CL',
                'MX','IL','AE','SA','ZA','NG','KE'
            ],
            data_date=f"{years[0]}-01-01",
            convert_date=False
        )
        df = df.reset_index()
        df = df.rename(columns={'country': 'country_name', 'date': 'Year'})
        df['Year'] = df['Year'].astype(int)
        df = df[df['Year'].between(years[0], years[1])]
        print(f"[WGI] Successfully fetched {len(df)} rows via wbdata")
        return df
    except Exception as e:
        print(f"[WGI] wbdata failed: {e}")
        return pd.DataFrame()


if __name__ == '__main__':
    df = fetch_from_wbdata()
    if len(df) == 0:
        df = fetch_manual()

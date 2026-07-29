"""
World Bank Open Data Fetcher
Fetches Level 1 (Core ACMF) and some Level 3 indicators.
"""

import wbdata
import pandas as pd
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent / 'data' / 'raw' / 'world_bank'
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Indicator codes → our IDs
WB_INDICATORS = {
    'SP.POP.TOTL': 'POP',
    'SP.DYN.CBRT.IN': 'BIRTH',
    'SP.DYN.CDRT.IN': 'DEATH',
    'SM.POP.NETM': 'MIGR',
    'NY.GDP.PCAP.KD': 'GDPC',
    'NY.GDP.MKTP.KD.ZG': 'GDPG',
    'FP.CPI.TOTL.ZG': 'INFL',
    'SL.UEM.TOTL.ZS': 'UNEMP',
    'SP.DYN.LE00.IN': 'LIFE',
    'SP.URB.TOTL.IN.ZS': 'URBAN',
    'EG.USE.PCAP.KG.OE': 'ENERGY_PC',
    'EN.GHG.CO2.PC.CE.AR5': 'CO2_PC',
    'IT.NET.USER.ZS': 'INTERNET',
    'EG.ELC.ACCS.ZS': 'ELECTRICITY',
    'SE.PRM.TENR': 'SCHOOL_ENROLL',
    'IP.PAT.RESD': 'PATENTS',
    'GB.XPD.RSDV.GD.ZS': 'RD_EXP',
    'TX.VAL.TECH.CD': 'HIGHTECH_X',
    'IP.JRN.ARTC.SC': 'SCI_PAPERS',
    'SP.POP.SCIE.RD.P6': 'RESEARCHERS',
    'SL.TLF.CACT.ZS': 'LFPR',
    'SL.UEM.1524.ZS': 'YOUTH_UNEMP',
    'SL.EMP.TOTL.SP.ZS': 'WORKING_AGE_EMP',
    'SL.EMP.SELF.ZS': 'SELF_EMP',
    'IC.BUS.NDNS.ZS': 'NEW_BUS',
    'IC.BUS.NREG': 'BUSINESS_FORMATIONS',
    'IC.BUS.EASE.XQ': 'EODB',
    'SI.POV.GINI': 'GINI',
    'GC.NLD.TOTL.GD.ZS': 'FISCAL_BUFFER',
    'FI.RES.TOTL.CD': 'FOREX_RESERVES',
}

COUNTRIES = [
    'CA', 'US', 'AU', 'NZ',
    'DE', 'FR', 'NL', 'SE', 'NO',
    'IT', 'ES', 'PT',
    'PL', 'CZ', 'RO', 'HU',
    'JP', 'KR', 'SG',
    'CN', 'IN', 'BD',
    'BR', 'CL', 'MX',
    'IL', 'AE', 'SA',
    'ZA', 'NG', 'KE'
]


def fetch(years=(1995, 2024), save=True):
    """Fetch all World Bank indicators."""
    print(f"[WB] Fetching {len(WB_INDICATORS)} indicators for {len(COUNTRIES)} countries...")

    df = wbdata.get_dataframe(
        indicators=WB_INDICATORS,
        country=COUNTRIES,
        data_date=f"{years[0]}-01-01",
        convert_date=False
    )

    df = df.reset_index()
    df = df.rename(columns={'country': 'country_name', 'date': 'Year'})
    df['Year'] = df['Year'].astype(int)
    df = df[df['Year'].between(years[0], years[1])]

    if save:
        path = RAW_DIR / 'world_bank_raw.csv'
        df.to_csv(path, index=False)
        print(f"[WB] Saved: {path} ({len(df)} rows)")

    return df


if __name__ == '__main__':
    fetch()

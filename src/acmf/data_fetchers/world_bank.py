from __future__ import annotations
from pathlib import Path
from typing import Mapping, Sequence
import time
import pandas as pd
import requests

COUNTRIES = {
    'Canada':'CA','United States':'US','Australia':'AU','New Zealand':'NZ','Germany':'DE','France':'FR','Netherlands':'NL','Sweden':'SE','Norway':'NO','Italy':'IT','Spain':'ES','Portugal':'PT','Poland':'PL','Czechia':'CZ','Romania':'RO','Hungary':'HU','Japan':'JP','Korea, Rep.':'KR','Singapore':'SG','China':'CN','India':'IN','Bangladesh':'BD','Brazil':'BR','Chile':'CL','Mexico':'MX','Israel':'IL','United Arab Emirates':'AE','Saudi Arabia':'SA','South Africa':'ZA','Nigeria':'NG','Kenya':'KE'
}

WB_INDICATORS = {
    'SP.POP.TOTL':'POP','SP.DYN.CBRT.IN':'BIRTH','SP.DYN.CDRT.IN':'DEATH','SM.POP.NETM':'MIGR','NY.GDP.PCAP.KD':'GDPC','NY.GDP.MKTP.KD.ZG':'GDPG','FP.CPI.TOTL.ZG':'INFL','SL.UEM.TOTL.ZS':'UNEMP','SP.DYN.LE00.IN':'LIFE','SP.URB.TOTL.IN.ZS':'URBAN','EG.USE.PCAP.KG.OE':'ENERGY_PC','EN.GHG.CO2.PC.CE.AR5':'CO2_PC','IT.NET.USER.ZS':'INTERNET','EG.ELC.ACCS.ZS':'ELECTRICITY','SE.PRM.TENR':'SCHOOL_ENROLL','IP.PAT.RESD':'PATENTS','GB.XPD.RSDV.GD.ZS':'RD_EXP','TX.VAL.TECH.CD':'HIGHTECH_X','IP.JRN.ARTC.SC':'SCI_PAPERS','SP.POP.SCIE.RD.P6':'RESEARCHERS','SL.TLF.CACT.ZS':'LFPR','SL.UEM.1524.ZS':'YOUTH_UNEMP','SL.EMP.TOTL.SP.ZS':'WORKING_AGE_EMP','SL.EMP.SELF.ZS':'SELF_EMP','IC.BUS.NDNS.ZS':'NEW_BUS','IC.BUS.NREG':'BUSINESS_FORMATIONS','IC.BUS.EASE.XQ':'EODB','SI.POV.GINI':'GINI','GC.NLD.TOTL.GD.ZS':'FISCAL_BUFFER','FI.RES.TOTL.CD':'FOREX_RESERVES'
}

API = 'https://api.worldbank.org/v2/country/{country}/indicator/{indicator}'

NAME_MAP = {
    'POP':'Population','BIRTH':'Birth_rate','DEATH':'Death_rate','MIGR':'Net_migration','GDPC':'GDP_per_capita','GDPG':'GDP_growth','INFL':'Inflation','UNEMP':'Unemployment','LIFE':'Life_expectancy','URBAN':'Urbanization_pct','ENERGY_PC':'Energy_consumption_per_capita','CO2_PC':'CO2_per_capita','INTERNET':'Internet_penetration','ELECTRICITY':'Electricity_access','SCHOOL_ENROLL':'Primary_school_enrollment','PATENTS':'Patent_activity','RD_EXP':'RD_expenditure_pct_GDP'
}

def complete_data_year(current_year: int | None = None, lag_years: int = 2) -> int:
    """Return the default complete-data year: current calendar year minus lag_years."""
    from datetime import date
    year = int(current_year if current_year is not None else date.today().year)
    return year - int(lag_years)

def _country_dict(countries: Mapping[str, str] | Sequence[str] | None):
    if countries is None:
        return COUNTRIES
    if isinstance(countries, Mapping):
        return dict(countries)
    wanted = set(countries)
    return {k:v for k,v in COUNTRIES.items() if k in wanted or v in wanted}

def _indicator_dict(indicators: Mapping[str, str] | Sequence[str] | None):
    if indicators is None:
        return WB_INDICATORS
    if isinstance(indicators, Mapping):
        return dict(indicators)
    wanted = set(indicators)
    return {k:v for k,v in WB_INDICATORS.items() if k in wanted or v in wanted}

def fetch_indicator_requests(country_code: str, indicator: str, start_year: int, end_year: int, timeout: int = 30) -> dict[int, float | None]:
    params = {'format':'json', 'date':f'{start_year}:{end_year}', 'per_page':20000}
    response = requests.get(API.format(country=country_code, indicator=indicator), params=params, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list) or len(payload) < 2 or payload[1] is None:
        return {}
    return {int(row['date']): row.get('value') for row in payload[1]}

def fetch_world_bank_requests(years=(1995, None), countries=None, indicators=None, sleep: float = 0.05, save_path: str | Path | None = None) -> pd.DataFrame:
    start, end = years
    if end is None:
        end = complete_data_year()
    countries_d = _country_dict(countries)
    indicators_d = _indicator_dict(indicators)
    rows = []
    for country_name, country_code in countries_d.items():
        by_year = {year: {'country_name': country_name, 'country_code': country_code, 'Year': year} for year in range(int(start), int(end)+1)}
        for api_code, ind_id in indicators_d.items():
            try:
                values = fetch_indicator_requests(country_code, api_code, int(start), int(end))
            except Exception as exc:
                print(f'[WB requests] WARN {country_name} {api_code}: {exc}')
                values = {}
            col = NAME_MAP.get(ind_id, ind_id)
            for year in range(int(start), int(end)+1):
                by_year[year][col] = values.get(year)
            if sleep:
                time.sleep(float(sleep))
        rows.extend(by_year.values())
    df = pd.DataFrame(rows).sort_values(['country_name','Year']).reset_index(drop=True)
    if save_path is not None:
        p = Path(save_path); p.parent.mkdir(parents=True, exist_ok=True); df.to_csv(p, index=False)
    return df

def fetch_world_bank_wbdata(years=(1995, None), countries=None, indicators=None, save_path: str | Path | None = None) -> pd.DataFrame:
    start, end = years
    if end is None:
        end = complete_data_year()
    countries_d = _country_dict(countries)
    indicators_d = _indicator_dict(indicators)
    try:
        import wbdata
    except Exception as exc:
        raise RuntimeError('wbdata backend requested but wbdata is not installed') from exc
    wb_indicators = {api: NAME_MAP.get(ind_id, ind_id) for api, ind_id in indicators_d.items()}
    df = wbdata.get_dataframe(wb_indicators, country=list(countries_d.values()), date=(str(start), str(end)))
    df = df.reset_index().rename(columns={'country':'country_name', 'date':'Year'})
    df['Year'] = df['Year'].astype(int)
    # Add stable country_code if wbdata preserved names only.
    reverse = {v:k for k,v in countries_d.items()}
    if 'country_code' not in df.columns:
        df['country_code'] = ''
    df = df.sort_values(['country_name','Year']).reset_index(drop=True)
    if save_path is not None:
        p = Path(save_path); p.parent.mkdir(parents=True, exist_ok=True); df.to_csv(p, index=False)
    return df

def fetch_world_bank(years=(1995, None), backend: str = 'requests', **kwargs) -> pd.DataFrame:
    """Fetch World Bank panel with either backend='requests' or backend='wbdata'."""
    if backend == 'requests':
        return fetch_world_bank_requests(years=years, **kwargs)
    if backend == 'wbdata':
        return fetch_world_bank_wbdata(years=years, **kwargs)
    if backend == 'auto':
        try:
            return fetch_world_bank_wbdata(years=years, **kwargs)
        except Exception:
            return fetch_world_bank_requests(years=years, **kwargs)
    raise ValueError("backend must be 'requests', 'wbdata', or 'auto'")

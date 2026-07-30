from __future__ import annotations
from datetime import date
from pathlib import Path
import time
import pandas as pd
import requests
from ..exceptions import SourceUnavailableError

COUNTRIES={'Canada':'CA','Germany':'DE','Japan':'JP','Australia':'AU','Korea, Rep.':'KR','United States':'US','France':'FR','Italy':'IT','Spain':'ES','Netherlands':'NL'}
WB_INDICATORS={'SP.POP.TOTL':'Population','NY.GDP.PCAP.KD':'GDP_per_capita','IT.NET.USER.ZS':'Internet_penetration','SP.DYN.CBRT.IN':'Birth_rate','SP.DYN.CDRT.IN':'Death_rate','SL.UEM.TOTL.ZS':'Unemployment','FP.CPI.TOTL.ZG':'Inflation','SP.DYN.LE00.IN':'Life_expectancy','IP.PAT.RESD':'Patent_activity','GB.XPD.RSDV.GD.ZS':'RD_expenditure_pct_GDP'}
API='https://api.worldbank.org/v2/country/{country}/indicator/{indicator}'

def complete_data_year(current_year: int | None=None, lag_years: int=2) -> int:
    return int(current_year or date.today().year) - int(lag_years)

def fetch_world_bank_requests(years=(1995,None), countries=None, indicators=None, timeout=30, sleep=0.05, strict=True, save_path=None) -> pd.DataFrame:
    start,end=years; end=complete_data_year() if end is None else int(end)
    country_map=COUNTRIES if countries is None else {k:v for k,v in COUNTRIES.items() if k in countries or v in countries}
    ind_map=WB_INDICATORS if indicators is None else {k:v for k,v in WB_INDICATORS.items() if k in indicators or v in indicators}
    rows=[]; errors=[]
    for cname,ccode in country_map.items():
        by_year={y:{'country_name':cname,'country_code':ccode,'Year':y} for y in range(int(start),end+1)}
        for api_code,col in ind_map.items():
            try:
                r=requests.get(API.format(country=ccode, indicator=api_code), params={'format':'json','date':f'{start}:{end}','per_page':20000}, timeout=timeout)
                r.raise_for_status(); payload=r.json(); values={}
                if isinstance(payload,list) and len(payload)>1 and payload[1]:
                    values={int(x['date']):x.get('value') for x in payload[1]}
                for y in range(int(start),end+1): by_year[y][col]=values.get(y)
            except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
                errors.append(f'{cname}:{api_code}:{exc}')
                if strict:
                    raise SourceUnavailableError(errors[-1]) from exc
                for y in range(int(start),end+1): by_year[y][col]=pd.NA
            if sleep: time.sleep(sleep)
        rows.extend(by_year.values())
    df=pd.DataFrame(rows).sort_values(['country_name','Year']).reset_index(drop=True)
    if save_path:
        p=Path(save_path); p.parent.mkdir(parents=True, exist_ok=True); df.to_csv(p,index=False)
    return df

#!/usr/bin/env python3
from __future__ import annotations
import argparse, time
from pathlib import Path
import requests, pandas as pd
COUNTRIES={"Australia":"AU","Bangladesh":"BD","Brazil":"BR","Canada":"CA","Chile":"CL","China":"CN","Czechia":"CZ","France":"FR","Germany":"DE","Hungary":"HU","India":"IN","Israel":"IL","Italy":"IT","Japan":"JP","Kenya":"KE","Korea, Rep.":"KR","Mexico":"MX","Netherlands":"NL","New Zealand":"NZ","Nigeria":"NG","Norway":"NO","Poland":"PL","Portugal":"PT","Romania":"RO","Saudi Arabia":"SA","Singapore":"SG","South Africa":"ZA","Spain":"ES","Sweden":"SE","United Arab Emirates":"AE","United States":"US"}
INDICATORS={"SP.DYN.CBRT.IN":"Birth_rate","EN.GHG.CO2.PC.CE.AR5":"CO2_per_capita","SP.DYN.CDRT.IN":"Death_rate","EG.ELC.ACCS.ZS":"Electricity_access","EG.USE.PCAP.KG.OE":"Energy_consumption_per_capita","NY.GDP.MKTP.KD.ZG":"GDP_growth","NY.GDP.PCAP.KD":"GDP_per_capita","FP.CPI.TOTL.ZG":"Inflation","IT.NET.USER.ZS":"Internet_penetration","SP.DYN.LE00.IN":"Life_expectancy","SM.POP.NETM":"Net_migration","IP.PAT.RESD":"Patent_activity","SP.POP.TOTL":"Population","SE.PRM.ENRR":"Primary_school_enrollment","GB.XPD.RSDV.GD.ZS":"RD_expenditure_pct_GDP","SL.UEM.TOTL.ZS":"Unemployment","SP.URB.TOTL.IN.ZS":"Urbanization_pct"}
API='https://api.worldbank.org/v2/country/{country}/indicator/{indicator}'
def fetch_indicator(country_code,indicator,start_year,end_year,timeout=30):
    r=requests.get(API.format(country=country_code,indicator=indicator),params={'format':'json','date':f'{start_year}:{end_year}','per_page':20000},timeout=timeout); r.raise_for_status(); payload=r.json()
    if not isinstance(payload,list) or len(payload)<2 or payload[1] is None: return {}
    return {int(row['date']):row.get('value') for row in payload[1]}
def download_world_data(start_year,end_year,countries,sleep=0.05):
    rows=[]
    for cname,ccode in countries.items():
        by_year={y:{'country_name':cname,'country_code':ccode,'Year':y} for y in range(start_year,end_year+1)}
        for ind,col in INDICATORS.items():
            try: vals=fetch_indicator(ccode,ind,start_year,end_year)
            except Exception as exc: print(f'WARN {cname} {ind}: {exc}'); vals={}
            for y in range(start_year,end_year+1): by_year[y][col]=vals.get(y)
            time.sleep(sleep)
        rows.extend(by_year.values())
    cols=['country_name','country_code','Year']+list(INDICATORS.values())
    return pd.DataFrame(rows)[cols].sort_values(['country_name','Year']).reset_index(drop=True)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--start-year',type=int,default=1995); ap.add_argument('--end-year',type=int,default=2025); ap.add_argument('--output',default='data/world_data_1995_2025.csv'); ap.add_argument('--countries',nargs='*')
    a=ap.parse_args(); countries=COUNTRIES if not a.countries else {k:v for k,v in COUNTRIES.items() if k in set(a.countries)}
    if not countries: raise SystemExit('No valid countries selected')
    df=download_world_data(a.start_year,a.end_year,countries); out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); df.to_csv(out,index=False); print(f'saved: {out} rows={len(df)} cols={len(df.columns)}')
if __name__=='__main__': main()

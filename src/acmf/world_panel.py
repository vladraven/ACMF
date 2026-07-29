from __future__ import annotations
from importlib import resources
from pathlib import Path
from typing import Dict, Sequence
import numpy as np, pandas as pd
DEFAULT_WORLD_DATA='world_data_1995_2025.csv'; ID_COLUMNS=['country_name','country_code','Year']
def _default_data_path(): return Path(resources.files('acmf.data').joinpath(DEFAULT_WORLD_DATA))
def load_world_panel(path=None):
    p=Path(path) if path is not None else _default_data_path(); df=pd.read_csv(p); df['Year']=df['Year'].astype(int); return df.sort_values(['country_name','Year']).reset_index(drop=True)
def world_panel_profile(df):
    ind=[c for c in df.columns if c not in ID_COLUMNS]; cov=[{'indicator':c,'non_null':int(df[c].notna().sum()),'coverage_pct':float(df[c].notna().mean()*100)} for c in ind]; cc=[]
    for country,g in df.groupby('country_name'): cc.append({'country':country,'years':int(g['Year'].nunique()),'avg_indicator_coverage_pct':float(g[ind].notna().mean().mean()*100)})
    return {'rows':int(len(df)),'countries_count':int(df['country_name'].nunique()),'year_min':int(df['Year'].min()),'year_max':int(df['Year'].max()),'indicator_count':len(ind),'indicators':ind,'indicator_coverage':sorted(cov,key=lambda x:x['coverage_pct'],reverse=True),'country_coverage':sorted(cc,key=lambda x:x['avg_indicator_coverage_pct'],reverse=True)}
def _minmax(s):
    x=pd.to_numeric(s,errors='coerce').astype(float); lo=x.min(skipna=True); hi=x.max(skipna=True)
    if not np.isfinite(lo) or not np.isfinite(hi) or abs(hi-lo)<1e-12: return pd.Series(np.full(len(x),0.5),index=s.index)
    return ((x-lo)/(hi-lo)).clip(0,1)
def _mean(df,cols):
    present=[c for c in cols if c in df.columns]
    return df[present].apply(pd.to_numeric,errors='coerce').mean(axis=1) if present else pd.Series(np.nan,index=df.index)
def make_acmf_proxy_panel(df,country,start_year=None,end_year=None,interpolate=True):
    g=df[df['country_name']==country].copy()
    if start_year is not None: g=g[g['Year']>=start_year]
    if end_year is not None: g=g[g['Year']<=end_year]
    if g.empty: raise ValueError(f'No rows for country={country!r}')
    g=g.sort_values('Year').reset_index(drop=True); num=[c for c in g.columns if c not in ID_COLUMNS]
    for c in num: g[c]=pd.to_numeric(g[c],errors='coerce')
    if interpolate: g[num]=g[num].interpolate(limit_direction='both')
    pop=g['Population'].astype(float); pop0=float(pop.iloc[0]) if np.isfinite(pop.iloc[0]) and pop.iloc[0]!=0 else float(pop.mean())
    return {'t':g['Year'].to_numpy(float),'P':(pop/pop0*500).to_numpy(float),'Prod':_minmax(g.get('GDP_per_capita',pd.Series(np.nan,index=g.index))).to_numpy(float),'A':_minmax(_mean(g,['Internet_penetration','Patent_activity','RD_expenditure_pct_GDP'])).to_numpy(float),'Inst':_minmax(_mean(g,['Electricity_access','Primary_school_enrollment','Urbanization_pct'])).to_numpy(float),'F':(g.get('Birth_rate',pd.Series(20,index=g.index)).astype(float)/10).clip(0,4).to_numpy(float),'Ch':_minmax(_mean(g,['Patent_activity','RD_expenditure_pct_GDP'])).to_numpy(float),'M':_minmax(_mean(g,['Unemployment','Inflation'])).to_numpy(float),'G':_minmax(_mean(g,['Internet_penetration','Urbanization_pct'])).to_numpy(float),'V':_minmax(_mean(g,['Unemployment','Inflation','CO2_per_capita'])).to_numpy(float),'R':_minmax(_mean(g,['Life_expectancy','Electricity_access','GDP_per_capita'])).to_numpy(float)}
def top_countries_by_coverage(df,n=10,min_years=20):
    out=[]
    for item in world_panel_profile(df)['country_coverage']:
        if item['years']>=min_years: out.append(item['country'])
        if len(out)>=n: break
    return out

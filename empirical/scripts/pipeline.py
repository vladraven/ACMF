from __future__ import annotations
from pathlib import Path
import csv,re,hashlib
import numpy as np, pandas as pd
from acmf.aging_transition_matrix import AGE_ORDER, fixed_alpha, apply_aging, transition_matrix
ROOT=Path(__file__).resolve().parents[1]; RAW=ROOT/'raw/statcan'; OUT=ROOT/'processed'; REP=ROOT/'reports'
PROVINCES=['Newfoundland and Labrador','Prince Edward Island','Nova Scotia','New Brunswick','Quebec','Ontario','Manitoba','Saskatchewan','Alberta','British Columbia','Yukon','Northwest Territories','Nunavut']
P1=set(['-1 year','0 to 4 years','5 to 9 years','10 to 14 years']); P2=set(['15 to 19 years','20 to 24 years','25 to 29 years','30 to 34 years','35 to 39 years','40 to 44 years','45 to 49 years','50 to 54 years','55 to 59 years','60 to 64 years']); P3=set(['65 to 69 years','70 to 74 years','75 to 79 years','80 to 84 years','85 to 89 years','90 to 94 years','95 to 99 years','100 years and older'])
def sha256(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rows(p):
    with open(p,encoding='utf-8-sig',newline='') as f: return list(csv.reader(f))
def cf(r):
    o=[]; last=''
    for x in r:
        if x: last=x
        o.append(last)
    return o
def num(x):
    try: return float(str(x).replace(',','').replace('t','').strip())
    except Exception: return np.nan
def period(s):
    m=re.match(r'(\d{4})\s*/\s*(\d{4})',str(s)); return (int(m.group(1)),int(m.group(2))) if m else (None,None)
def clean_age(x): return re.sub(r'\s+\d+(\s+\d+)*$','',str(x).strip()).strip()
def cname(x): return re.sub(r'[^a-z0-9_]+','',re.sub(r'\s+\d+(\s+\d+)*$','',str(x).strip().lower()).replace(' ','_').replace('-','_'))
def wide(file,geo_row,gender_row,period_row,data_start,comp_row=None,migrant_row=None):
    R=rows(RAW/file); geos=cf(R[geo_row]); genders=cf(R[gender_row]); periods=R[period_row]; comps=cf(R[comp_row]) if comp_row is not None else None; migs=cf(R[migrant_row]) if migrant_row is not None else None; rec=[]
    for r in R[data_start:]:
        if not r or str(r[0]).startswith('Symbol legend'): break
        age=clean_age(r[0])
        if not age or age.lower().startswith('age group'): continue
        for j in range(1,min(len(r),len(geos),len(genders),len(periods))):
            if not geos[j] or not genders[j] or not periods[j]: continue
            ys,ye=period(periods[j]); d={'geo':geos[j],'gender':genders[j],'age_group':age,'period':periods[j],'start_year':ys,'end_year':ye,'value':num(r[j])}
            if comps is not None: d['component']=cname(comps[j])
            if migs is not None: d['migrants']=cname(migs[j])
            rec.append(d)
    return pd.DataFrame(rec)
def parse_population():
    df=wide('1710000501-eng.csv',8,9,10,12).dropna(subset=['value']); df['year']=df.period.astype(int); df=df.rename(columns={'value':'population'})
    return df[df.geo.isin(PROVINCES)&df.gender.isin(['Men+','Women+'])&df.age_group.isin(AGE_ORDER)][['geo','gender','age_group','year','population']]
def parse_deaths():
    df=wide('1710000601-eng.csv',8,9,10,12).dropna(subset=['value']).rename(columns={'value':'deaths'})
    return df[df.geo.isin(PROVINCES)&df.gender.isin(['Men+','Women+'])&df.age_group.isin(AGE_ORDER)][['geo','gender','age_group','start_year','end_year','deaths']]
def parse_international():
    df=wide('1710001401-eng.csv',8,9,11,13,comp_row=10).dropna(subset=['value']); df=df[df.geo.isin(PROVINCES)&df.gender.isin(['Men+','Women+'])&df.age_group.isin(AGE_ORDER)]
    sign={'immigrants':1,'emigrants':-1,'returning_emigrants':1,'net_temporary_emigration':-1,'net_non_permanent_residents':1}; df['signed']=df.value*df.component.map(sign).fillna(0)
    return df.groupby(['geo','gender','age_group','start_year','end_year'],as_index=False).signed.sum().rename(columns={'signed':'net_international_migration'})
def parse_interprov_in():
    frames=[]
    for f in ['1710001501-eng (1).csv','1710001501-eng.csv']:
        if (RAW/f).exists():
            df=wide(f,8,9,11,13,migrant_row=10).dropna(subset=['value']); df=df[df.geo.isin(PROVINCES)&df.gender.isin(['Men+','Women+'])&df.age_group.isin(AGE_ORDER)&df.migrants.eq('in_migrants')]; frames.append(df)
    if not frames: return pd.DataFrame(columns=['geo','gender','age_group','start_year','end_year','in_migrants'])
    return pd.concat(frames,ignore_index=True).drop_duplicates(['geo','gender','age_group','start_year','end_year']).rename(columns={'value':'in_migrants'})[['geo','gender','age_group','start_year','end_year','in_migrants']]
def parse_growth():
    R=rows(RAW/'1710000801-eng.csv'); geos=cf(R[8]); periods=R[9]; rec=[]
    for r in R[11:]:
        if not r or r[0].startswith('Symbol legend'): break
        comp=cname(r[0])
        for j in range(1,min(len(r),len(geos),len(periods))):
            if geos[j] and periods[j]: ys,ye=period(periods[j]); rec.append({'geo':geos[j],'component':comp,'period':periods[j],'start_year':ys,'end_year':ye,'value':num(r[j])})
    return pd.DataFrame(rec).query('geo in @PROVINCES')
def parse_births(): return parse_growth().query("component=='births'")[['geo','start_year','end_year','value']].rename(columns={'value':'births'})
def aggregate_pop(df):
    tmp=df.copy(); tmp['cohort']=tmp.age_group.map(lambda a:'P1_0_14' if a in P1 else ('P2_15_64' if a in P2 else ('P3_65plus' if a in P3 else None))); tmp=tmp.dropna(subset=['cohort'])
    w=tmp.groupby(['geo','year','cohort'],as_index=False).population.sum().pivot_table(index=['geo','year'],columns='cohort',values='population',aggfunc='sum').reset_index(); w.columns.name=None
    for c in ['P1_0_14','P2_15_64','P3_65plus']:
        if c not in w: w[c]=0.0
    w['P_tot']=w[['P1_0_14','P2_15_64','P3_65plus']].sum(1); return w
def apply_components(pred,pop_t,year,deaths,intl,inp,growth,births, components=('births','deaths','international','interprovincial')):
    pred=pred.copy()
    if 'births' in components:
        for _,r in births[births.start_year.eq(year)][['geo','births']].iterrows():
            sh=pop_t[(pop_t.geo.eq(r.geo))&(pop_t.age_group.eq('0 to 4 years'))]; tot=sh.population.sum()
            if tot>0:
                for _,s in sh.iterrows(): pred.loc[(pred.geo.eq(r.geo))&(pred.gender.eq(s.gender))&(pred.age_group.eq('0 to 4 years')),'population_pred']+=r.births*s.population/tot
    if 'deaths' in components:
        pred=pred.merge(deaths[deaths.start_year.eq(year)][['geo','gender','age_group','deaths']],on=['geo','gender','age_group'],how='left'); pred['deaths']=pred.deaths.fillna(0); pred['population_pred']-=pred.deaths
    if 'international' in components:
        pred=pred.merge(intl[intl.start_year.eq(year)][['geo','gender','age_group','net_international_migration']],on=['geo','gender','age_group'],how='left'); pred['net_international_migration']=pred.net_international_migration.fillna(0); pred['population_pred']+=pred.net_international_migration
    if 'interprovincial' in components:
        for _,r in growth[(growth.start_year.eq(year))&(growth.component.eq('net_interprovincial_migration'))][['geo','value']].iterrows():
            sh=inp[(inp.start_year.eq(year))&(inp.geo.eq(r.geo))]; den=sh.in_migrants.sum() if len(sh) else 0
            if den<=0: sh=pop_t[pop_t.geo.eq(r.geo)][['geo','gender','age_group','population']].rename(columns={'population':'in_migrants'}); den=sh.in_migrants.sum()
            if den>0:
                for _,s in sh.iterrows(): pred.loc[(pred.geo.eq(r.geo))&(pred.gender.eq(s.gender))&(pred.age_group.eq(s.age_group)),'population_pred'] += r.value*s.in_migrants/den
    return pred
def stage_trace(pop_t,alpha,year,deaths,intl,inp,growth,births):
    stages=[]
    current=apply_aging(pop_t,alpha); current['stage']='after_aging'; stages.append(current[['geo','gender','age_group','stage','population_pred']].copy())
    for name, comps in [('after_births',('births',)),('after_deaths',('births','deaths')),('after_international',('births','deaths','international')),('after_interprovincial',('births','deaths','international','interprovincial'))]:
        current=apply_aging(pop_t,alpha); current=apply_components(current,pop_t,year,deaths,intl,inp,growth,births,components=comps); current['stage']=name; stages.append(current[['geo','gender','age_group','stage','population_pred']].copy())
    out=pd.concat(stages,ignore_index=True); out['year']=year+1; return out
def predict(pop,alpha,years,deaths,intl,inp,growth,births,components=('births','deaths','international','interprovincial')):
    arr=[]
    for y in years:
        pt=pop[pop.year.eq(y)]; pr=apply_aging(pt,alpha); pr=apply_components(pr,pt,y,deaths,intl,inp,growth,births,components); pr['year']=y+1; arr.append(pr[['geo','gender','age_group','year','population_pred']])
    out=pd.concat(arr); out.population_pred=out.population_pred.clip(lower=0); return out
def metrics(pred,obs,model):
    rows=[]
    for t in ['P1_0_14','P2_15_64','P3_65plus','P_tot']:
        m=pred[['geo','year',t]].merge(obs[['geo','year',t]],on=['geo','year'],suffixes=('_pred','_obs'))
        for geo,g in [('ALL',m)]+list(m.groupby('geo')):
            e=g[f'{t}_pred']-g[f'{t}_obs']; rows.append({'model':model,'target':t,'geo':geo,'rmse':float(np.sqrt(np.mean(e*e))),'mae':float(np.mean(abs(e))),'relative_rmse':float(np.sqrt(np.mean(e*e))/np.mean(abs(g[f'{t}_obs']))),'n':len(g)})
    return rows
def baselines(obs):
    rows=[]
    for y in [2022,2023,2024]:
        cur=obs[obs.year.eq(y)]; prev=obs[obs.year.eq(y-1)]
        lv=cur.copy(); lv['year']=y+1; lv['model']='last_value'; rows.append(lv)
        m=cur.merge(prev,on='geo',suffixes=('_c','_p')); ls=m[['geo']].copy(); ls['year']=y+1
        for c in ['P1_0_14','P2_15_64','P3_65plus','P_tot']: ls[c]=m[f'{c}_c']+(m[f'{c}_c']-m[f'{c}_p'])
        ls['model']='last_slope'; rows.append(ls)
    return pd.concat(rows)
def estimate_alpha(pop,deaths,intl,inp,growth,births):
    # Deliberately auditable: starts from fixed 0.2 and tunes older ages only. If output remains 0.2, report it.
    alpha=fixed_alpha(.2); tune=['60 to 64 years','65 to 69 years','70 to 74 years','75 to 79 years','80 to 84 years','85 to 89 years','90 to 94 years','95 to 99 years']; grid=np.array([.02,.08,.14,.20,.26,.32,.38,.44])
    obs=pop.rename(columns={'population':'obs'})[['geo','gender','age_group','year','obs']]
    def obj(a):
        pr=predict(pop,a,[2021],deaths,intl,inp,growth,births).merge(obs,on=['geo','gender','age_group','year']); pr=pr[pr.age_group.isin(P3)]; e=pr.population_pred-pr.obs; return float(np.sqrt(np.mean(e*e)))
    for age in tune:
        best=(obj(alpha),alpha[age])
        for g in grid:
            tr=dict(alpha); tr[age]=float(g); val=obj(tr)
            if val<best[0]: best=(val,float(g))
        alpha[age]=best[1]
    return alpha


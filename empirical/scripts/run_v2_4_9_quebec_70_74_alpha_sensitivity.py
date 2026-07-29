from __future__ import annotations
from pathlib import Path
import csv, re, json, hashlib, sys
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from acmf.aging_transition_matrix import AGE_ORDER, fixed_alpha

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'raw/statcan'; OUT=ROOT/'processed'; REP=ROOT/'reports'
OUT.mkdir(parents=True, exist_ok=True); REP.mkdir(parents=True, exist_ok=True)
GEO='Quebec'; SOURCE='65 to 69 years'; TARGET='70 to 74 years'; YEARS=[2022,2023,2024]
PROVINCES=['Newfoundland and Labrador','Prince Edward Island','Nova Scotia','New Brunswick','Quebec','Ontario','Manitoba','Saskatchewan','Alberta','British Columbia','Yukon','Northwest Territories','Nunavut']
AGE_BINS={'0 to 4 years':range(0,5),'5 to 9 years':range(5,10),'10 to 14 years':range(10,15),'15 to 19 years':range(15,20),'20 to 24 years':range(20,25),'25 to 29 years':range(25,30),'30 to 34 years':range(30,35),'35 to 39 years':range(35,40),'40 to 44 years':range(40,45),'45 to 49 years':range(45,50),'50 to 54 years':range(50,55),'55 to 59 years':range(55,60),'60 to 64 years':range(60,65),'65 to 69 years':range(65,70),'70 to 74 years':range(70,75),'75 to 79 years':range(75,80),'80 to 84 years':range(80,85),'85 to 89 years':range(85,90),'90 to 94 years':range(90,95),'95 to 99 years':range(95,100)}

def sha256(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read_rows(path):
    with open(path,encoding='utf-8-sig',newline='') as f: return list(csv.reader(f))
def cf(row):
    out=[]; last=''
    for x in row:
        if x: last=x
        out.append(last)
    return out
def num(x):
    try: return float(str(x).replace(',','').replace('t','').strip())
    except Exception: return np.nan
def period(s):
    m=re.match(r'(\d{4})\s*/\s*(\d{4})',str(s)); return (int(m.group(1)),int(m.group(2))) if m else (None,None)
def clean_age(x): return re.sub(r'\s+\d+(\s+\d+)*$','',str(x).strip()).strip()
def cname(x): return re.sub(r'[^a-z0-9_]+','',re.sub(r'\s+\d+(\s+\d+)*$','',str(x).strip().lower()).replace(' ','_').replace('-','_'))
def wide(file,geo_row,gender_row,period_row,data_start,comp_row=None,migrant_row=None):
    R=read_rows(RAW/file); geos=cf(R[geo_row]); genders=cf(R[gender_row]); periods=R[period_row]; comps=cf(R[comp_row]) if comp_row is not None else None; migs=cf(R[migrant_row]) if migrant_row is not None else None; rec=[]
    for r in R[data_start:]:
        if not r or str(r[0]).startswith('Symbol legend'): break
        age=clean_age(r[0]);
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
    return pd.concat(frames,ignore_index=True).drop_duplicates(['geo','gender','age_group','start_year','end_year']).rename(columns={'value':'in_migrants'})[['geo','gender','age_group','start_year','end_year','in_migrants']] if frames else pd.DataFrame(columns=['geo','gender','age_group','start_year','end_year','in_migrants'])
def parse_growth():
    R=read_rows(RAW/'1710000801-eng.csv'); geos=cf(R[8]); periods=R[9]; rec=[]
    for r in R[11:]:
        if not r or r[0].startswith('Symbol legend'): break
        comp=cname(r[0])
        for j in range(1,min(len(r),len(geos),len(periods))):
            if geos[j] and periods[j]: ys,ye=period(periods[j]); rec.append({'geo':geos[j],'component':comp,'period':periods[j],'start_year':ys,'end_year':ye,'value':num(r[j])})
    return pd.DataFrame(rec).query('geo in @PROVINCES')
def parse_single_age_2021():
    R=read_rows(RAW/'9810002301-eng.csv'); gr=next(i for i,r in enumerate(R) if r and r[0]=='Geography'); gg=R[gr+1]; geos=[]; last=''
    for x in R[gr][1:]:
        if x: last=re.sub(r'\s+i\d+$','',x).strip()
        geos.append(last)
    genders=[]; lg=''
    for g in gg[1:]:
        if g: lg=re.sub(r'\s+\d+(\s+\d+)*$','',g).strip()
        genders.append(lg)
    rec=[]
    for r in R[gr+3:]:
        if not r or r[0].startswith('Average age') or r[0].startswith('Abbreviation notes'): break
        label=r[0].strip()
        if label=='Under 1 year': age=0
        elif re.fullmatch(r'\d+',label): age=int(label)
        elif label=='100 years and over': age=100
        else: continue
        for j,val in enumerate(r[1:]):
            if j<len(geos) and geos[j] and j<len(genders) and genders[j] in {'Men+','Women+'}: rec.append({'geo':geos[j],'gender':genders[j],'age_single':age,'year':2021,'population':num(val)})
    return pd.DataFrame(rec).dropna(subset=['population'])
def estimate_real_alpha(single):
    alpha=fixed_alpha(.2); rows=[]
    for group, ages in AGE_BINS.items():
        ages=list(ages); total=single[single.age_single.isin(ages)].population.sum(); exit_pop=single[single.age_single.eq(max(ages))].population.sum(); frac=float(exit_pop/total) if total>0 else .2; alpha[group]=min(max(frac,0),.95); rows.append({'age_group':group,'outflow_fraction':alpha[group],'fixed20':.2,'diff_vs_fixed20':alpha[group]-.2})
    alpha['-1 year']=0; alpha['100 years and older']=0; return alpha,pd.DataFrame(rows)
def interprov_alloc(inp,growth,year,gender,age_group,pop_t):
    net=growth[(growth.geo.eq(GEO))&(growth.start_year.eq(year))&(growth.component.eq('net_interprovincial_migration'))].value.sum(); shares=inp[(inp.geo.eq(GEO))&(inp.start_year.eq(year))]; denom=shares.in_migrants.sum() if len(shares) else 0
    if denom<=0 or np.isnan(denom): shares=pop_t[pop_t.geo.eq(GEO)][['geo','gender','age_group','population']].rename(columns={'population':'in_migrants'}); denom=shares.in_migrants.sum()
    if denom<=0: return 0.0
    val=shares[(shares.gender.eq(gender))&(shares.age_group.eq(age_group))].in_migrants.sum(); return float(net*val/denom)
def predict_70_74(pop,deaths,intl,inp,growth,alpha_source,alpha_target):
    rows=[]
    for y in YEARS:
        pop_t=pop[(pop.geo.eq(GEO))&(pop.year.eq(y))]
        total_pred=0; total_obs=0; comp=[]
        for gender in ['Men+','Women+']:
            psrc=float(pop_t[(pop_t.gender.eq(gender))&(pop_t.age_group.eq(SOURCE))].population.sum()); ptgt=float(pop_t[(pop_t.gender.eq(gender))&(pop_t.age_group.eq(TARGET))].population.sum())
            stay=(1-alpha_target)*ptgt; inflow=alpha_source*psrc; after_aging=stay+inflow
            d=float(deaths[(deaths.geo.eq(GEO))&(deaths.start_year.eq(y))&(deaths.gender.eq(gender))&(deaths.age_group.eq(TARGET))].deaths.sum())
            im=float(intl[(intl.geo.eq(GEO))&(intl.start_year.eq(y))&(intl.gender.eq(gender))&(intl.age_group.eq(TARGET))].net_international_migration.sum())
            ip=interprov_alloc(inp,growth,y,gender,TARGET,pop_t); pred=after_aging-d+im+ip; obs=float(pop[(pop.geo.eq(GEO))&(pop.year.eq(y+1))&(pop.gender.eq(gender))&(pop.age_group.eq(TARGET))].population.sum())
            total_pred+=pred; total_obs+=obs
            comp.append({'target_year':y+1,'gender':gender,'population_source_start':psrc,'population_target_start':ptgt,'aging_stay_from_target':stay,'aging_inflow_from_source':inflow,'after_aging':after_aging,'deaths':d,'net_international_migration':im,'allocated_net_interprovincial':ip,'prediction':pred,'observed':obs,'residual':pred-obs})
        rows.append({'target_year':y+1,'prediction':total_pred,'observed':total_obs,'residual':total_pred-total_obs,'abs_error':abs(total_pred-total_obs),'squared_error':(total_pred-total_obs)**2,'components':comp})
    return rows
def summarize(year_rows):
    se=np.array([r['squared_error'] for r in year_rows]); ae=np.array([r['abs_error'] for r in year_rows])
    return {'rmse':float(np.sqrt(se.mean())),'mae':float(ae.mean()),'max_abs_error':float(ae.max()),'median_abs_error':float(np.median(ae))}
def main():
    pop=parse_population(); deaths=parse_deaths(); intl=parse_international(); inp=parse_interprov_in(); growth=parse_growth(); single=parse_single_age_2021(); alpha_real, alpha_source=estimate_real_alpha(single); alpha_fixed=fixed_alpha(.2)
    a_src_real=alpha_real[SOURCE]; a_tgt_real=alpha_real[TARGET]
    grid=[]; detail_models=[]
    for a_src in np.round(np.arange(0.12,0.281,0.005),3):
        for a_tgt in np.round(np.arange(0.12,0.281,0.005),3):
            rows=predict_70_74(pop,deaths,intl,inp,growth,float(a_src),float(a_tgt)); s=summarize(rows); grid.append({'alpha_source_65_69':float(a_src),'alpha_target_70_74':float(a_tgt),**s})
    grid_df=pd.DataFrame(grid).sort_values('rmse'); grid_df.to_csv(OUT/'v2_4_9_quebec_70_74_alpha_grid.csv',index=False)
    candidates={
        'real_single_age':(a_src_real,a_tgt_real),
        'fixed20':(.2,.2),
        'best_grid_rmse':(float(grid_df.iloc[0].alpha_source_65_69),float(grid_df.iloc[0].alpha_target_70_74)),
        'best_grid_mae':tuple(grid_df.sort_values('mae').iloc[0][['alpha_source_65_69','alpha_target_70_74']].astype(float)),
        'high_source_fixed_target':(.23,.2),
        'fixed_source_low_target':(.2,.18),
    }
    model_summ=[]; yearly=[]; comps=[]
    for name,(a_src,a_tgt) in candidates.items():
        rows=predict_70_74(pop,deaths,intl,inp,growth,a_src,a_tgt); s=summarize(rows); model_summ.append({'model':name,'alpha_source_65_69':a_src,'alpha_target_70_74':a_tgt,**s})
        for r in rows:
            rr={k:v for k,v in r.items() if k!='components'}; rr.update({'model':name,'alpha_source_65_69':a_src,'alpha_target_70_74':a_tgt}); yearly.append(rr)
            for c in r['components']:
                cc=dict(c); cc.update({'model':name,'alpha_source_65_69':a_src,'alpha_target_70_74':a_tgt}); comps.append(cc)
    ms=pd.DataFrame(model_summ).sort_values('rmse'); ms.to_csv(OUT/'v2_4_9_quebec_70_74_alpha_models_summary.csv',index=False)
    pd.DataFrame(yearly).to_csv(OUT/'v2_4_9_quebec_70_74_yearly_predictions_by_model.csv',index=False)
    pd.DataFrame(comps).to_csv(OUT/'v2_4_9_quebec_70_74_gender_component_trace_by_model.csv',index=False)
    alpha_focus=alpha_source[alpha_source.age_group.isin([SOURCE,TARGET])].copy(); alpha_focus.to_csv(OUT/'v2_4_9_quebec_70_74_alpha_real_focus.csv',index=False)
    real=ms[ms.model.eq('real_single_age')].iloc[0].to_dict(); fixed=ms[ms.model.eq('fixed20')].iloc[0].to_dict(); best=ms.iloc[0].to_dict()
    findings=[]
    findings.append('This is a local sensitivity/counterfactual audit, not a production operator-selection model.')
    findings.append(f"Best grid RMSE is {best['rmse']:.2f} at alpha_source={best['alpha_source_65_69']:.3f}, alpha_target={best['alpha_target_70_74']:.3f}.")
    findings.append(f"Observed real_single_age alphas are source={a_src_real:.6f}, target={a_tgt_real:.6f}; fixed20 uses source=0.200000, target=0.200000.")
    if best['rmse'] < fixed['rmse'] and best['rmse'] < real['rmse']: findings.append('A local alpha pair can outperform both real_single_age and fixed20 for Quebec 70-74 in this window; this is evidence for local regime sensitivity, not a general rule.')
    if fixed['rmse'] < real['rmse']: findings.append('fixed20 outperforms real_single_age for Quebec 70-74, confirming the v2.4.8 localized failure mode.')
    report={'status':'PASS_WITH_FINDINGS','purpose':'Local alpha sensitivity for Quebec 70-74 to determine whether the failure is tied to the 65-69 inflow / 70-74 stay rates.','findings':findings,'model_summary':ms.to_dict('records'),'best_grid_row':grid_df.iloc[0].to_dict(),'limitations':['Grid is evaluated on the same Quebec 2023-2025 window; do not use best_grid as a production operator without out-of-sample validation.','This is an explanatory counterfactual around one age bin and province.','Observed components remain accounting-mode inputs.']}
    (REP/'v2_4_9_quebec_70_74_alpha_sensitivity_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    lines=['# v2.4.9 Quebec 70-74 Alpha Sensitivity','',f"Status: **{report['status']}**",'', '## Purpose',report['purpose'],'','## Model summary']
    for r in report['model_summary']: lines.append(f"- `{r['model']}`: alpha_source={r['alpha_source_65_69']:.3f}, alpha_target={r['alpha_target_70_74']:.3f}, RMSE={r['rmse']:.2f}, MAE={r['mae']:.2f}, MaxAE={r['max_abs_error']:.2f}")
    lines+=['','## Findings']+[f"- {x}" for x in findings]+['','## Limitations']+[f"- {x}" for x in report['limitations']]
    (REP/'v2_4_9_quebec_70_74_alpha_sensitivity_report.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps({'status':report['status'],'findings':findings,'best':report['best_grid_row']},indent=2))
if __name__=='__main__': main()


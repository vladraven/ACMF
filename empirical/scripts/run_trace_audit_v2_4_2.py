from __future__ import annotations
from pathlib import Path
import sys,json,pandas as pd,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from acmf.aging_transition_matrix import fixed_alpha, transition_matrix
from empirical.scripts.pipeline import OUT,REP,RAW,sha256,parse_population,parse_deaths,parse_international,parse_interprov_in,parse_growth,parse_births,aggregate_pop,predict,baselines,metrics,estimate_alpha,stage_trace

def target_diff(a,b,name_a,name_b):
    m=a.merge(b,on=['geo','year'],suffixes=(f'_{name_a}',f'_{name_b}'))
    rows=[]
    for t in ['P1_0_14','P2_15_64','P3_65plus','P_tot']:
        d=m[f'{t}_{name_a}']-m[f'{t}_{name_b}']
        rows.append({'target':t,'max_abs_diff':float(abs(d).max()),'mean_abs_diff':float(abs(d).mean()),'allclose':bool(np.allclose(m[f'{t}_{name_a}'],m[f'{t}_{name_b}']))})
    return pd.DataFrame(rows)
def aggregate_stage(stage_df):
    tmp=stage_df.rename(columns={'population_pred':'population'}); tmp['cohort']=tmp.age_group.map(lambda a:'P1_0_14' if a in ['-1 year','0 to 4 years','5 to 9 years','10 to 14 years'] else ('P2_15_64' if a in ['15 to 19 years','20 to 24 years','25 to 29 years','30 to 34 years','35 to 39 years','40 to 44 years','45 to 49 years','50 to 54 years','55 to 59 years','60 to 64 years'] else ('P3_65plus' if a in ['65 to 69 years','70 to 74 years','75 to 79 years','80 to 84 years','85 to 89 years','90 to 94 years','95 to 99 years','100 years and older'] else None)))
    out=tmp.groupby(['operator','stage','geo','year','cohort'],as_index=False).population.sum().pivot_table(index=['operator','stage','geo','year'],columns='cohort',values='population',aggfunc='sum').reset_index(); out.columns.name=None
    for c in ['P1_0_14','P2_15_64','P3_65plus']:
        if c not in out: out[c]=0.0
    out['P_tot']=out[['P1_0_14','P2_15_64','P3_65plus']].sum(1); return out

def main():
    REP.mkdir(exist_ok=True,parents=True); OUT.mkdir(exist_ok=True,parents=True)
    input_hashes={p.name:sha256(p) for p in sorted((Path(__file__).resolve().parents[1]/'raw/statcan').glob('*.csv'))}
    pop=parse_population(); deaths=parse_deaths(); intl=parse_international(); inp=parse_interprov_in(); growth=parse_growth(); births=parse_births(); obs=aggregate_pop(pop); obs_eval=obs[obs.year.isin([2023,2024,2025])]
    alpha_fixed=fixed_alpha(.2); alpha_emp=estimate_alpha(pop,deaths,intl,inp,growth,births)
    alpha_df=pd.DataFrame([{'age_group':k,'fixed_outflow':alpha_fixed[k],'empirical_outflow':alpha_emp[k],'difference':alpha_emp[k]-alpha_fixed[k]} for k in alpha_fixed]); alpha_df.to_csv(OUT/'v2_4_2_aging_operator_diff.csv',index=False)
    transition_matrix(alpha_emp).to_csv(OUT/'v2_4_2_transition_matrix.csv',index=False)
    # Stage traces, all provinces/genders/ages/years, fixed and empirical
    traces=[]
    for year in [2021,2022,2023,2024]:
        pt=pop[pop.year.eq(year)]
        if len(pt)==0: continue
        f=stage_trace(pt,alpha_fixed,year,deaths,intl,inp,growth,births); f['operator']='fixed20'; traces.append(f)
        e=stage_trace(pt,alpha_emp,year,deaths,intl,inp,growth,births); e['operator']='empirical_transition'; traces.append(e)
    trace=pd.concat(traces,ignore_index=True); trace.to_csv(OUT/'v2_4_2_full_stage_trace_age_gender.csv',index=False)
    ag=aggregate_stage(trace); ag.to_csv(OUT/'v2_4_2_full_stage_trace_p123.csv',index=False)
    # Fixed vs empirical diff at every stage
    stage_diffs=[]
    for stage in sorted(ag.stage.unique()):
        f=ag[(ag.operator.eq('fixed20'))&(ag.stage.eq(stage))]; e=ag[(ag.operator.eq('empirical_transition'))&(ag.stage.eq(stage))]
        d=target_diff(e,f,'empirical','fixed'); d['stage']=stage; stage_diffs.append(d)
    stage_diff=pd.concat(stage_diffs,ignore_index=True); stage_diff.to_csv(OUT/'v2_4_2_stage_prediction_diff.csv',index=False)
    # Component ablation chains
    component_sets=[('aging_only',()),('aging_births',('births',)),('aging_births_deaths',('births','deaths')),('aging_births_deaths_international',('births','deaths','international')),('aging_births_deaths_international_interprovincial',('births','deaths','international','interprovincial'))]
    all_metrics=[]; all_preds=[]
    for op,alpha in [('fixed20',alpha_fixed),('empirical_transition',alpha_emp)]:
        for label,components in component_sets:
            pr=predict(pop,alpha,[2022,2023,2024],deaths,intl,inp,growth,births,components=components)
            pp=aggregate_pop(pr.rename(columns={'population_pred':'population'})); pp['model']=f'{op}_{label}'; all_preds.append(pp)
            all_metrics += metrics(pp,obs_eval,f'{op}_{label}')
    base=baselines(obs)
    for m,g in base.groupby('model'): all_metrics += metrics(g,obs_eval,m)
    met=pd.DataFrame(all_metrics); met.to_csv(OUT/'v2_4_2_component_ablation_metrics.csv',index=False)
    all_summary=met[met.geo.eq('ALL')]
    deltas=[]
    for op in ['fixed20','empirical_transition']:
        chain=[f'{op}_{x[0]}' for x in component_sets]
        for target in ['P1_0_14','P2_15_64','P3_65plus','P_tot']:
            vals=[float(all_summary[(all_summary.model.eq(m))&(all_summary.target.eq(target))].rmse.iloc[0]) for m in chain]
            for i in range(1,len(vals)):
                deltas.append({'operator':op,'target':target,'from_model':chain[i-1],'to_model':chain[i],'delta_rmse':vals[i]-vals[i-1],'rmse_before':vals[i-1],'rmse_after':vals[i]})
    delta_df=pd.DataFrame(deltas); delta_df.to_csv(OUT/'v2_4_2_component_delta_rmse.csv',index=False)
    pt=all_summary[all_summary.target.eq('P_tot')][['model','rmse','mae','relative_rmse']].sort_values('rmse'); pt.to_csv(OUT/'v2_4_2_p_tot_forecast_vs_accounting.csv',index=False)
    # Conclusions
    operator_changed=bool((alpha_df.difference.abs()>1e-12).any())
    stage_changed=bool((stage_diff.max_abs_diff>0).any())
    findings=[]
    findings.append('Aging operator coefficients changed from fixed 20%.' if operator_changed else 'Aging operator coefficients did not change from fixed 20%; empirical calibration selected the same coefficients.')
    findings.append('Stage trace shows empirical transition changes predictions.' if stage_changed else 'Stage trace shows no difference at any stage between fixed and empirical transition outputs.')
    if not operator_changed and not stage_changed:
        findings.append('Root cause: v2.4 transition matrix variant was effectively equivalent to fixed20; identical RMSE was a real pipeline finding, not independent evidence of improvement.')
    best=all_summary.sort_values(['target','rmse']).groupby('target').first().reset_index()[['target','model','rmse','mae','relative_rmse','n']]
    report={'status':'PASS_WITH_FINDINGS','input_hashes':input_hashes,'alpha_operator_changed':operator_changed,'stage_predictions_changed':stage_changed,'findings':findings,'stage_diff_summary':stage_diff.to_dict('records'),'best_by_target':best.to_dict('records'),'p_tot_forecast_vs_accounting':pt.to_dict('records')[:10],'known_limitations':['Observed demographic components are used in accounting-style ablations.','Current empirical transition calibration can select the fixed20 solution; v2.4 is not proven as an improvement.','No uncertainty propagation or stochastic component yet.','Interprovincial net migration by age/gender is approximated from official net totals and in-migrant shares.']}
    (REP/'v2_4_2_trace_audit_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    md=['# v2.4.2 Trace / Pipeline Audit','',f"Status: **{report['status']}**",'', '## Findings']+[f'- {x}' for x in findings]+['','## Operator changed?',f"- `alpha_operator_changed`: `{operator_changed}`",f"- `stage_predictions_changed`: `{stage_changed}`",'', '## Stage diff summary']
    for r in report['stage_diff_summary'][:20]: md.append(f"- stage `{r['stage']}` target `{r['target']}`: max_abs_diff={r['max_abs_diff']}, allclose={r['allclose']}")
    md += ['', '## Best by target']+[f"- `{r['target']}`: `{r['model']}` RMSE={r['rmse']:.2f}, rel={r['relative_rmse']:.6f}" for r in report['best_by_target']]
    md += ['', '## P_tot modes']+[f"- `{r['model']}`: RMSE={r['rmse']:.2f}, rel={r['relative_rmse']:.8f}" for r in report['p_tot_forecast_vs_accounting']]
    (REP/'v2_4_2_trace_audit_report.md').write_text('\n'.join(md),encoding='utf-8')
    print(json.dumps({'status':report['status'],'findings':findings,'alpha_operator_changed':operator_changed,'stage_predictions_changed':stage_changed},indent=2))
if __name__=='__main__': main()


from __future__ import annotations
from pathlib import Path
import json
import numpy as np
import pandas as pd
from .world_panel import load_world_panel, make_acmf_proxy_panel, OBSERVED_CORE, ALL_OBSERVABLES
from .model_levels import observed_vars_for_level
from .calibration import calibrate_country_proxy, predict_from_theta, CALIBRATION_PARAMS
from .validation_metrics import metrics_dataframe
from .identifiability import simple_fim_diagnostics as fim_diagnostics
from .observation_designer import score_candidate_observables_simple as score_candidate_observables

CORE5 = ['Canada','Germany','Japan','Australia','Korea, Rep.']

def _safe(obj):
    if isinstance(obj, dict): return {k:_safe(v) for k,v in obj.items()}
    if isinstance(obj, list): return [_safe(v) for v in obj]
    if isinstance(obj, tuple): return [_safe(v) for v in obj]
    if isinstance(obj, np.ndarray): return obj.tolist()
    if isinstance(obj, (np.integer,)): return int(obj)
    if isinstance(obj, (np.floating,float)):
        x=float(obj)
        if np.isnan(x): return None
        if np.isinf(x): return 'Infinity' if x>0 else '-Infinity'
        return x
    return obj

def split_proxy_data(data: dict, train_end: int=2015, validation_start: int=2016, validation_end: int=2024):
    t=np.asarray(data['t'])
    train_mask=t<=train_end
    val_mask=(t>=validation_start)&(t<=validation_end)
    train={k:np.asarray(v)[train_mask] for k,v in data.items()}
    val={k:np.asarray(v)[val_mask] for k,v in data.items()}
    return train, val

def _subset_by_year(data, start, end):
    t=np.asarray(data['t']); m=(t>=start)&(t<=end)
    return {k:np.asarray(v)[m] for k,v in data.items()}

def forecast_validation(data_full, theta, validation_start, validation_end, variables):
    start_idx=int(np.where(data_full['t']==validation_start)[0][0])
    pred=predict_from_theta(data_full, theta, start_idx=start_idx, steps=validation_end-validation_start+1)
    obs=_subset_by_year(data_full, validation_start, validation_end)
    metrics=metrics_dataframe(obs, pred, variables)
    yearly=[]
    for i,y in enumerate(obs['t']):
        for v in variables:
            yearly.append({'Year':int(y),'variable':v,'observed':float(obs[v][i]),'predicted':float(pred[v][i]),'error':float(pred[v][i]-obs[v][i])})
    return metrics, pd.DataFrame(yearly), pred

def run_country_validation(country: str, train_start=1995, train_end=2015, validation_start=2016, validation_end=2024, seeds=(0,1,2), variables=None, max_nfev=60, data_path=None, model_level: str='R5'):
    variables=list(variables or observed_vars_for_level(model_level))
    panel=load_world_panel(data_path)
    full=make_acmf_proxy_panel(panel,country,train_start, validation_end, fit_end_year=train_end)
    train=_subset_by_year(full, train_start, train_end)
    runs=[]
    for seed in seeds:
        cr=calibrate_country_proxy(country, train, variables, seed=seed, max_nfev=max_nfev)
        val_metrics, yearly, pred = forecast_validation(full, cr.theta, validation_start, validation_end, variables)
        iddiag=fim_diagnostics(train, cr.theta, variables)
        runs.append({'seed':seed,'calibration':cr,'validation_metrics':val_metrics,'yearly_errors':yearly,'identifiability':iddiag})
    # choose best final loss
    best=min(runs, key=lambda r:r['calibration'].loss_final)
    rows=[]
    for r in runs:
        cr=r['calibration']
        row={'country':country,'seed':r['seed'],'converged':cr.converged,'loss_initial':cr.loss_initial,'loss_final':cr.loss_final,'loss_reduction_pct':100*(cr.loss_initial-cr.loss_final)/max(cr.loss_initial,1e-12),'nfev':cr.nfev,'bounds_hit':';'.join(cr.bounds_hit),'rank':r['identifiability']['rank'],'condition_number':r['identifiability']['condition_number']}
        row.update({name:float(val) for name,val in zip(cr.parameter_names, cr.theta)})
        rows.append(row)
    runs_df=pd.DataFrame(rows)
    metrics=best['validation_metrics'].copy(); metrics.insert(0,'country',country); metrics.insert(1,'seed',best['seed'])
    yearly=best['yearly_errors'].copy(); yearly.insert(0,'country',country); yearly.insert(1,'seed',best['seed'])
    # candidate observation design after best calibration
    candidates=[v for v in ALL_OBSERVABLES if v not in variables]
    od=score_candidate_observables(train, best['calibration'].theta, variables, candidates).to_dict(orient='records')
    return {'country':country,'runs':runs_df,'best_metrics':metrics,'yearly_errors':yearly,'best_identifiability':best['identifiability'],'observation_design':od}

def run_core5_validation(countries=CORE5, **kwargs):
    reports=[run_country_validation(c, **kwargs) for c in countries]
    runs=pd.concat([r['runs'] for r in reports], ignore_index=True)
    metrics=pd.concat([r['best_metrics'] for r in reports], ignore_index=True)
    yearly=pd.concat([r['yearly_errors'] for r in reports], ignore_index=True)
    return {'country_reports':reports,'runs':runs,'metrics':metrics,'yearly_errors':yearly,'parameter_stability':parameter_stability_report(runs),'identifiability_map':identifiability_map(runs)}

def parameter_stability_report(runs_df: pd.DataFrame):
    rows=[]
    for p in CALIBRATION_PARAMS:
        x=pd.to_numeric(runs_df[p], errors='coerce')
        mean=float(x.mean()); std=float(x.std(ddof=0)); cv=float(std/max(abs(mean),1e-12))
        cls='stable' if cv<0.25 else ('weak' if cv<0.75 else 'unstable')
        rows.append({'parameter':p,'mean':mean,'std':std,'min':float(x.min()),'max':float(x.max()),'coefficient_of_variation':cv,'classification':cls})
    return pd.DataFrame(rows)

def identifiability_map(runs_df: pd.DataFrame):
    rows=[]
    for country,g in runs_df.groupby('country'):
        best=g.sort_values('loss_final').iloc[0]
        stable=sum(g[CALIBRATION_PARAMS].std(ddof=0) / g[CALIBRATION_PARAMS].mean().abs().clip(lower=1e-12) < 0.25)
        weak=sum((g[CALIBRATION_PARAMS].std(ddof=0) / g[CALIBRATION_PARAMS].mean().abs().clip(lower=1e-12)).between(0.25,0.75))
        non=len(CALIBRATION_PARAMS)-stable-weak
        rows.append({'country':country,'rank':int(best['rank']),'condition_number':float(best['condition_number']),'stable_parameters':int(stable),'weak_parameters':int(weak),'non_identifiable_parameters':int(non)})
    return pd.DataFrame(rows)

def indicator_ablation_study(country='Canada', variables=None, train_start=1995, train_end=2015, validation_start=2016, validation_end=2024, seed=0, model_level: str='R5'):
    variables=list(variables or observed_vars_for_level(model_level))
    base=run_country_validation(country,train_start,train_end,validation_start,validation_end,seeds=(seed,),variables=variables,max_nfev=40)
    base_rmse=float(base['best_metrics']['RMSE'].mean()); base_cond=float(base['runs'].iloc[0]['condition_number'])
    rows=[]
    for removed in variables:
        keep=[v for v in variables if v!=removed]
        if not keep: continue
        rep=run_country_validation(country,train_start,train_end,validation_start,validation_end,seeds=(seed,),variables=keep,max_nfev=40, model_level=model_level)
        rmse=float(rep['best_metrics']['RMSE'].mean()); cond=float(rep['runs'].iloc[0]['condition_number'])
        rows.append({'country':country,'removed_indicator':removed,'baseline_rmse':base_rmse,'ablation_rmse':rmse,'delta_rmse_pct':100*(rmse-base_rmse)/max(base_rmse,1e-12),'baseline_condition_number':base_cond,'ablation_condition_number':cond,'delta_condition_number_pct':100*(cond-base_cond)/max(base_cond,1e-12)})
    return pd.DataFrame(rows)

def backtest_2008(country='Canada', seed=0, model_level: str='R5'):
    return run_country_validation(country,train_start=1995,train_end=2007,validation_start=2008,validation_end=2015,seeds=(seed,),variables=observed_vars_for_level(model_level),max_nfev=50, model_level=model_level)

def write_validation_outputs(report: dict, output_dir='output/empirical_validation'):
    out=Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    report['runs'].to_csv(out/'country_parameter_estimates.csv', index=False)
    report['metrics'].to_csv(out/'core5_validation_metrics.csv', index=False)
    report['yearly_errors'].to_csv(out/'dynamic_errors_by_year.csv', index=False)
    report['parameter_stability'].to_csv(out/'parameter_stability_map.csv', index=False)
    report['identifiability_map'].to_csv(out/'identifiability_map.csv', index=False)
    summary={'countries':sorted(report['runs']['country'].unique()),'mean_RMSE':float(report['metrics']['RMSE'].mean()),'mean_MAE':float(report['metrics']['MAE'].mean()),'parameter_stability':report['parameter_stability'].to_dict(orient='records'),'identifiability_map':report['identifiability_map'].to_dict(orient='records')}
    (out/'empirical_validation_report.json').write_text(json.dumps(_safe(summary), indent=2), encoding='utf-8')
    return out

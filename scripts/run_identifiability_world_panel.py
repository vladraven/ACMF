#!/usr/bin/env python3
from __future__ import annotations
import sys, json, argparse
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from acmf import LossConfig
from acmf.world_panel import load_world_panel, make_acmf_proxy_panel, top_countries_by_coverage
from acmf.identifiability import parameter_sensitivity_matrix, fisher_information_matrix, fim_diagnostics, parameter_correlation_from_fim, top_correlated_pairs, observation_design_score
THETA=np.array([0.8,0.5,0.3,0.08,0.2,0.4,0.6,0.03,0.5,0.5,0.5,0.5]); BASE=['P','Prod','A','Inst','F']; CAND=['Ch','M','G','V','R']
def analyze(df,country,start,end):
    data=make_acmf_proxy_panel(df,country,start,end); cfg=LossConfig(observed_vars=BASE,lambda_prior=0.0); sens=parameter_sensitivity_matrix(data,THETA,BASE,cfg); F=fisher_information_matrix(sens.S,ridge=1e-12); diag=fim_diagnostics(F,sens.parameter_names); corr=parameter_correlation_from_fim(F); gains=observation_design_score(data,THETA,BASE,CAND,cfg)
    return {'country':country,'years':[int(data['t'][0]),int(data['t'][-1])],'n_time_points':int(len(data['t'])),'rank':diag.rank,'condition_number':diag.condition_number,'min_eigenvalue':diag.min_eigenvalue,'weak_directions':diag.weak_directions[:3],'top_correlated_pairs':top_correlated_pairs(corr,sens.parameter_names)[:10],'observation_design_gain':gains}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--data',default=None); ap.add_argument('--start-year',type=int,default=1995); ap.add_argument('--end-year',type=int,default=2023); ap.add_argument('--top-n',type=int,default=5); ap.add_argument('--countries',nargs='*'); ap.add_argument('--output',default='output/identifiability_world_panel_report.json'); a=ap.parse_args()
    df=load_world_panel(a.data); countries=a.countries if a.countries else top_countries_by_coverage(df,n=a.top_n); results=[]
    for c in countries:
        try: results.append(analyze(df,c,a.start_year,a.end_year))
        except Exception as exc: results.append({'country':c,'error':str(exc)})
    summary={'dataset':'world_data_1995_2025.csv','start_year':a.start_year,'end_year':a.end_year,'countries':countries,'results':results}; out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(summary,indent=2),encoding='utf-8')
    compact=[({'country':r['country'],'rank':r['rank'],'condition_number':r['condition_number'],'best_added_observable':r['observation_design_gain'][0] if r['observation_design_gain'] else None,'top_pair':r['top_correlated_pairs'][0] if r['top_correlated_pairs'] else None} if 'error' not in r else r) for r in results]
    print(json.dumps(compact,indent=2)); print(f'saved: {out}')
if __name__=='__main__': main()

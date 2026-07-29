#!/usr/bin/env python3
from __future__ import annotations
import json, os
import numpy as np
from acmf import default_params, simulate, LossConfig
from acmf.identifiability import parameter_sensitivity_matrix, fisher_information_matrix, fim_diagnostics, parameter_correlation_from_fim, top_correlated_pairs, observation_design_score, windowed_identifiability

def make_data(span=(1970,2025), shock=False):
    p=default_params(alpha7=0.8,K_g=0.5,beta_neg=0.3,NaturalDecay=0.08,q1=0.2,q3=0.4,alpha1=0.6,b1=0.03)
    x0=np.array([0.3,0.4,0.5,0.5,0.5,0.3,0.6,0.5,2.0,500.0]); t,tr=simulate(x0,span,1.0,p)
    if shock:
        mid=len(t)//2; tr[mid:,5]=np.clip(tr[mid:,5]+np.linspace(0,0.25,len(t)-mid),0,1)
    data={'t':t}
    for name,idx in [('P',9),('Prod',1),('A',0),('Inst',6),('F',8),('Ch',2),('M',3),('G',4),('V',5),('R',7)]: data[name]=tr[:,idx]
    return data

def run_case(label,data):
    theta=np.array([0.8,0.5,0.3,0.08,0.2,0.4,0.6,0.03,0.5,0.5,0.5,0.5]); base=['P','Prod','A','Inst','F']; cand=['Ch','M','G','V','R']
    cfg=LossConfig(observed_vars=base,lambda_prior=0.0); r=parameter_sensitivity_matrix(data,theta,base,cfg); F=fisher_information_matrix(r.S); d=fim_diagnostics(F,r.parameter_names); corr=parameter_correlation_from_fim(F)
    t=data['t']; windows={'early':(float(t[0]),float(t[len(t)//2])),'late':(float(t[len(t)//2]),float(t[-1]))}
    return {'label':label,'rank':d.rank,'condition_number':d.condition_number,'min_eigenvalue':d.min_eigenvalue,'weak_directions':d.weak_directions[:3],'top_correlated_pairs':top_correlated_pairs(corr,r.parameter_names)[:10],'observation_design_gain':observation_design_score(data,theta,base,cand,cfg),'windowed':windowed_identifiability(data,theta,base,windows,cfg)}

def main():
    cases=[run_case('short_stable',make_data((1970,1975))),run_case('long_stable',make_data((1970,2025))),run_case('long_with_synthetic_v_shift',make_data((1970,2025),True))]
    os.makedirs('output',exist_ok=True); open('output/identifiability_synthetic_report.json','w').write(json.dumps(cases,indent=2))
    print(json.dumps(cases,indent=2)[:6000]); print('saved: output/identifiability_synthetic_report.json')
if __name__=='__main__': main()

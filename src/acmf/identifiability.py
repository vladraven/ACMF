from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Sequence
import numpy as np
from .calibration import ACMFObjective, LossConfig

STATE_INDEX={'A':0,'Prod':1,'Ch':2,'M':3,'G':4,'V':5,'Inst':6,'R':7,'F':8,'P':9}

@dataclass
class SensitivityResult:
    S: np.ndarray; theta: np.ndarray; parameter_names: List[str]; observable_names: List[str]; row_labels: List[str]; baseline_observables: np.ndarray
@dataclass
class FIMDiagnostics:
    F: np.ndarray; eigenvalues: np.ndarray; eigenvectors: np.ndarray; rank: int; condition_number: float; min_eigenvalue: float; max_eigenvalue: float; weak_directions: List[Dict]; parameter_names: List[str]

def _flat(traj,t,obs,time_mask=None):
    if time_mask is None: time_mask=np.ones(len(t),dtype=bool)
    vals=[]; labels=[]
    for o in obs:
        if o not in STATE_INDEX: raise ValueError(f'Unknown observable: {o}')
        vals.append(traj[time_mask, STATE_INDEX[o]])
        labels += [f'{o}@{float(tt):g}' for tt in t[time_mask]]
    return np.concatenate(vals), labels

def _pert(theta,j,step,bounds):
    lo,hi=bounds[j]; p=theta.copy(); m=theta.copy(); p[j]=min(theta[j]+step,hi); m[j]=max(theta[j]-step,lo); den=p[j]-m[j]
    if abs(den)<1e-15: raise ValueError('bad perturbation')
    return p,m,den

def parameter_sensitivity_matrix(data:Dict[str,np.ndarray], theta:Sequence[float], observables:Sequence[str], config:LossConfig|None=None, rel_step=1e-4, abs_step=1e-6, time_mask=None):
    theta=np.asarray(theta,dtype=float); obj=ACMFObjective(data,config); t=obj.t
    if time_mask is not None:
        time_mask=np.asarray(time_mask,dtype=bool)
    base=obj._integrate(theta); y0,labels=_flat(base,t,observables,time_mask)
    S=np.zeros((len(y0),len(theta)))
    for j,(lo,hi) in enumerate(obj.BOUNDS):
        step=max(abs_step, rel_step*max(abs(theta[j]), hi-lo, 1.0)); tp,tm,den=_pert(theta,j,step,obj.BOUNDS)
        yp,_=_flat(obj._integrate(tp),t,observables,time_mask); ym,_=_flat(obj._integrate(tm),t,observables,time_mask)
        S[:,j]=(yp-ym)/den
    return SensitivityResult(S,theta.copy(),list(obj.THETA_NAMES),list(observables),labels,y0)

def fisher_information_matrix(S, noise_std=1.0, ridge=0.0):
    S=np.asarray(S,dtype=float)
    if np.isscalar(noise_std): w=np.full(S.shape[0], 1.0/max(float(noise_std)**2,1e-300))
    else:
        ns=np.asarray(noise_std,dtype=float); w=1.0/np.maximum(ns**2,1e-300)
    F=S.T@(S*w[:,None])
    return F+ridge*np.eye(F.shape[0]) if ridge>0 else F

def fim_diagnostics(F, parameter_names=None, tol=1e-10, weak_count=5):
    F=np.asarray(F,dtype=float); names=list(parameter_names) if parameter_names is not None else [f'theta_{i}' for i in range(F.shape[0])]
    vals,vecs=np.linalg.eigh(0.5*(F+F.T)); order=np.argsort(vals); vals=vals[order]; vecs=vecs[:,order]; pos=vals[vals>tol]
    rank=len(pos); maxv=float(pos.max()) if len(pos) else 0.0; minpos=float(pos.min()) if len(pos) else 0.0; cond=float(maxv/minpos) if minpos>0 else float('inf')
    weak=[]
    for k in range(min(weak_count,len(vals))):
        v=vecs[:,k]; loads=sorted([{'parameter':names[i],'loading':float(v[i]),'abs_loading':float(abs(v[i]))} for i in range(len(names))], key=lambda x:x['abs_loading'], reverse=True)[:5]
        weak.append({'eigenvalue':float(vals[k]),'top_loadings':loads})
    return FIMDiagnostics(F,vals,vecs,int(rank),cond,float(vals[0]) if len(vals) else 0.0,maxv,weak,names)

def parameter_correlation_from_fim(F, ridge=1e-9):
    F=np.asarray(F,dtype=float); cov=np.linalg.pinv(F+ridge*np.eye(F.shape[0])); d=np.sqrt(np.maximum(np.diag(cov),0))
    return np.nan_to_num(cov/np.outer(d,d),nan=0.0,posinf=0.0,neginf=0.0)

def top_correlated_pairs(corr, parameter_names, threshold=0.85):
    names=list(parameter_names); out=[]
    for i in range(len(names)):
        for j in range(i+1,len(names)):
            c=float(corr[i,j])
            if abs(c)>=threshold: out.append({'pair':[names[i],names[j]],'corr':c,'abs_corr':abs(c)})
    return sorted(out,key=lambda x:x['abs_corr'],reverse=True)

def observation_design_score(data, theta, base_observables, candidate_observables, config=None, noise_std=1.0):
    base=parameter_sensitivity_matrix(data,theta,base_observables,config); bd=fim_diagnostics(fisher_information_matrix(base.S,noise_std),base.parameter_names); scores=[]
    for obs in candidate_observables:
        if obs in base_observables: continue
        r=parameter_sensitivity_matrix(data,theta,list(base_observables)+[obs],config); d=fim_diagnostics(fisher_information_matrix(r.S,noise_std),r.parameter_names)
        gain=bd.condition_number/d.condition_number if np.isfinite(bd.condition_number) and np.isfinite(d.condition_number) and d.condition_number>0 else np.nan
        scores.append({'added_observable':obs,'rank':d.rank,'condition_number':d.condition_number,'min_eigenvalue':d.min_eigenvalue,'condition_gain':float(gain) if np.isfinite(gain) else np.nan})
    return sorted(scores,key=lambda x:(x['rank'],-np.nan_to_num(x['condition_number'],nan=np.inf)),reverse=True)

def windowed_identifiability(data, theta, observables, windows, config=None, noise_std=1.0):
    t=np.asarray(data['t'],dtype=float); out={}
    for name,(lo,hi) in windows.items():
        mask=(t>=lo)&(t<=hi)
        if mask.sum()<2: out[name]={'error':'window has fewer than two time points'}; continue
        r=parameter_sensitivity_matrix(data,theta,observables,config,time_mask=mask); d=fim_diagnostics(fisher_information_matrix(r.S,noise_std),r.parameter_names)
        out[name]={'rank':d.rank,'condition_number':d.condition_number,'min_eigenvalue':d.min_eigenvalue,'weak_directions':d.weak_directions}
    return out

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List
import warnings
import numpy as np
from scipy.interpolate import interp1d
from scipy.optimize import differential_evolution, minimize
from .core import ACMFParams, default_params, rhs


def huber_loss(residual, delta=1.0):
    r=np.asarray(residual,dtype=float); a=np.abs(r)
    return float(np.mean(np.where(a<=delta,0.5*r*r,delta*(a-0.5*delta))))

def compute_derivative(y,t):
    y=np.asarray(y,dtype=float); t=np.asarray(t,dtype=float)
    if len(y)<2: return np.zeros_like(y)
    d=np.zeros_like(y); d[0]=(y[1]-y[0])/(t[1]-t[0]); d[-1]=(y[-1]-y[-2])/(t[-1]-t[-2])
    for i in range(1,len(y)-1): d[i]=(y[i+1]-y[i-1])/(t[i+1]-t[i-1])
    return d

@dataclass(frozen=True)
class PriorSpec:
    kind: str='uniform'; mu: float=0.0; sigma: float=1.0; a: float=2.0; b: float=2.0; weight: float=1.0
    def penalty(self, value, lower=None, upper=None):
        x=float(value); k=self.kind.lower()
        if k=='uniform': return 0.0
        if self.sigma<=0: raise ValueError('sigma must be positive')
        if k=='normal': return float(self.weight*0.5*((x-self.mu)/self.sigma)**2)
        if k=='lognormal':
            if x<=0: return 1e12
            z=(np.log(x)-self.mu)/self.sigma; return float(self.weight*0.5*z*z)
        if k=='beta':
            if lower is None or upper is None or upper<=lower: return 1e12
            u=float(np.clip((x-lower)/(upper-lower),1e-12,1-1e-12))
            return float(self.weight*(-(self.a-1)*np.log(u)-(self.b-1)*np.log(1-u)))
        raise ValueError(f'Unsupported prior kind: {self.kind}')

def default_prior_specs(theta_names=None):
    priors={
        'alpha7':PriorSpec('lognormal',mu=np.log(0.5),sigma=0.8,weight=0.2),
        'K_g':PriorSpec('lognormal',mu=np.log(0.4),sigma=0.6,weight=0.2),
        'beta_neg':PriorSpec('lognormal',mu=np.log(0.2),sigma=0.6,weight=0.2),
        'NaturalDecay':PriorSpec('lognormal',mu=np.log(0.04),sigma=0.7,weight=0.2),
        'q1':PriorSpec('beta',a=2,b=2,weight=0.05),'q3':PriorSpec('beta',a=2,b=2,weight=0.05),
        'alpha1':PriorSpec('lognormal',mu=np.log(0.4),sigma=0.8,weight=0.2),'b1':PriorSpec('lognormal',mu=np.log(0.04),sigma=0.8,weight=0.2),
        'Ch0':PriorSpec('beta',a=2,b=2,weight=0.05),'M0':PriorSpec('beta',a=2,b=2,weight=0.05),'G0':PriorSpec('beta',a=2,b=2,weight=0.05),'R0':PriorSpec('beta',a=2,b=2,weight=0.05)}
    return {k:v for k,v in priors.items() if theta_names is None or k in theta_names}

@dataclass
class LossConfig:
    observed_vars: List[str]=field(default_factory=lambda:['P','Prod','A','Inst','F'])
    lambda_deriv: float=0.5; delta_huber: float=1.0; lambda_prior: float=0.01
    priors: Dict[str,PriorSpec]=field(default_factory=dict)
    var_index: Dict[str,int]=field(default_factory=lambda:{'A':0,'Prod':1,'Ch':2,'M':3,'G':4,'V':5,'Inst':6,'R':7,'F':8,'P':9})

class ACMFObjective:
    THETA_NAMES=['alpha7','K_g','beta_neg','NaturalDecay','q1','q3','alpha1','b1','Ch0','M0','G0','R0']
    BOUNDS=[(0.05,2.0),(0.1,0.9),(0.05,0.5),(0.01,0.20),(0.0,1.0),(0.0,1.0),(0.05,1.0),(0.0,0.1),(0.0,1.0),(0.0,1.0),(0.0,1.0),(0.0,1.0)]
    def __init__(self,data,config=None):
        self.t=np.asarray(data['t'],dtype=float); self.data={k:np.asarray(v,dtype=float) for k,v in data.items() if k!='t'}
        self.config=config or LossConfig()
        if not self.config.priors: self.config.priors=default_prior_specs(self.THETA_NAMES)
        self.var_scale={}
        for var in self.config.observed_vars:
            if var in self.data:
                sd=float(np.std(self.data[var])); self.var_scale[var]=sd if sd>1e-12 else 1.0
    def _theta_to_params(self,theta):
        p=default_params(); theta=np.asarray(theta,dtype=float)
        p.alpha7,p.K_g,p.beta_neg,p.NaturalDecay=theta[0],theta[1],theta[2],theta[3]
        p.q1,p.q3,p.alpha1,p.b1=theta[4],theta[5],theta[6],theta[7]
        return p
    def _initial_state(self,theta):
        return np.array([self.data.get('A',[0.3])[0], self.data.get('Prod',[0.4])[0], theta[8], theta[9], theta[10], 0.3, self.data.get('Inst',[0.6])[0], theta[11], self.data.get('F',[2.0])[0], self.data.get('P',[500.0])[0]],dtype=float)
    @staticmethod
    def _project(x):
        y=np.asarray(x,dtype=float).copy(); y[:8]=np.clip(y[:8],0,1); y[8]=np.clip(y[8],0,4); y[9]=max(y[9],0.0); return y
    def _integrate(self,theta):
        p=self._theta_to_params(theta); x0=self._project(self._initial_state(theta)); t0,tf=float(self.t[0]),float(self.t[-1])
        dt=min(0.5,(tf-t0)/max(len(self.t)*2,10)); n=int(np.ceil((tf-t0)/dt))+1; tt=np.linspace(t0,tf,n); tr=np.zeros((n,10)); tr[0]=x0
        for i in range(1,n):
            h=tt[i]-tt[i-1]; x=tr[i-1]; k1=rhs(x,p); k2=rhs(x+0.5*h*k1,p); k3=rhs(x+0.5*h*k2,p); k4=rhs(x+h*k3,p); tr[i]=self._project(x+(h/6)*(k1+2*k2+2*k3+k4))
        out=np.zeros((len(self.t),10))
        for j in range(10): out[:,j]=interp1d(tt,tr[:,j],kind='linear',fill_value='extrapolate')(self.t)
        return out
    def prior_penalty(self,theta):
        total=0.0
        for i,n in enumerate(self.THETA_NAMES):
            spec=self.config.priors.get(n)
            if spec is not None: total+=spec.penalty(theta[i], *self.BOUNDS[i])
        return float(total)
    def __call__(self,theta):
        theta=np.asarray(theta,dtype=float)
        try: tr=self._integrate(theta)
        except Exception: return 1e10
        if not np.all(np.isfinite(tr)): return 1e10
        loss=0.0; nvars=0
        for var in self.config.observed_vars:
            if var not in self.data: continue
            idx=self.config.var_index[var]; scale=self.var_scale.get(var,1.0); y=self.data[var]; s=tr[:,idx]
            loss+=huber_loss((y-s)/scale,self.config.delta_huber)+self.config.lambda_deriv*huber_loss((compute_derivative(y,self.t)-compute_derivative(s,self.t))/scale,self.config.delta_huber); nvars+=1
        return float(loss/max(nvars,1)+self.config.lambda_prior*self.prior_penalty(theta))

@dataclass
class CalibrationResult:
    theta_opt: np.ndarray; loss_opt: float; hessian_inv: np.ndarray|None=None; cov_matrix: np.ndarray|None=None; corr_matrix: np.ndarray|None=None; mcmc_samples: np.ndarray|None=None; mcmc_acceptance_rate: float=0.0; diagnostics: Dict|None=None

def differential_evolution_fit(objective,bounds=None,maxiter=200,popsize=15,workers=1,seed=42,tol=1e-6):
    r=differential_evolution(objective,bounds or objective.BOUNDS,maxiter=maxiter,popsize=popsize,workers=workers,seed=seed,tol=tol,polish=False,disp=False); return r.x,float(r.fun)
def lbfgsb_refinement(objective,x0,bounds=None,maxiter=1000):
    r=minimize(objective,x0,method='L-BFGS-B',bounds=bounds or objective.BOUNDS,options={'maxiter':maxiter}); h=None
    try: h=np.array(r.hess_inv.todense())
    except Exception: pass
    return r.x,float(r.fun),h
def estimate_covariance(hess_inv, objective=None):
    if hess_inv is None: return None,None
    cov=np.asarray(hess_inv,dtype=float); d=np.sqrt(np.maximum(np.diag(cov),0)); corr=np.nan_to_num(cov/np.outer(d,d),nan=0.0,posinf=0.0,neginf=0.0)
    tri=corr[np.triu_indices_from(corr,k=1)]
    if tri.size and np.max(np.abs(tri))>0.85: warnings.warn(f"Multicollinearity detected: max|R|={np.max(np.abs(tri)):.3f}")
    return cov,corr
def dram_mcmc(objective,theta_map,cov_proposal=None,n_samples=1000,burn_in=200,adapt_interval=100,target_acceptance=0.25,seed=42):
    rng=np.random.default_rng(seed); theta_map=np.asarray(theta_map,dtype=float); n=len(theta_map); cov_proposal=np.eye(n)*1e-4 if cov_proposal is None else np.asarray(cov_proposal,dtype=float)
    cur=theta_map.copy(); ce=0.5*objective(cur)**2; samples=np.zeros((n_samples,n)); acc=0; log_scale=0.0
    for i in range(n_samples):
        if i>0 and i%adapt_interval==0: log_scale=float(np.clip(log_scale+(0.1 if acc/i>target_acceptance else -0.1),-5,2))
        prop=cur+rng.multivariate_normal(np.zeros(n),cov_proposal*np.exp(log_scale))
        for j,(lo,hi) in enumerate(objective.BOUNDS): prop[j]=np.clip(prop[j],lo,hi)
        pe=0.5*objective(prop)**2
        if pe<ce or rng.random()<np.exp(-(pe-ce)): cur=prop; ce=pe; acc+=1
        samples[i]=cur
    return samples[burn_in:], acc/max(n_samples,1)
def model_adequacy(objective,theta): return {'_overall':{'n_params':len(theta),'n_obs':sum(len(objective.data[v]) for v in objective.config.observed_vars if v in objective.data)}}
def run_calibration_pipeline(data,config=None,de_maxiter=5,mcmc_samples=200,mcmc_burn_in=50,seed=42):
    obj=ACMFObjective(data,config); x,loss=differential_evolution_fit(obj,maxiter=de_maxiter,seed=seed); x,loss,h=lbfgsb_refinement(obj,x); cov,corr=estimate_covariance(h,obj); smp,acc=dram_mcmc(obj,x,cov,n_samples=mcmc_samples,burn_in=mcmc_burn_in,seed=seed); return CalibrationResult(x,loss,h,cov,corr,smp,acc,model_adequacy(obj,x))

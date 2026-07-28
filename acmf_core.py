from __future__ import annotations
import numpy as np
STATE_NAMES=["A","Prod","Ch","M","G","V","Inst","R","F","P1","P2","P3"]
def rhs_acmf(t,y,p,D):
    N=int(p.get('N',len(y)//12)); X=np.asarray(y,float).reshape(N,12); d=np.zeros_like(X)
    A,Prod,Ch,M,G,V,Inst,R,F,P1,P2,P3=[X[:,i] for i in range(12)]
    d[:,0]=.04*A*(1-A/max(p.get('A_max',.95),1e-9)); d[:,1]=.08*A-.03*V
    d[:,2]=.03*(Inst-Ch); d[:,3]=.02*(Prod-M); d[:,4]=.02*(Inst-G); d[:,5]=.03*((P1+P3)/np.maximum(P2,1)-V); d[:,6]=.02*(G+Ch-2*Inst); d[:,7]=.02*(Ch+Inst-V-R)
    d[:,8]=p.get('lambda_fert',.05)*(p.get('k_sat',18)/10-F)-p.get('beta_fert_stress',.1)*V*F
    births=np.maximum(0,(p.get('b0',.005)+p.get('b1',.015)*F/4)*.49*.56*P2)
    d[:,9]=births-(p.get('mu1',.002)+p.get('gamma1',1/15))*P1
    d[:,10]=p.get('gamma1',1/15)*P1-(p.get('mu2',.005)+p.get('gamma2',1/48))*P2
    d[:,11]=p.get('gamma2',1/48)*P2-p.get('mu3',.035)*P3
    return d.ravel()

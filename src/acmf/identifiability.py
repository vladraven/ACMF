from __future__ import annotations
import numpy as np
from .calibration import residuals, CALIBRATION_PARAMS

def sensitivity_matrix(data, theta, variables, eps=1e-4):
    theta=np.asarray(theta,float); base=residuals(theta, data, variables); cols=[]
    for i,x in enumerate(theta):
        step=eps*max(abs(x),1.0); th=theta.copy(); th[i]+=step
        cols.append((residuals(th,data,variables)-base)/step)
    return np.column_stack(cols)

def fim_diagnostics(data, theta, variables):
    S=sensitivity_matrix(data,theta,variables); F=S.T@S + np.eye(S.shape[1])*1e-10
    vals, vecs=np.linalg.eigh(F); vals=np.maximum(vals,0)
    rank=int(np.linalg.matrix_rank(F, tol=1e-8)); cond=float(vals.max()/max(vals.min(),1e-12))
    weak=[]
    for k in np.argsort(vals)[:3]:
        loads=sorted([{'parameter':p,'loading':float(vecs[i,k]),'abs_loading':float(abs(vecs[i,k]))} for i,p in enumerate(CALIBRATION_PARAMS)], key=lambda d:d['abs_loading'], reverse=True)[:4]
        weak.append({'eigenvalue':float(vals[k]),'top_loadings':loads})
    return {'rank':rank,'condition_number':cond,'min_eigenvalue':float(vals.min()),'max_eigenvalue':float(vals.max()),'weak_directions':weak}

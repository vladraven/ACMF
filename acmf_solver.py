from __future__ import annotations
import numpy as np
from scipy.integrate import solve_ivp
from acmf_core import rhs_acmf
def solve_acmf(y0,t_span,p,D,**kw): return solve_ivp(lambda t,y: rhs_acmf(t,y,p,D),t_span,np.asarray(y0,float).ravel(),method=kw.get('method','Radau'),rtol=kw.get('rtol',1e-6),atol=kw.get('atol',1e-8),max_step=kw.get('max_step',1.0))


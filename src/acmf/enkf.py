from __future__ import annotations
import numpy as np
from .solver import rk4_step
from .core import default_params

def enkf_assimilate(observations, x0, steps: int, ensemble_size: int=20, obs_index: int=9, obs_noise: float=1.0, seed: int=0):
    rng=np.random.default_rng(seed); ens=np.tile(np.asarray(x0,float), (ensemble_size,1)) + rng.normal(0,0.01,(ensemble_size,len(x0)))
    p=default_params(); means=[]
    for k in range(steps):
        for i in range(ensemble_size): ens[i]=rk4_step(ens[i],1.0,p)
        y=observations[k] if k < len(observations) else np.nan
        if np.isfinite(y):
            hx=ens[:,obs_index]; var=float(np.var(hx)+obs_noise**2); cov=np.mean((ens-ens.mean(0))*(hx-hx.mean())[:,None],0)
            K=cov/var
            ens += (y + rng.normal(0,obs_noise,ensemble_size) - hx)[:,None]*K[None,:]
        means.append(ens.mean(0).copy())
    return np.array(means)

from __future__ import annotations
import pandas as pd
from .identifiability import fim_diagnostics

def score_candidate_observables(data, theta, base_observables, candidate_observables):
    base=fim_diagnostics(data,theta,base_observables); rows=[]
    for c in candidate_observables:
        if c in base_observables: continue
        d=fim_diagnostics(data,theta,list(base_observables)+[c])
        rows.append({'candidate':c,'rank_gain':d['rank']-base['rank'],'condition_gain':base['condition_number']/d['condition_number'] if d['condition_number'] else 0,'min_eigenvalue_gain':d['min_eigenvalue']-base['min_eigenvalue'],'score':(d['rank']-base['rank'])*1e6 + (d['min_eigenvalue']-base['min_eigenvalue'])})
    return pd.DataFrame(rows).sort_values(['rank_gain','score'], ascending=[False,False]).reset_index(drop=True) if rows else pd.DataFrame()

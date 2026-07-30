from __future__ import annotations
import numpy as np
import pandas as pd

AGE_GROUPS = ['0_14','15_64','65_plus']

def fixed_alpha(a: float=0.2) -> dict:
    if not (0.0 <= a <= 1.0):
        raise ValueError('a must be in [0, 1]')
    return {'0_14_to_15_64':float(a), '15_64_to_65_plus':float(a), 'retention_65_plus':1.0-float(a)}

def transition_matrix(alpha_0_14_to_15_64: float, alpha_15_64_to_65_plus: float, mortality_65_plus: float=0.0) -> pd.DataFrame:
    for name, val in [('alpha_0_14_to_15_64',alpha_0_14_to_15_64),('alpha_15_64_to_65_plus',alpha_15_64_to_65_plus),('mortality_65_plus',mortality_65_plus)]:
        if not (0.0 <= val <= 1.0):
            raise ValueError(f'{name} must be in [0, 1]')
    mat=np.array([
        [1-alpha_0_14_to_15_64, 0.0, 0.0],
        [alpha_0_14_to_15_64, 1-alpha_15_64_to_65_plus, 0.0],
        [0.0, alpha_15_64_to_65_plus, 1-mortality_65_plus],
    ], dtype=float)
    return pd.DataFrame(mat, index=AGE_GROUPS, columns=AGE_GROUPS)

def apply_transition(population_by_age: dict, matrix: pd.DataFrame) -> dict:
    vec=np.array([float(population_by_age[g]) for g in AGE_GROUPS])
    nxt=matrix.to_numpy() @ vec
    return dict(zip(AGE_GROUPS, map(float, nxt)))

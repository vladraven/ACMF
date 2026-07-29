#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from acmf import default_params, simulate
from acmf.observation_designer import greedy_observation_design, minimal_observation_set, result_to_dict, DEFAULT_THETA


def make_data():
    p = default_params(alpha7=0.8, K_g=0.5, beta_neg=0.3, NaturalDecay=0.08, q1=0.2, q3=0.4, alpha1=0.6, b1=0.03)
    x0 = np.array([0.3,0.4,0.5,0.5,0.5,0.3,0.6,0.5,2.0,500.0])
    t, tr = simulate(x0, (1970, 2025), 1.0, p)
    data = {'t': t}
    for name, idx in [('P',9),('Prod',1),('A',0),('Inst',6),('F',8),('Ch',2),('M',3),('G',4),('V',5),('R',7)]:
        data[name] = tr[:, idx]
    return data


def main():
    data = make_data()
    greedy = greedy_observation_design(data, theta=DEFAULT_THETA, k=5)
    minimal = minimal_observation_set(data, theta=DEFAULT_THETA, required_observables=['P'], target_rank=12, max_observables=10)
    out = {'greedy_k5': result_to_dict(greedy), 'minimal_rank12': result_to_dict(minimal)}
    Path('output').mkdir(exist_ok=True)
    Path('output/observation_designer_synthetic.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    print(json.dumps(out, indent=2)[:6000])
    print('saved: output/observation_designer_synthetic.json')
if __name__ == '__main__':
    main()

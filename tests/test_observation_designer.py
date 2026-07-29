import numpy as np
from acmf import default_params, simulate, __version__
from acmf.observation_designer import score_candidate_observables, greedy_observation_design, minimal_observation_set, DEFAULT_THETA, result_to_dict


def synthetic_data():
    p = default_params(alpha7=0.8, K_g=0.5, beta_neg=0.3, NaturalDecay=0.08, q1=0.2, q3=0.4, alpha1=0.6, b1=0.03)
    x0 = np.array([0.3,0.4,0.5,0.5,0.5,0.3,0.6,0.5,2.0,500.0])
    t, tr = simulate(x0, (1970, 1980), 1.0, p)
    data = {'t': t}
    for name, idx in [('P',9),('Prod',1),('A',0),('Inst',6),('F',8),('Ch',2),('M',3),('G',4),('V',5),('R',7)]:
        data[name] = tr[:, idx]
    return data


def test_version_incremented_to_observation_designer():
    assert __version__ == '3.3.1.5-clean-observation-designer'


def test_score_candidate_observables():
    data = synthetic_data()
    scores = score_candidate_observables(data, DEFAULT_THETA, ['P','Prod','A','Inst','F'], ['Ch','M','G','V','R'])
    assert len(scores) == 5
    assert scores.iloc[0]['candidate'] in {'Ch','M','G','V','R'}
    assert 'condition_gain' in scores.columns


def test_greedy_observation_design_k2():
    data = synthetic_data()
    result = greedy_observation_design(data, theta=DEFAULT_THETA, k=2)
    assert len(result.selected_observables) == 7
    assert len(result.history) == 2
    assert result.final_rank >= 1
    as_dict = result_to_dict(result)
    assert 'selected_observables' in as_dict


def test_minimal_observation_set_progresses():
    data = synthetic_data()
    result = minimal_observation_set(data, theta=DEFAULT_THETA, required_observables=['P'], target_rank=6, max_observables=10)
    assert 'P' in result.selected_observables
    assert len(result.selected_observables) >= 1
    assert result.final_rank >= 1

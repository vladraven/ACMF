import pytest
pytestmark = pytest.mark.slow
import numpy as np
from acmf import default_params, simulate, LossConfig
from acmf.identifiability import parameter_sensitivity_matrix, fisher_information_matrix, fim_diagnostics, parameter_correlation_from_fim, top_correlated_pairs, observation_design_score, windowed_identifiability

def synthetic_data():
    p=default_params(alpha7=0.8,K_g=0.5,beta_neg=0.3,NaturalDecay=0.08,q1=0.2,q3=0.4,alpha1=0.6,b1=0.03)
    x0=np.array([0.3,0.4,0.5,0.5,0.5,0.3,0.6,0.5,2.0,500.0]); t,tr=simulate(x0,(1970,1975),1.0,p)
    data={'t':t}
    for name,idx in [('P',9),('Prod',1),('A',0),('Inst',6),('F',8),('Ch',2),('M',3),('G',4),('V',5),('R',7)]: data[name]=tr[:,idx]
    return data

def theta(): return np.array([0.8,0.5,0.3,0.08,0.2,0.4,0.6,0.03])

def test_sensitivity_fim_shapes():
    data=synthetic_data(); obs=['P','Prod','A','Inst','F']; res=parameter_sensitivity_matrix(data,theta(),obs,LossConfig(observed_vars=obs,lambda_prior=0.0))
    assert res.S.shape == (len(data['t'])*len(obs), 8)
    diag=fim_diagnostics(fisher_information_matrix(res.S),res.parameter_names)
    assert diag.rank >= 1 and len(diag.weak_directions) > 0

def test_correlation_design_windowed():
    data=synthetic_data(); obs=['P','Prod','A','Inst','F']; cfg=LossConfig(observed_vars=obs,lambda_prior=0.0)
    res=parameter_sensitivity_matrix(data,theta(),obs,cfg); corr=parameter_correlation_from_fim(fisher_information_matrix(res.S))
    assert len(top_correlated_pairs(corr,res.parameter_names,threshold=0.0)) > 0
    assert len(observation_design_score(data,theta(),obs,['Ch','M','G','V','R'],cfg)) == 5
    w=windowed_identifiability(data,theta(),obs,{'early':(1970,1972),'late':(1973,1975)},cfg)
    assert 'rank' in w['early'] and 'rank' in w['late']

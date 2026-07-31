import numpy as np
import pandas as pd
import acmf
from acmf.world_panel import TrainFittedScaler, load_world_panel, make_acmf_proxy_panel
from acmf.calibration import ACMFObjective, DEFAULT_THETA
from acmf.model_levels import available_model_levels, observed_vars_for_level


def test_v4_version():
    assert acmf.__version__ == '4.0.0-stable-baseline'


def test_train_fitted_scaler_does_not_leak_validation_extreme():
    train = pd.Series([1.0, 2.0, 3.0])
    validation = pd.Series([1000000.0])
    scaler = TrainFittedScaler.fit(train)
    assert scaler.minimum == 1.0
    assert scaler.maximum == 3.0
    transformed = scaler.transform(validation)
    assert transformed[0] == 1.0
    # The extreme validation value is clipped after using train-fitted min/max;
    # it must not change scaler.maximum to 1000000.
    assert scaler.maximum == 3.0


def test_proxy_panel_fits_scalers_on_train_end():
    df = load_world_panel()
    data = make_acmf_proxy_panel(df, 'Canada', 2010, 2014, fit_end_year=2012)
    assert len(data['t']) == 5
    assert {'P','Prod','A','Inst','F','Ch','M','G','V','R'}.issubset(data.keys())
    assert np.all(np.isfinite(data['Prod']))


def test_acmf_objective_uses_observed_initial_conditions():
    df = load_world_panel()
    data = make_acmf_proxy_panel(df, 'Canada', 2010, 2014, fit_end_year=2012)
    obj = ACMFObjective(data)
    assert obj.THETA_NAMES == ['alpha7','K_g','beta_neg','NaturalDecay','q1','q3','alpha1','b1']
    assert len(obj.BOUNDS) == 8
    x0 = obj._initial_state()
    assert x0.shape == (10,)
    assert np.isclose(x0[0], data['A'][0])
    assert np.isclose(x0[2], data['Ch'][0])
    assert np.isclose(x0[7], data['R'][0])
    assert len(DEFAULT_THETA) == 8


def test_reduced_model_levels_are_explicit():
    assert available_model_levels() == ['R3','R5','R7','FULL10']
    assert observed_vars_for_level('R3') == ['P','Prod','Inst']
    assert observed_vars_for_level('R5') == ['P','Prod','A','Inst','F']
    assert observed_vars_for_level('FULL10') == ['P','Prod','A','Inst','F','Ch','M','G','V','R']

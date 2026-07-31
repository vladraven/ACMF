import pytest
pytestmark = pytest.mark.slow
import numpy as np
import pandas as pd
from acmf import __version__
from acmf.world_panel import load_world_panel, make_acmf_proxy_panel
from acmf.validation_metrics import metrics_for_series
from acmf.empirical_validation import run_country_validation, run_core5_validation, indicator_ablation_study, backtest_2008
from acmf.enkf import enkf_assimilate


def test_version():
    assert __version__ == '4.0.0-stable-baseline'


def test_world_panel_proxy():
    df = load_world_panel()
    data = make_acmf_proxy_panel(df, 'Canada', 2010, 2014)
    assert len(data['t']) == 5
    assert {'P','Prod','A','Inst','F'}.issubset(data.keys())


def test_metrics():
    m = metrics_for_series([1,2,3], [1,2,4])
    assert m['RMSE'] > 0
    assert 'R2' in m


def test_country_validation_smoke():
    r = run_country_validation('Canada', train_start=2010, train_end=2012, validation_start=2013, validation_end=2014, seeds=(0,), max_nfev=8)
    assert not r['runs'].empty
    assert not r['best_metrics'].empty
    assert 'best_identifiability' in r


def test_core5_validation_two_countries_smoke():
    r = run_core5_validation(['Canada','Germany'], train_start=2010, train_end=2012, validation_start=2013, validation_end=2014, seeds=(0,), max_nfev=6)
    assert set(r['runs']['country']) == {'Canada','Germany'}
    assert not r['parameter_stability'].empty
    assert not r['identifiability_map'].empty


def test_ablation_and_backtest_smoke():
    a = indicator_ablation_study(country='Canada', train_start=2010, train_end=2012, validation_start=2013, validation_end=2014, seed=0)
    assert len(a) >= 1
    b = backtest_2008('Canada', seed=0)
    assert not b['best_metrics'].empty


def test_enkf_smoke():
    x0 = np.array([0.3,0.4,0.5,0.5,0.5,0.3,0.6,0.5,2.0,500.0])
    out = enkf_assimilate([500,501,502], x0, steps=3, ensemble_size=5)
    assert out.shape == (3,10)

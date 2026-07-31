from pathlib import Path
import ast
import pytest
import pandas as pd
from acmf import __version__
from acmf.config import load_calibration_profile, load_parameter_config
from acmf.exceptions import ManualDownloadRequired
from acmf.data_fetchers.innovation import fetch_unesco_rd
from acmf.data_fetchers.world_values import fetch_wvs_manual
from acmf.data_fetchers.resilience import fetch_vdem_manual
from acmf.aging_transition_matrix import transition_matrix, apply_transition
from acmf.demography_age_structured import cohort_label

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src' / 'acmf'


def test_version_quality_hardening():
    assert __version__ == '4.0.0-stable-baseline'


def test_config_profiles_are_valid():
    smoke = load_calibration_profile('smoke')
    research = load_calibration_profile('research')
    params = load_parameter_config('baseline')
    assert smoke.max_nfev < research.max_nfev
    assert research.max_nfev >= 100
    assert 'alpha7' in params.parameters


def test_manual_fetchers_raise_explicit_errors():
    for fn in [fetch_unesco_rd, fetch_wvs_manual, fetch_vdem_manual]:
        with pytest.raises(ManualDownloadRequired):
            fn()


def test_no_empty_dataframe_placeholder_returns():
    offenders=[]
    for path in SRC.rglob('*.py'):
        text=path.read_text(encoding='utf-8')
        if 'return pd.DataFrame()' in text or 'return pandas.DataFrame()' in text:
            offenders.append(str(path.relative_to(ROOT)))
    assert offenders == []


def test_no_return_locals_in_model_code():
    offenders=[]
    for path in SRC.rglob('*.py'):
        text=path.read_text(encoding='utf-8')
        if 'return locals()' in text:
            offenders.append(str(path.relative_to(ROOT)))
    assert offenders == []


def test_no_broad_exception_silencing():
    offenders=[]
    for path in SRC.rglob('*.py'):
        tree=ast.parse(path.read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                broad = node.type is None or (isinstance(node.type, ast.Name) and node.type.id == 'Exception')
                if broad:
                    body_types=[type(x).__name__ for x in node.body]
                    if 'Pass' in body_types:
                        offenders.append(str(path.relative_to(ROOT)))
    assert offenders == []


def test_age_transition_is_real_matrix():
    mat = transition_matrix(0.1, 0.05, 0.02)
    assert mat.shape == (3, 3)
    nxt = apply_transition({'0_14': 100, '15_64': 200, '65_plus': 50}, mat)
    assert set(nxt) == {'0_14', '15_64', '65_plus'}
    assert nxt['15_64'] > 0


def test_cohort_label_raises_unknown_age():
    assert cohort_label(64) == '15_64'
    with pytest.raises(ValueError):
        cohort_label(121)

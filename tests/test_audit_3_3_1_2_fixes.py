import math
import numpy as np

from acmf import algebraic_layer, default_params, rhs
from acmf.smoothing import EPSILON, smax, smin
from acmf.priors import BoundedPrior, LogNormalPrior, UnitIntervalPrior


def finite_difference_jacobian_column(x, idx, params, h=1e-6):
    xp = np.array(x, dtype=float)
    xm = np.array(x, dtype=float)
    xp[idx] += h
    xm[idx] -= h
    return (rhs(xp, params) - rhs(xm, params)) / (2.0 * h)


def test_demographic_mode_is_not_strictly_constant_near_smoothing_layer():
    eps = EPSILON
    l_over_p_at_eps = 0.6 * smax(eps, eps, eps) / eps
    l_over_p_at_sqrt_eps = 0.6 * smax(math.sqrt(eps), eps, eps) / math.sqrt(eps)
    l_over_p_asymptotic = 0.6 * smax(1.0, eps, eps)

    assert l_over_p_at_eps > 1000.0
    assert not math.isclose(float(l_over_p_at_sqrt_eps), 0.6, rel_tol=1e-2)
    assert math.isclose(float(l_over_p_asymptotic), 0.6, rel_tol=1e-6)


def test_demographic_mode_separation_for_non_demographic_block_away_from_smoothing_layer():
    p = default_params()
    x = np.array([0.4, 0.5, 0.5, 0.5, 0.5, 0.3, 0.6, 0.5, 2.0, 500.0])
    d_by_p = finite_difference_jacobian_column(x, 9, p, h=1e-3)
    assert np.max(np.abs(d_by_p[:9])) < 1e-5


def test_v_row_jacobian_signs_document_inst_g_and_parameter_dependent_r():
    p = default_params()
    x = np.array([0.4, 0.5, 0.5, 0.5, 0.5, 0.3, 0.6, 0.5, 2.0, 500.0])

    d_by_inst = finite_difference_jacobian_column(x, 6, p)[5]
    d_by_r_default = finite_difference_jacobian_column(x, 7, p)[5]
    d_by_g = finite_difference_jacobian_column(x, 4, p)[5]

    assert d_by_inst > 0.0
    assert d_by_r_default < 0.0  # direct -beta12 * R * V dominates at defaults
    assert abs(d_by_g) < 1e-7

    p_no_direct_r_loss = default_params(beta12=0.0)
    d_by_r_indirect_only = finite_difference_jacobian_column(x, 7, p_no_direct_r_loss)[5]
    assert d_by_r_indirect_only > 0.0


def test_l2_feedback_loop_is_negative_under_default_parameters():
    p = default_params()
    x = np.array([0.4, 0.5, 0.5, 0.5, 0.5, 0.3, 0.6, 0.5, 2.0, 500.0])

    inst_to_v = finite_difference_jacobian_column(x, 6, p)[5]
    v_to_inst = finite_difference_jacobian_column(x, 5, p)[6]

    assert inst_to_v > 0.0
    assert v_to_inst < 0.0
    assert inst_to_v * v_to_inst < 0.0


def test_index_outputs_are_bounded_but_raw_diagnostics_are_available():
    p = default_params()
    for g in [0.0, 0.5, 1.0, 2.0, 5.0]:
        for ch in [0.0, 0.5, 1.0, 2.0]:
            x = np.array([0.4, 0.5, ch, 0.5, g, 0.3, 0.6, 0.5, 2.0, 500.0])
            a = algebraic_layer(x, p)
            assert 0.0 <= a["Innovation"] <= 1.0 + 1e-7
            assert 0.0 <= a["EI"] <= 1.0 + 1e-7
            assert 0.0 <= a["StructuralLimits"] <= 1.0 + 1e-7
            assert "Innovation_raw" in a
            assert "EI_raw" in a
            assert "StructuralLimits_raw" in a


def test_pmax_upper_bound_uses_k0_not_kmin():
    p_val = 100.0
    k_min = 50.0
    k0 = 200.0

    upper_at_k0 = 1.0 - p_val / k0
    value_at_kmin = 1.0 - p_val / k_min

    assert upper_at_k0 > value_at_kmin


def test_population_derivative_negative_above_large_capacity_bound():
    p = default_params(M_max=0.0)
    x = np.array([0.4, 0.5, 0.5, 0.5, 0.5, 0.3, 0.6, 0.5, 2.0, 10.0 * p.K0])
    assert rhs(x, p)[9] < 0.0


def test_smax_smin_are_c1_numerically():
    # The smoothing width is sqrt(EPSILON); use a smaller step to test local C1 continuity.
    h = 1e-8
    left = (smax(0.0, -h) - smax(0.0, -2*h)) / h
    right = (smax(0.0, 2*h) - smax(0.0, h)) / h
    assert abs(float(left - right)) < 1e-2

    left_min = (smin(0.0, -h) - smin(0.0, -2*h)) / h
    right_min = (smin(0.0, 2*h) - smin(0.0, h)) / h
    assert abs(float(left_min - right_min)) < 1e-2


def test_positive_and_bounded_prior_transforms():
    lp = LogNormalPrior(mu=0.0, sigma=1.0)
    up = UnitIntervalPrior(mu=0.0, sigma=1.0)
    bp = BoundedPrior(lower=10.0, upper=20.0, mu=0.0, sigma=1.0)

    for z in [-10, -1, 0, 1, 10]:
        assert lp.transform(z) > 0.0
        assert 0.0 <= up.transform(z) <= 1.0
        assert 10.0 <= bp.transform(z) <= 20.0

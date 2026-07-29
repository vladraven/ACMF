import math
import numpy as np

from acmf import (
    ACMFObjective, LossConfig, algebraic_layer, check_P_invariance,
    check_demographic_decoupling, compute_derivative, default_params,
    dsmax_dx, dsmax_dy, dsmin_dx, dsmin_dy, feedback_loops_summary,
    huber_loss, numerical_jacobian, rhs, simulate, spectrum_analysis,
)
from acmf.calibration import differential_evolution_fit, lbfgsb_refinement, dram_mcmc, model_adequacy
from acmf.smoothing import EPSILON, smax


def test_indices_are_bounded_and_raw_values_are_available():
    p = default_params()
    x = np.array([0.0, 0.0, 0.0, 0.5, 5.0, 1.0, 0.0, 0.0, 0.0, 100.0])
    a = algebraic_layer(x, p)
    for key in ["Env", "EI", "StructuralLimits", "Innovation"]:
        assert 0.0 <= a[key] <= 1.0 + 1e-8
    for key in ["Env_raw", "EI_raw", "StructuralLimits_raw", "Innovation_raw"]:
        assert key in a
    assert a["EI_raw"] >= a["EI"]
    assert a["StructuralLimits_raw"] >= a["StructuralLimits"]


def test_v_r_sign_is_parameter_dependent_not_universal():
    x = np.array([0.4, 0.5, 0.5, 0.5, 0.5, 0.3, 0.6, 0.5, 2.0, 500.0])
    p = default_params()
    J_default = numerical_jacobian(x, p)
    assert J_default[5, 6] > 0.0
    assert J_default[5, 7] < 0.0
    assert abs(J_default[5, 4]) < 1e-6

    p_indirect_only = default_params(beta12=0.0)
    J_indirect = numerical_jacobian(x, p_indirect_only)
    assert J_indirect[5, 7] > 0.0


def test_demographic_decoupling_and_p_invariance_diagnostics():
    x = np.array([0.4, 0.5, 0.5, 0.5, 0.5, 0.3, 0.6, 0.5, 2.0, 1e6])
    result = check_demographic_decoupling(x, tol=1e-4)
    assert result["passed"]

    p = default_params(M_max=0.0)
    for _, dP in check_P_invariance([1e6, 1e7], p):
        assert dP < 0.0


def test_smoothing_derivatives_are_finite_and_sum_to_one():
    x, y = 0.2, 0.1
    assert math.isfinite(float(dsmax_dx(x, y)))
    assert math.isfinite(float(dsmax_dy(x, y)))
    assert math.isclose(float(dsmax_dx(x, y) + dsmax_dy(x, y)), 1.0, rel_tol=1e-12)
    assert math.isclose(float(dsmin_dx(x, y) + dsmin_dy(x, y)), 1.0, rel_tol=1e-12)


def test_demographic_load_ratio_is_nonlinear_near_epsilon():
    eps = EPSILON
    assert 0.6 * smax(eps, eps, eps) / eps > 1000.0
    assert math.isclose(float(0.6 * smax(1.0, eps, eps)), 0.6, rel_tol=1e-6)


def test_solver_and_spectrum_smoke():
    x0 = np.array([0.3, 0.4, 0.5, 0.5, 0.5, 0.3, 0.6, 0.5, 2.0, 500.0])
    t, traj = simulate(x0, (0.0, 1.0), dt=0.1)
    assert traj.shape == (len(t), 10)
    assert np.all(np.isfinite(traj))
    spec = spectrum_analysis(x0)
    assert "max_real" in spec
    assert "P_mode_eigenvalue" in spec
    assert "Inst" in feedback_loops_summary(x0)


def test_calibration_objective_and_short_pipeline_components():
    t = np.linspace(0.0, 2.0, 5)
    x0 = np.array([0.3, 0.4, 0.5, 0.5, 0.5, 0.3, 0.6, 0.5, 2.0, 500.0])
    _, traj = simulate(x0, (0.0, 2.0), dt=0.5)
    # match observation grid
    data = {"t": t, "P": np.interp(t, np.linspace(0.0, 2.0, len(traj)), traj[:, 9]), "A": np.interp(t, np.linspace(0.0, 2.0, len(traj)), traj[:, 0])}
    config = LossConfig(observed_vars=["P", "A"], lambda_deriv=0.1)
    objective = ACMFObjective(data, config)
    theta0 = np.array([0.3, 0.4, 0.2, 0.04, 0.15, 0.3, 0.4, 0.04, 0.5, 0.5, 0.5, 0.5])
    loss = objective(theta0)
    assert np.isfinite(loss)
    assert huber_loss([0.0, 1.0]) >= 0.0
    assert compute_derivative(np.array([0.0, 1.0, 4.0]), np.array([0.0, 1.0, 2.0])).shape == (3,)
    metrics = model_adequacy(objective, theta0)
    assert "_overall" in metrics
    samples, acc = dram_mcmc(objective, theta0, n_samples=20, burn_in=5, seed=1)
    assert samples.shape[1] == len(theta0)
    assert 0.0 <= acc <= 1.0


def test_calibration_priors_are_integrated_into_objective():
    from acmf import PriorSpec
    t = np.linspace(0.0, 1.0, 3)
    data = {"t": t, "P": np.array([500.0, 499.0, 498.0]), "A": np.array([0.3, 0.31, 0.32])}
    base_theta = np.array([0.3, 0.4, 0.2, 0.04, 0.15, 0.3, 0.4, 0.04, 0.5, 0.5, 0.5, 0.5])
    config_no_prior = LossConfig(observed_vars=["P", "A"], lambda_deriv=0.1, lambda_prior=0.0)
    obj_no_prior = ACMFObjective(data, config_no_prior)
    config_with_prior = LossConfig(
        observed_vars=["P", "A"],
        lambda_deriv=0.1,
        lambda_prior=1.0,
        priors={"alpha7": PriorSpec(kind="normal", mu=10.0, sigma=0.1, weight=1.0)},
    )
    obj_with_prior = ACMFObjective(data, config_with_prior)
    assert obj_with_prior.prior_penalty(base_theta) > 0.0
    assert obj_with_prior(base_theta) > obj_no_prior(base_theta)

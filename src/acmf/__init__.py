"""ACMF 3.3.1.2 package."""

from .smoothing import (
    EPSILON, smax, smin, sigmoid,
    dsmax_dx, dsmax_dy, dsmin_dx, dsmin_dy,
)
from .core import ACMFParams, default_params, algebraic_layer, rhs, unpack_state
from .adaptive_dynamics import AdaptiveWeights, adaptive_dynamics_layer
from .diagnostics import (
    numerical_jacobian, sign_matrix, check_demographic_decoupling,
    check_P_invariance, spectrum_analysis, feedback_loops_summary,
)
from .solver import rk4_step, simulate, scenario_run, project_state
from .priors import LogNormalPrior, UnitIntervalPrior, BoundedPrior
from .benchmark_models import (
    random_walk_forecast, linear_trend_fit, linear_trend_forecast,
    arima_110_fit, arima_110_forecast, var1_fit, var1_forecast,
    fit_all_benchmarks, forecast_all_benchmarks,
)
from .diebold_mariano import dm_test, compare_acmf_vs_benchmarks
from .enkf import ACMFEnKF
from .digital_twin import DigitalTwin
from .calibration import (
    LossConfig, ACMFObjective, CalibrationResult, huber_loss, compute_derivative,
    differential_evolution_fit, lbfgsb_refinement, estimate_covariance, dram_mcmc,
    model_adequacy, run_calibration_pipeline,
)

__version__ = "3.3.1.2-audit-corrected"

__all__ = [
    "EPSILON", "smax", "smin", "sigmoid", "dsmax_dx", "dsmax_dy", "dsmin_dx", "dsmin_dy",
    "ACMFParams", "default_params", "algebraic_layer", "rhs", "unpack_state",
    "AdaptiveWeights", "adaptive_dynamics_layer",
    "numerical_jacobian", "sign_matrix", "check_demographic_decoupling",
    "check_P_invariance", "spectrum_analysis", "feedback_loops_summary",
    "rk4_step", "simulate", "scenario_run", "project_state",
    "LogNormalPrior", "UnitIntervalPrior", "BoundedPrior",
    "LossConfig", "ACMFObjective", "CalibrationResult", "huber_loss", "compute_derivative",
    "differential_evolution_fit", "lbfgsb_refinement", "estimate_covariance", "dram_mcmc",
    "model_adequacy", "run_calibration_pipeline",
    "random_walk_forecast", "linear_trend_fit", "linear_trend_forecast",
    "arima_110_fit", "arima_110_forecast", "var1_fit", "var1_forecast",
    "fit_all_benchmarks", "forecast_all_benchmarks",
    "dm_test", "compare_acmf_vs_benchmarks", "ACMFEnKF", "DigitalTwin",
]

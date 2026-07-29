"""ACMF 3.3.1.2 audit-corrected research package."""
from .smoothing import EPSILON, smax, smin, sigmoid, dsmax_dx, dsmax_dy, dsmin_dx, dsmin_dy
from .core import ACMFParams, default_params, algebraic_layer, rhs, unpack_state
from .adaptive_dynamics import AdaptiveWeights, adaptive_dynamics_layer
from .solver import project_state, rk4_step, simulate, scenario_run
from .calibration import PriorSpec, default_prior_specs, LossConfig, ACMFObjective, CalibrationResult, huber_loss, compute_derivative, run_calibration_pipeline
from .identifiability import parameter_sensitivity_matrix, fisher_information_matrix, fim_diagnostics, parameter_correlation_from_fim, top_correlated_pairs, observation_design_score, windowed_identifiability
__version__ = "3.3.1.2-audit-corrected-identifiability"
__all__ = [
    'EPSILON','smax','smin','sigmoid','dsmax_dx','dsmax_dy','dsmin_dx','dsmin_dy',
    'ACMFParams','default_params','algebraic_layer','rhs','unpack_state',
    'AdaptiveWeights','adaptive_dynamics_layer','project_state','rk4_step','simulate','scenario_run',
    'PriorSpec','default_prior_specs','LossConfig','ACMFObjective','CalibrationResult','huber_loss','compute_derivative','run_calibration_pipeline',
    'parameter_sensitivity_matrix','fisher_information_matrix','fim_diagnostics','parameter_correlation_from_fim','top_correlated_pairs','observation_design_score','windowed_identifiability'
]

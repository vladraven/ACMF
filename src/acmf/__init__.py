"""ACMF 3.3.1.4 clean datacube src-layout package."""
from .smoothing import EPSILON, smax, smin, sigmoid, dsmax_dx, dsmax_dy, dsmin_dx, dsmin_dy
from .core import ACMFParams, default_params, algebraic_layer, rhs, unpack_state, STATE_NAMES
from .adaptive_dynamics import AdaptiveWeights, adaptive_dynamics_layer
from .solver import project_state, rk4_step, simulate, scenario_run
from .calibration import PriorSpec, default_prior_specs, LossConfig, ACMFObjective, CalibrationResult, huber_loss, compute_derivative, run_calibration_pipeline
from .identifiability import parameter_sensitivity_matrix, fisher_information_matrix, fim_diagnostics, parameter_correlation_from_fim, top_correlated_pairs, observation_design_score, windowed_identifiability
from .world_panel import load_world_panel, world_panel_profile, make_acmf_proxy_panel, top_countries_by_coverage
__version__ = "3.3.1.4-clean-datacube"
__all__ = [
    'EPSILON','smax','smin','sigmoid','dsmax_dx','dsmax_dy','dsmin_dx','dsmin_dy',
    'ACMFParams','default_params','algebraic_layer','rhs','unpack_state','STATE_NAMES',
    'AdaptiveWeights','adaptive_dynamics_layer','project_state','rk4_step','simulate','scenario_run',
    'PriorSpec','default_prior_specs','LossConfig','ACMFObjective','CalibrationResult','huber_loss','compute_derivative','run_calibration_pipeline',
    'parameter_sensitivity_matrix','fisher_information_matrix','fim_diagnostics','parameter_correlation_from_fim','top_correlated_pairs','observation_design_score','windowed_identifiability',
    'load_world_panel','world_panel_profile','make_acmf_proxy_panel','top_countries_by_coverage', 'load_metadata','get_indicator_df','compute_oed_score','select_indicators','build_panel_dataset','parse_year_range','init_data_cube','build_data_cube','load_data_cube'
]

# Cohort transition helpers are available as acmf.aging_transition_matrix.

from .panel_builder import load_metadata, get_indicator_df, compute_oed_score, select_indicators, build_panel_dataset, parse_year_range

from .data_cube import init_data_cube, build_data_cube, load_data_cube

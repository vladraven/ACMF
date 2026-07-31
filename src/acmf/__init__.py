"""ACMF 4.0.0 stable baseline package."""
from .core import ACMFParams, default_params, rhs, algebraic_layer, STATE_NAMES
from .solver import simulate, rk4_step
from .calibration import calibrate_country_proxy, predict_from_theta, CALIBRATION_PARAMS, LossConfig
from .adaptive_dynamics import adaptive_dynamics_layer
from .empirical_validation import run_country_validation, run_core5_validation, parameter_stability_report, identifiability_map, indicator_ablation_study, backtest_2008, write_validation_outputs
from .world_panel import load_world_panel, make_acmf_proxy_panel, world_panel_profile, top_countries_by_coverage
from .enkf import enkf_assimilate
from .config import load_calibration_profile, load_parameter_config
from .exceptions import ACMFError, ManualDownloadRequired, SourceUnavailableError
from .aging_transition_matrix import transition_matrix, apply_transition
from .demography_age_structured import cohort_label, aggregate_age_counts
__version__ = "4.0.0-stable-baseline"

from .model_levels import MODEL_LEVELS, available_model_levels, get_model_level, observed_vars_for_level
from .world_panel import TrainFittedScaler

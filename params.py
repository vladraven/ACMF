"""Default parameter registry for ACMF complete system pack v2.1.

This file deliberately keeps the old scalar parameters for backward compatibility
while the new age-structured demographic layer is introduced separately.
"""
from __future__ import annotations
import numpy as np

def get_default_params(N: int = 10) -> dict:
    return {
        "N": int(N),
        # demographic legacy defaults
        "b0": 0.005,
        "b1": 0.015,
        "mu1": 0.002,
        "mu2": 0.005,
        "mu3": 0.035,
        "gamma1": 1.0 / 15.0,
        "gamma2": 1.0 / 48.0,
        "lambda_fert": 0.05,
        "beta_fert_stress": 0.10,
        "migration_rate_coeff": 0.02,
        "k_out": 0.05,
        "k_sat": 18.0,
        "sigma_dist": 1.0,
        "P_base": np.ones(N) * 1_000_000.0,
        # sociotechnical latent dynamics
        "rA": 0.04,
        "A_max": 0.95,
        "eta_prod_A": 0.08,
        "eta_prod_ch": 0.03,
        "delta_prod_stress": 0.03,
        "r_ch": 0.03,
        "r_mob": 0.02,
        "r_gov": 0.02,
        "r_v": 0.02,
        "r_inst": 0.02,
        "r_res": 0.02,
        "s1": 1.5,
        "s2": 1.2,
        "dep_stress_weight": 0.5,
        "demographic_mode": "legacy_p123",
        "age_structured_validation_mode": "observed_components",
        "scenario_mode": "endogenous_acmf_mechanisms",
    }

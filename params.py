from __future__ import annotations

def get_default_params(N:int=10)->dict:
    return {"N":N,"b0":0.005,"b1":0.015,"mu1":0.002,"mu2":0.005,"mu3":0.035,"gamma1":1/15,"gamma2":1/48,"migration_rate_coeff":0.02,"sigma_dist":1.0,"k_out":0.05,"rA":0.04,"A_max":0.95,"lambda_fert":0.05,"beta_fert_stress":0.1,"k_sat":18.0,"empirical_mode":"age_gender_component"}


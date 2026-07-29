# Changelog

## 3.3.1.2-audit-corrected-full

### Added

- `src/acmf/benchmark_models.py`: Persistence, LinearTrend, ARIMA(1,1,0), and VAR(1) benchmark forecasters.
- `src/acmf/diebold_mariano.py`: Diebold-Mariano predictive-accuracy test and ACMF-vs-benchmark comparison helper.
- `src/acmf/enkf.py`: Ensemble Kalman Filter for latent ACMF state tracking.
- `src/acmf/digital_twin.py`: Digital Twin engine wrapping EnKF assimilation and scenario forecasts.
- `scripts/run_benchmark_dm.py`: synthetic benchmark and Diebold-Mariano demo.
- `scripts/run_digital_twin.py`: EnKF/Digital Twin demo.

- `src/acmf/diagnostics.py`: numerical Jacobian, sign matrix, demographic decoupling check, P-invariance check, local spectrum analysis, and feedback-loop sign summary.
- `src/acmf/solver.py`: scenario-oriented RK4 solver with optional state projection for demos and visualization.
- `src/acmf/calibration.py`: Phase II calibration scaffold with Huber loss, derivative mismatch term, Differential Evolution, L-BFGS-B refinement, covariance/correlation diagnostics, and adaptive random-walk MCMC.
- `src/acmf/priors.py`: positive and bounded prior transforms.
- Smoothing operator derivatives: `dsmax_dx`, `dsmax_dy`, `dsmin_dx`, `dsmin_dy`.
- `scripts/run_acmf.py`: diagnostic demo runner.
- `scripts/run_calibration_synthetic.py`: small synthetic calibration demo.
- `tests/test_diagnostics_solver_calibration.py`: regression tests for diagnostics, bounded indices, parameter-dependent `J[V,R]`, solver, and calibration smoke checks.

### Fixed / refined

- Calibration priors are now operational: `PriorSpec` and `default_prior_specs` are integrated into `ACMFObjective` via `LossConfig.lambda_prior`, so DE, L-BFGS-B, and MCMC use the prior-augmented objective while retaining hard bounds as support constraints.

- `Env`, `EI`, `Innovation`, and `StructuralLimits` now expose bounded deployed values in `[0, 1]` and raw diagnostic values:
  - `Env_raw`
  - `EI_raw`
  - `Innovation_raw`
  - `StructuralLimits_raw`
- `J[V,R]` is documented and tested as parameter/state dependent, not a universal sign.
- `sigmoid` no longer evaluates both exponential branches, avoiding overflow warnings in diagnostics.
- `K0` remains the correct upper-bound capacity for the `P_max` argument.
- Demographic mode separation is tested as asymptotic/nonlinear near the smoothing layer, not as a strict global equality.

### Validation

- `PYTHONPATH=src pytest -q` -> `18 passed`.
- `examples/basic_usage.py` -> pass.
- `scripts/run_empirical_canada.py` -> pass.
- `scripts/run_synthetic_tests.py` -> pass.
- `scripts/run_acmf.py` -> pass.
- `scripts/run_calibration_synthetic.py` -> pass.
- `main.py --task health` -> pass.
- `main.py --task v2_4_9` -> pass with findings.
- `scripts/run_benchmark_dm.py` -> pass.
- `scripts/run_digital_twin.py` -> pass.

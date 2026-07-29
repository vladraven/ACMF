# ACMF Identifiability Program

This module introduces practical identifiability diagnostics for the ACMF calibration subset.

## Hypotheses

- **H-I1 Poor Observation Design**: the model may be identifiable under ideal observations, but the current observable set is insufficient.
- **H-I2 Redundant Parameterization**: some parameters may enter the observable dynamics through nearly equivalent composite directions.
- **H-I3 Latent State Overcapacity**: simultaneously estimating latent initial states can allow compensation between states and dynamic parameters.
- **H-I4 Regime-Dependent Identifiability**: the same parameter may be identifiable in crisis/transition regimes but weakly identifiable in stable regimes.

## Implemented diagnostics

`src/acmf/identifiability.py` provides:

- `parameter_sensitivity_matrix(...)`
- `fisher_information_matrix(...)`
- `fim_diagnostics(...)`
- `parameter_correlation_from_fim(...)`
- `top_correlated_pairs(...)`
- `observation_design_score(...)`
- `windowed_identifiability(...)`

## Synthetic runner

Run:

```bash
PYTHONPATH=src python scripts/run_identifiability_synthetic.py
```

The runner compares short stable, long stable, and synthetic-regime-shift trajectories. It reports FIM rank, condition number, weak eigen-directions, top correlated pairs, observation-design gain, and windowed diagnostics.

## Interpretation

This is a practical numerical identifiability layer. It does not prove symbolic structural identifiability. Instead, it establishes a measurable workflow for asking which parameters can be distinguished under a specific observation design and trajectory regime.

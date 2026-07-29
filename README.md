# ACMF 3.3.1.2

**Adaptive Civilizational Metabolism Framework**  
**Адаптивная модель цивилизационного метаболизма**

This repository contains the integrated **ACMF 3.3.1.2 system package**: the corrected mathematical core, the Adaptive Dynamics extension, the hypothesis ladder, empirical runners, tests, and documentation.

## Status

```text
Core analytical status:
  VALIDATED WITH CORRECTIONS APPLIED

Adaptive Dynamics status:
  DEFINED AS DIAGNOSTIC EXTENSION / TO BE EMPIRICALLY VALIDATED

Research programme status:
  EXECUTABLE HYPOTHESIS-LADDER SCAFFOLD
```

ACMF 3.3.1.2 does **not** import external futurist scenarios, fixed historical cycles, or scenario probabilities. It formalizes general testable mechanisms:

- fast/slow time-scale mismatch;
- inertial potential;
- transformational potential;
- adaptive capacity;
- criticality;
- phase transition probability;
- hypothesis ladder H0/H2/H1/H3;
- criticality hypotheses C0/C1/C2/C3.

## Repository layout

```text
src/acmf/
  smoothing.py              Smooth Smax/Smin operators
  core.py                   ACMF 10-state ODE core and algebraic layer
  adaptive_dynamics.py      Inertial/transformational/criticality module
  hypothesis_ladder.py      H0/H2/H1/H3 model comparison tools
  empirical.py              CSV loader and empirical runner helpers

tests/
  pytest suite

docs/
  mathematical specification
  philosophical foundation
  adaptive dynamics module
  hypothesis ladder
  empirical protocol

data/
  Canada FRED/World Bank empirical example CSV and manifest

scripts/
  run_synthetic_tests.py
  run_empirical_canada.py
```

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## Run tests

```bash
pytest -q
```

## Run synthetic hypothesis-ladder validation

```bash
python scripts/run_synthetic_tests.py
```

## Run bundled real empirical example

```bash
python scripts/run_empirical_canada.py
```

## Important limitation

The bundled empirical example is a minimal real-data smoke run. It is **not** a full empirical validation of ACMF. Full validation requires richer panel data with demographic cohorts, institutional proxies, productivity, automation, fertility, migration, stress, and latent-state candidates.


## Audit-corrected full package notes

This package includes the integrated post-audit runtime extension:

- diagnostics for Jacobian signs, local spectrum, demographic decoupling, and P-invariance;
- scenario RK4 solver for fast demos and visualization;
- Phase II calibration scaffold using Differential Evolution, L-BFGS-B, and adaptive MCMC;
- bounded deployed index values with raw diagnostics preserved;
- explicit treatment of `J[V,R]` as parameter/state dependent.

Run the full test suite:

```bash
PYTHONPATH=src pytest -q
```

Expected result for this package:

```text
18 passed
```

Run demos:

```bash
PYTHONPATH=src python scripts/run_acmf.py
PYTHONPATH=src python scripts/run_calibration_synthetic.py
PYTHONPATH=src python scripts/run_empirical_canada.py
PYTHONPATH=src python scripts/run_synthetic_tests.py
```

Important interpretation notes:

- `adaptive_dynamics.py` remains a diagnostic extension, not a fully calibrated probability model.
- `hypothesis_ladder.py` remains a statistical hypothesis-ladder scaffold and is not a substitute for ODE parameter calibration.
- `calibration.py` provides the Phase II scaffold for ODE calibration, but full empirical validation still requires richer panel data and stronger measurement models.


## Phase II/III benchmark and digital-twin extensions

This package also includes:

- benchmark econometric forecasters: Persistence/RandomWalk, LinearTrend, ARIMA(1,1,0), VAR(1);
- Diebold-Mariano forecast-comparison utilities;
- Ensemble Kalman Filter for latent-state estimation;
- Digital Twin wrapper for assimilation and scenario forecasts.

Run the additional demos:

```bash
PYTHONPATH=src python scripts/run_benchmark_dm.py
PYTHONPATH=src python scripts/run_digital_twin.py
```

The full test suite for this archive is expected to report:

```text
18 passed
```

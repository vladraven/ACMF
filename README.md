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


## Identifiability Program

The package now includes a numerical identifiability layer:

```bash
PYTHONPATH=src python scripts/run_identifiability_synthetic.py
```

It computes sensitivity matrices, Fisher Information Matrices, FIM rank, condition number, weak directions, parameter correlation from the pseudo-inverse FIM, observation-design gain, and windowed identifiability.

See `docs/IDENTIFIABILITY_PROGRAM.md`.

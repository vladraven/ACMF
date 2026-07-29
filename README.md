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


## Audit correction patch — 3.3.1.2-audit-corrected

This deployment package includes the post-audit corrections applied to the executable `src/acmf` package:

- Demographic mode separation is treated as nonlinear near the smoothing layer; `L_s / P` is **not** documented or tested as identically `0.6`.
- The `V` equation now preserves both R channels: the indirect positive `R -> Education -> C -> Gap -> V` channel and the direct stabilizing `-beta12 * R * V` channel. Therefore `J[V,R]` is documented and tested as parameter/state dependent, not universal.
- Feedback loop `L2` is tested as a negative feedback loop.
- `K0` is retained for the `P_max` upper-bound argument; `K_min` is not used as the worst-case upper estimate.
- `EI`, `Innovation`, and `StructuralLimits` now expose raw diagnostics (`*_raw`) while the deployed index values are bounded to `[0, 1]`.
- Positive/bounded prior transforms are available in `src/acmf/priors.py`.
- Audit regression tests are in `tests/test_audit_3_3_1_2_fixes.py`.

Validation command used for this package:

```bash
PYTHONPATH=src pytest -q
```

Expected result:

```text
15 passed
```

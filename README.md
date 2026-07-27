# ACMF
## Adaptive Civilizational Metabolism Framework

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)]
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)]
[![Status](https://img.shields.io/badge/Status-Research-orange.svg)]

Adaptive Civilizational Metabolism Framework (ACMF) is an open-source mathematical framework for modeling long-term socio-economic and demographic dynamics as a system of coupled nonlinear differential equations.

Unlike conventional macroeconomic models, ACMF represents society as an adaptive metabolic system where demographic, institutional, technological, economic and social processes evolve simultaneously through nonlinear feedbacks.

---

# Project Status

**Current status:** Active Research

Current repository contains:

- formal mathematical specification;
- reference numerical implementation;
- empirical validation framework;
- statistical data ingestion pipeline;
- calibration and validation tools;
- baseline comparison framework;
- age-structured demographic architecture (v2).

The mathematical core is internally validated.

Empirical validation is currently in progress.

---

# Main Idea

ACMF models civilization as a dynamic system composed of interacting regional subsystems.

Each region contains interacting variables representing

- population,
- productivity,
- automation,
- institutions,
- human capital,
- moral capital,
- agency,
- environmental resilience,
- fertility,
- migration,
- systemic stress.

The model studies how these feedback loops influence long-term societal trajectories.

---

# Mathematical Foundation

The original ACMF formulation describes every region by a nonlinear state vector

X = (A, Prod, Ch, M, G, V, Inst, R, F, P1, P2, P3)

where the complete system consists of coupled ordinary differential equations over multiple interacting regions.

The mathematical specification includes

- invariant state domain,
- conservation properties,
- migration constraints,
- smooth nonlinear operators,
- dissipativity,
- existence of a global attractor,
- production-ready numerical implementation guidelines.

---

# Age-Structured Architecture (v2)

Beginning with version 2.0 the demographic subsystem is being refactored.

Instead of using

P1
P2
P3

as the internal demographic state,

ACMF now represents population as

Population[province, gender, age_group]

The traditional demographic aggregates become reporting variables only.

Historical validation uses observed demographic components.

Scenario simulations use endogenous ACMF dynamics.

This separation removes a structural limitation identified during empirical validation.

---

# Repository Structure

```
acmf/
    core/
    solver/
    demography/
    calibration/

empirical/
    raw/
    processed/
    reports/
    statcan_ingest/
    scripts/

tests/

docs/

examples/
```

---

# Validation Philosophy

The project distinguishes between

## Mathematical validation

Verifies

- numerical stability;
- invariance;
- conservation laws;
- solver correctness;
- Jacobian correctness.

## Empirical validation

Verifies

- calibration quality;
- out-of-sample prediction;
- rolling-window cross validation;
- province-level metrics;
- comparison against statistical baselines.

Mathematical correctness does not automatically imply empirical predictive performance.

---

# Current Empirical Results

The empirical framework currently performs

- rolling cross-validation;
- baseline comparison;
- uncertainty estimation;
- multi-start calibration;
- province-level evaluation.

Current experiments indicate that the original three-cohort demographic subsystem does **not yet outperform** simple demographic baseline models.

This result motivated the transition toward the new age-structured demographic architecture.

Negative empirical results are preserved as part of the project's scientific development history.

---

# Data

The project uses publicly available datasets from Statistics Canada.

Examples include

- population estimates
- births
- deaths
- migration
- GDP
- demographic components

The repository contains parsers and normalization tools for supported datasets.

Raw datasets are not redistributed unless permitted by their licenses.

---

# Scientific Goals

The long-term objective of ACMF is to provide a reproducible framework for studying

- demographic transition;
- institutional dynamics;
- technological change;
- migration;
- labor shortages;
- automation;
- long-term resilience;
- scenario analysis.

The framework is intended as a research platform rather than a forecasting service.

---

# Development Principles

Every architectural change should satisfy

✓ mathematical consistency

✓ numerical stability

✓ reproducibility

✓ automated testing

✓ empirical validation

✓ comparison with baseline models

---

# Running

Clone repository

```bash
git clone https://github.com/<user>/acmf.git
cd acmf
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run tests

```bash
pytest
```

Run empirical diagnostics

```bash
python empirical/scripts/build_full_package.py
```

---

# Documentation

The repository contains

- Mathematical Specification
- Numerical Implementation
- Architecture Documentation
- Validation Reports
- Empirical Diagnostics
- Development History

---

# Citation

If you use ACMF in research, please cite both

- the software repository
- the accompanying scientific publication

A `CITATION.cff` file is included.

---

# License

Apache License 2.0

---

# Disclaimer

ACMF is an experimental scientific research framework.

The mathematical model is formally specified and numerically validated.

Empirical validation is an ongoing research process.

The project does not claim predictive superiority over statistical baseline models until such performance is demonstrated through reproducible empirical evaluation.

---

© 2026 ACMF Project

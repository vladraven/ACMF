# ACMF 3.3.1.9-clean-quality-hardening Report

## Status

`3.3.1.9-clean-quality-hardening` is a hardening release. The prior weak empirical-validation line is treated as withdrawn and replaced by explicit quality gates, configuration, typed source errors, safer runners and anti-stub tests.

## Main fixes

- Added YAML-driven parameter and calibration configuration:
  - `configs/params/baseline.yaml`
  - `configs/calibration/smoke.yaml`
  - `configs/calibration/research.yaml`
- Added config validation:
  - `src/acmf/config.py`
- Added typed source/calibration errors:
  - `src/acmf/exceptions.py`
- Added non-silent manual-source contracts:
  - missing WVS, ESS, V-Dem, INFORM, UNESCO and WIPO files now raise `ManualDownloadRequired` instead of returning empty tables.
- Added stricter World Bank fetcher behavior:
  - API errors raise `SourceUnavailableError` in strict mode.
- Added real age-structure behavior:
  - `src/acmf/aging_transition_matrix.py`
  - `src/acmf/demography_age_structured.py`
- Hardened numerical smoothing to remove overflow warnings from sigmoid and smooth min/max operations.
- Replaced ad-hoc task execution with a single `TaskSpec` runner:
  - `src/acmf/task_runner.py`
- Hardened `app.py`:
  - task whitelist;
  - optional bearer token through `ACMF_API_TOKEN`;
  - stdout/stderr truncation;
  - bounded task timeout.
- Added quality hardening tests:
  - `tests/test_quality_hardening.py`

## Anti-stub checks performed twice

Both quality scans passed and found no source occurrences of:

```text
return pd.DataFrame()
return pandas.DataFrame()
return locals()
except Exception: pass
placeholder
TODO
pass at end of source line
```

Forbidden root files were absent:

```text
root acmf/
root acmf_core.py
root acmf_solver.py
index.php
ACMF_PROJECT_BUNDLE.txt
```

## Test results, double pass

First pass:

```text
15 passed
pytest_pass1_status:0
```

Second pass:

```text
15 passed
pytest_pass2_status:0
```

## Smoke task results

```text
health_status:0
validate_canada_status:0
validate_core5_status:0
ablation_status:0
backtest_2008_status:0
```

## Known scope boundary

This release is not Spatial Dynamics and does not claim that all external protected/manual data sources have public APIs. Instead, it makes missing manual sources explicit and non-silent, which is the correct behavior for a research platform.

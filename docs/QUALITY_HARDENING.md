# ACMF Quality Hardening

Version: `3.3.1.9-clean-quality-hardening`.

## Quality gates

The release includes automated checks for:

- no empty `pd.DataFrame()` placeholder returns in source modules;
- no `return locals()` in model code;
- no `except Exception: pass` broad silencing;
- manual fetchers raising explicit `ManualDownloadRequired`;
- calibration research profile requiring non-smoke iteration budgets;
- validated YAML parameter bounds;
- age transition matrix behavior;
- unsupported age groups raising `ValueError`.

## Fetcher contract

A fetcher must either:

1. return a real non-silent result;
2. raise a typed error explaining the missing source or API problem.

It must not silently return an empty table on missing required data.

## Calibration contract

Smoke profiles are isolated from research profiles. Scientific results should use `configs/calibration/research.yaml` or stricter explicit profiles.

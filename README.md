# ACMF 3.3.1.9-clean-quality-hardening

This release withdraws the weak `3.3.1.8` line and ships a quality-hardening package focused on explicit contracts, configuration, anti-stub tests and safer task execution.

## What is hardened

- Calibration parameters are loaded from YAML configuration with bounds validation.
- Calibration profiles separate smoke and research settings.
- Manual-only data sources now raise explicit `ManualDownloadRequired` errors instead of silently returning empty `DataFrame`s.
- World Bank fetcher supports strict mode and raises `SourceUnavailableError` on API failures by default.
- Age-structure modules contain real transition and aggregation behavior.
- `cohort_label()` raises an error for unsupported ages instead of returning `None`.
- API task execution truncates stdout/stderr and supports bearer-token protection through `ACMF_API_TOKEN`.
- Anti-stub tests scan for empty `DataFrame` placeholders, `return locals()`, and broad exception silencing.

## Tasks

```bash
python main.py --task health
python main.py --task empirical_validate_canada
python main.py --task empirical_validate_core5
python main.py --task empirical_indicator_ablation
python main.py --task empirical_backtest_2008
```

## Research run

```bash
python scripts/run_empirical_validation.py \
  --mode core5 \
  --countries Canada Germany Japan Australia "Korea, Rep." \
  --train-start 1995 \
  --train-end 2015 \
  --validation-start 2016 \
  --validation-end 2024 \
  --seeds 0 1 2 \
  --max-nfev 300
```

## Configuration

```text
configs/params/baseline.yaml
configs/calibration/smoke.yaml
configs/calibration/research.yaml
```

Smoke settings are for CI only and are not valid for scientific claims.

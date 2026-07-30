# ACMF 3.3.1.10-clean-empirical-validation Report

## Status

`3.3.1.10-clean-empirical-validation` is the empirical-validation release built on top of the `3.3.1.9-clean-quality-hardening` gate. It keeps the hardening contracts in place and restores the empirical-validation direction with explicit configuration, smoke/research separation, validation outputs and anti-stub checks.

## Main contents

- ACMF mathematical core and RK4 solver.
- Empirical validation layer:
  - country calibration;
  - Core5 validation;
  - train/validation split;
  - RMSE, MAE, MAPE and R²;
  - dynamic year-by-year errors;
  - parameter stability map;
  - identifiability map;
  - indicator ablation;
  - 2008 backtest.
- Quality-hardening contracts retained:
  - manual data sources raise `ManualDownloadRequired`;
  - strict World Bank fetcher raises `SourceUnavailableError`;
  - YAML parameter and calibration profiles;
  - no empty DataFrame source behavior;
  - no `return locals()`;
  - safer task runner and bounded API task capture.
- Added empirical validation configuration:
  - `configs/validation_core5.yaml`

## Task entrypoints

```bash
python main.py --task health
python main.py --task empirical_validate_canada
python main.py --task empirical_validate_core5
python main.py --task empirical_indicator_ablation
python main.py --task empirical_backtest_2008
```

## Full research run

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

## Double test pass

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

## Double quality scan

Both scans confirmed:

```text
version: 3.3.1.10-clean-empirical-validation
source file count: 23
compile_status:0
```

No source matches were found for:

```text
return pd.DataFrame()
return pandas.DataFrame()
return locals()
except Exception: pass
placeholder
TODO
FIXME
stub
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

## Smoke task results

```text
health_status:0
validate_canada_status:0
validate_core5_status:0
ablation_status:0
backtest_2008_status:0
```

## Scope note

This release is intended as the first empirical-validation package after quality hardening. It does not claim final scientific validation by itself. It provides the reproducible machinery and guardrails needed to run and audit the empirical validation program.

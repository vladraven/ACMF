# ACMF Full v2.1 Complete System Build Report

Status: **PASS_WITH_AVAILABLE_DATA**

## Included core files
- `acmf_core.py`
- `params.py`
- `acmf_solver.py`
- `acmf/core.py`
- `acmf/solver.py`
- `acmf/demography_age_structured.py`

## Available raw files
- `1710015101-eng (1).csv`

## Missing expected raw files for full rerun
- `17100005.csv`
- `1710000501-eng.csv`
- `1710000601-eng.csv`
- `1710000801-eng.csv`
- `1710001401-eng.csv`
- `1710001501-eng (1).csv`
- `1710001501-eng (2).csv`
- `1710002001-eng.csv`
- `1710004001-eng.csv`
- `36100222.csv`

## Test results
- `parse_1710015101`: `PASS`
- `province_er_reconciliation`: `PASS`

## Parsed outputs
- `economic_region_components_2024_2025_long.csv`: `{'rows': 1800, 'province_count': 13, 'economic_region_count': 76, 'component_count': 10}`
- `province_vs_economic_region_reconciliation.csv`: `{'rows': 130, 'max_abs_difference': 0.0}`

## Explanation
The old P1/P2/P3 internal demographic block is retained only for scenario/backward compatibility. Empirical validation must use the new age/gender component layer.

The package is complete as code/system distribution; data-driven tests are limited by the raw files physically available in this runtime.

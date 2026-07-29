# ACMF 3.3.1.3-clean-datafetch Report

## Version

`3.3.1.3-clean-datafetch`

This is the next package version after `3.3.1.2-clean`.

## Completed integration

- Added `src/acmf/data_fetchers/` with clean source modules:
  - `world_bank.py`
  - `wgi.py`
  - `innovation.py`
  - `world_values.py`
  - `resilience.py`
- Added two World Bank download backends:
  - `requests` backend, direct World Bank REST API.
  - `wbdata` backend, optional package backend.
- Added metadata-driven panel builder:
  - `src/acmf/panel_builder.py`
  - `scripts/build_panel_dataset.py`
- Added fixed YAML metadata in expected locations:
  - `data/metadata/indicators.yaml`
  - `src/acmf/data/indicators.yaml`
- Added integrated data:
  - `data/world_data_level1_1995_2025.csv`
  - `src/acmf/data/world_data_level1_1995_2025.csv`
- Added documentation:
  - `docs/DATAFETCH_PANEL_BUILDER.md`
- Added tests:
  - `tests/test_panel_builder.py`
  - `tests/test_data_fetchers.py`

## Complete-date rule

The default complete data year is now:

```text
complete_data_year = current_calendar_year - 2
```

Therefore, for 2026 the complete-data cutoff is 2024.

## New task entrypoints

```bash
python main.py --task data_list_indicators
python main.py --task data_fisher_rank
python main.py --task data_build_minimal
python main.py --task data_build_standard
```

Existing clean entrypoints remain available.

## Validation

Pytest:

```text
20 passed
```

Runtime smoke tests succeeded:

```text
health_status:0
data_list_status:0
data_fisher_status:0
data_build_minimal_status:0
data_build_standard_status:0
v249_status:0
world_ident_status:0
downloader_help_status:0
```

## Clean-package discipline

Confirmed absent:

- root `acmf/` stub package;
- root `acmf_core.py` / `acmf_solver.py`;
- `index.php`;
- `ACMF_PROJECT_BUNDLE.txt`.

Manifest was regenerated from the live package tree.

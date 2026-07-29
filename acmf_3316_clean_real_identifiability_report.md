# ACMF 3.3.1.6-clean-real-identifiability Report

## Version

`3.3.1.6-clean-real-identifiability`

This is the next package version after `3.3.1.5-clean-observation-designer`.

## Completed integration

- Added Real Identifiability Lab module:
  - `src/acmf/real_identifiability.py`
- Added runner:
  - `scripts/run_real_identifiability_world_panel.py`
- Added documentation:
  - `docs/REAL_IDENTIFIABILITY.md`
- Added tests:
  - `tests/test_real_identifiability.py`
- Exported public functions:
  - `analyze_country_identifiability`
  - `build_real_identifiability_report`
  - `summarize_real_identifiability`
  - `save_real_identifiability_report`

## Capability

The Real Identifiability Lab runs practical identifiability diagnostics on real country panel proxies and reports:

```text
rank
condition_number
min_eigenvalue
max_eigenvalue
weak_directions
top_correlated_pairs
observation_design_gain
greedy_design
minimal_design
```

## New task entrypoints

```bash
python main.py --task real_ident_canada
python main.py --task real_ident_core5
```

`real_ident_canada` is a bounded deployment smoke test.

`real_ident_core5` runs the core country set on a bounded recent window for a reproducible runtime smoke test:

```text
Canada
Germany
Japan
Korea, Rep.
Australia
```

For the full research run, call the script directly with the desired full window and design depth:

```bash
python scripts/run_real_identifiability_world_panel.py \
  --countries Canada Germany Japan "Korea, Rep." Australia \
  --start-year 1995 \
  --design-k 3
```

## Validation

Pytest:

```text
30 passed
```

Runtime smoke tests:

```text
health_status:0
real_ident_canada_status:0
real_ident_core5_status:0
```

## Clean-package discipline

Confirmed absent from package source tree:

- root `acmf/` stub package;
- root `acmf_core.py` / `acmf_solver.py`;
- `index.php`;
- `ACMF_PROJECT_BUNDLE.txt`.

Manifest was regenerated from the live package tree.

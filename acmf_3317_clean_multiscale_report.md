# ACMF 3.3.1.7-clean-multiscale Report

## Version

`3.3.1.7-clean-multiscale`

This is the next package version after `3.3.1.6-clean-real-identifiability`.

## Completed integration

- Added Multi-Scale Framework module:
  - `src/acmf/multiscale.py`
- Added builder script:
  - `scripts/build_multiscale_frame.py`
- Added documentation:
  - `docs/MULTISCALE.md`
- Added tests:
  - `tests/test_multiscale.py`
- Exported public API:
  - `ScaleNode`
  - `ScaleEdge`
  - `MultiScaleFrame`
  - `build_country_multiscale_frame`
  - `aggregate_children`
  - `disaggregate_parent_to_children`
  - `compare_scales`
  - `save_multiscale_frame`
  - `load_multiscale_frame`

## Capability

The Multi-Scale Framework represents ACMF as one model across aggregation levels:

```text
World
↓
Country
↓
Province
↓
City
↓
District
```

This release implements the first practical hierarchy layer:

```text
scale nodes
containment edges
cross-scale observations
schema validation
child-to-parent aggregation
parent-to-child disaggregation
cross-scale comparison
JSON persistence
```

## Aggregation defaults

```text
P      -> sum
Prod   -> population-weighted mean
A      -> population-weighted mean
Inst   -> population-weighted mean
F      -> population-weighted mean
Ch/M/G/V/R -> population-weighted mean
```

## New task entrypoint

```bash
python main.py --task multiscale_build
```

Direct script call:

```bash
python scripts/build_multiscale_frame.py \
  --countries Canada Germany Japan "Korea, Rep." Australia \
  --start-year 1995 \
  --end-year auto
```

## Validation

Pytest:

```text
34 passed
```

Runtime smoke tests:

```text
health_status:0
multiscale_build_status:0
```

## Clean-package discipline

Confirmed absent from package source tree:

- root `acmf/` stub package;
- root `acmf_core.py` / `acmf_solver.py`;
- `index.php`;
- `ACMF_PROJECT_BUNDLE.txt`.

Manifest was regenerated from the live package tree.

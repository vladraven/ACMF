# ACMF Multi-Scale Framework

Version line: `3.3.1.7-clean-multiscale`.

## Purpose

The Multi-Scale Framework represents ACMF as one model that can be evaluated at different aggregation levels:

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

This release implements the first clean infrastructure layer for hierarchical scale nodes, containment edges, cross-scale observations, aggregation, disaggregation and validation.

## Core module

```text
src/acmf/multiscale.py
```

Main classes and functions:

```python
ScaleNode
ScaleEdge
MultiScaleFrame
build_country_multiscale_frame(...)
aggregate_children(...)
disaggregate_parent_to_children(...)
compare_scales(...)
save_multiscale_frame(...)
load_multiscale_frame(...)
```

## Aggregation rules

Default rules:

```text
P      -> sum
Prod   -> population-weighted mean
A      -> population-weighted mean
Inst   -> population-weighted mean
F      -> population-weighted mean
Ch/M/G/V/R -> population-weighted mean
```

## CLI task

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

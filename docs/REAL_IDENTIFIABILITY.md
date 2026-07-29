# ACMF Real Identifiability Lab

Version line: `3.3.1.6-clean-real-identifiability`.

## Purpose

The Real Identifiability Lab runs practical identifiability diagnostics on real country panel proxies rather than only synthetic trajectories.

Default core countries:

```text
Canada
Germany
Japan
Korea, Rep.
Australia
```

## Core module

```text
src/acmf/real_identifiability.py
```

Main functions:

```python
analyze_country_identifiability(...)
build_real_identifiability_report(...)
summarize_real_identifiability(...)
save_real_identifiability_report(...)
```

## Report contents

Each country report includes:

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

## CLI tasks

Deployment smoke test:

```bash
python main.py --task real_ident_canada
```

Core-5 research task:

```bash
python main.py --task real_ident_core5
```

Direct script call:

```bash
python scripts/run_real_identifiability_world_panel.py \
  --countries Canada Germany Japan "Korea, Rep." Australia \
  --design-k 3 \
  --output output/real_identifiability_world_panel.json
```

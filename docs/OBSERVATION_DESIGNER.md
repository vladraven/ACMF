# ACMF Observation Designer

Version line: `3.3.1.7-clean-multiscale`.

## Purpose

The Observation Designer promotes ACMF from diagnostics to experiment design. It answers:

1. If one new observable can be added, which one improves practical identifiability the most?
2. If `k` observables can be added, which set should be selected greedily?
3. What small observation set reaches a target rank / condition threshold when possible?

## Core module

```text
src/acmf/observation_designer.py
```

Main functions:

```python
score_candidate_observables(...)
greedy_observation_design(...)
minimal_observation_set(...)
design_for_world_panel_country(...)
```

## Scoring

Each candidate is evaluated using the existing ACMF sensitivity/FIM layer:

```text
rank_gain
min_eigenvalue_gain
logdet_gain
condition_gain
```

The output remains model-based and distinct from metadata-level `oed_score` used in the panel builder.

## CLI tasks

```bash
python main.py --task obs_design_synthetic
python main.py --task obs_design_world
```

The default `obs_design_world` task runs a bounded smoke design for Canada with `k=2`. For broader research runs call the script directly:

```bash
python scripts/run_observation_designer_world_panel.py --countries Canada Germany Japan "Korea, Rep." Australia --k 5
```

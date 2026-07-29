# ACMF 3.3.1.5-clean-observation-designer Report

## Version

`3.3.1.5-clean-observation-designer`

This is the next package version after `3.3.1.4-clean-datacube`.

## Completed integration

- Added Observation Designer module:
  - `src/acmf/observation_designer.py`
- Added scripts:
  - `scripts/run_observation_designer_synthetic.py`
  - `scripts/run_observation_designer_world_panel.py`
- Added documentation:
  - `docs/OBSERVATION_DESIGNER.md`
- Added tests:
  - `tests/test_observation_designer.py`
- Exported public functions from `acmf.__init__`:
  - `score_candidate_observables`
  - `greedy_observation_design`
  - `minimal_observation_set`
  - `design_for_world_panel_country`

## Observation Designer capability

The layer answers:

1. If one new observable can be added, which one improves practical identifiability most?
2. If `k` observables can be added, which greedy set should be selected?
3. What small observable set reaches a target rank / threshold when possible?

## Scoring metrics

Candidate observables are ranked by model-based identifiability gains:

```text
rank_gain
min_eigenvalue_gain
logdet_gain
condition_gain
```

This is separate from metadata-level `oed_score` in the panel builder.

## New task entrypoints

```bash
python main.py --task obs_design_synthetic
python main.py --task obs_design_world
```

The default `obs_design_world` entrypoint is bounded for deployment smoke tests:

```text
Canada, k=2
```

Research runs can call the script directly with more countries and `k=5`.

## Validation

Pytest:

```text
27 passed
```

Runtime smoke tests:

```text
health_status:0
obs_synthetic_status:0
obs_world_status:0
```

## Clean-package discipline

Confirmed absent from package source tree:

- root `acmf/` stub package;
- root `acmf_core.py` / `acmf_solver.py`;
- `index.php`;
- `ACMF_PROJECT_BUNDLE.txt`.

Manifest was regenerated from the live package tree.

# ACMF v2.1 Direction of Changes

## What changes

1. `P1/P2/P3` are deprecated as internal demographic state.
2. Internal empirical demographic state becomes `Pop[province, gender, age_group]`.
3. Historical validation uses observed StatCan components.
4. Endogenous ACMF demographic mechanisms remain for scenario simulation and backward compatibility.
5. Strong baselines remain mandatory: `last_slope`, `linear_trend`, `official_components_total`, `age_structured_component_model`.

## Where changes live

- `acmf_core.py`: legacy/scenario RHS and compatibility entrypoint.
- `acmf/demography_age_structured.py`: new age/gender demographic layer.
- `empirical/statcan_ingest/`: raw StatCan wide-to-long parser layer.
- `empirical/scripts/build_full_package.py`: data build and report entrypoint.
- `tests/`: system, core, and parser tests.

## Scientific rule

No historical demographic model is considered validated unless it beats cohort-persistence/last-slope baselines on rolling windows.


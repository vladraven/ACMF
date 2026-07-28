# ACMF Full v2.4.2 Trace Audit Package

This package audits the demographic pipeline rather than claiming a model improvement.

## Run

```bash
python empirical/scripts/run_trace_audit_v2_4_2.py
python tests/test_v2_4_2_trace_audit.py
```

## What is audited

- Whether empirical transition predictions differ from fixed20 predictions.
- Whether aging coefficients actually changed.
- Stage-by-stage traces: after aging, births, deaths, international migration, and interprovincial migration.
- Component contribution deltas.
- P_tot forecast/accounting sensitivity.

## Current finding

The trace audit determines whether v2.4 really changed the predictions, and records the answer in `empirical/reports/v2_4_2_trace_audit_report.md`.

## v2.4.3 real aging operator re-estimation

```bash
python empirical/scripts/run_real_aging_operator_reestimation_v2_4_3.py
python tests/test_v2_4_3_real_aging_reestimation.py
```

v2.4.3 adds mandatory matrix-level and output-level tests:

- `T_real != T_fixed20`
- `predictions_real != predictions_fixed20`
- `after_aging` stage differs before later components are applied

# Changelog

## 3.3.1.2-audit-corrected

### Fixed

- Removed reliance on strict demographic equality `L_s / P = 0.6`; tests now assert the nonlinear smoothing-layer behavior.
- Refined the executable `V` equation audit: `d(dV/dt)/dInst > 0` and `d(dV/dt)/dG = 0` at the reference state, while `d(dV/dt)/dR` is parameter/state dependent because R has both a positive indirect channel and a direct stabilizing loss channel.
- Reconfirmed `L2` as a negative feedback loop.
- Retained `K0` as the safe upper-bound capacity in the `P_max` argument.
- Added bounded deployed versions of `EI`, `Innovation`, and `StructuralLimits`; raw values remain available as `EI_raw`, `Innovation_raw`, and `StructuralLimits_raw`.
- Added `LogNormalPrior`, `UnitIntervalPrior`, and `BoundedPrior` for positive and bounded parameters.
- Added audit regression tests.

### Validation

- `PYTHONPATH=src pytest -q` -> `15 passed`.
- `examples/basic_usage.py` -> pass.
- `scripts/run_empirical_canada.py` -> pass.
- `scripts/run_synthetic_tests.py` -> pass.
- `main.py --task health` -> pass.
- `main.py --task v2_4_9` -> pass with findings.

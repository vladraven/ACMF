# v2.4.3 Real Aging Operator Re-estimation Audit

Status: **PASS_WITH_FINDINGS**

## Matrix-level test
- `max_abs_diff(T_real, T_fixed20)`: 0.11309114830787224
- `frobenius_norm(T_real - T_fixed20)`: 0.21348176066183128
- `nonzero_entries`: 40

## Output-level test
- `P1_0_14`: max_abs_diff=3609.8896793322638, mean_abs_diff=852.1242633775894, allclose=False
- `P2_15_64`: max_abs_diff=5448.2707809992135, mean_abs_diff=1241.9425234348105, allclose=False
- `P3_65plus`: max_abs_diff=9058.160460332409, mean_abs_diff=2094.066786812664, allclose=False
- `P_tot`: max_abs_diff=1.862645149230957e-09, mean_abs_diff=1.9799424053141564e-10, allclose=True

## Stage after-aging test
- `P1_0_14`: max_abs_diff=3609.8896793322638, allclose=False
- `P2_15_64`: max_abs_diff=5448.2707809992135, allclose=False
- `P3_65plus`: max_abs_diff=9058.160460332874, allclose=False
- `P_tot`: max_abs_diff=1.862645149230957e-09, allclose=True

## Best by target
- `P1_0_14`: `fixed20_all_components` RMSE=2070.40, relative_RMSE=0.003666
- `P2_15_64`: `real_single_age_aging_births_deaths_international_interprovincial` RMSE=3964.23, relative_RMSE=0.001623
- `P3_65plus`: `real_single_age_aging_births_deaths_international_interprovincial` RMSE=1776.59, relative_RMSE=0.002496
- `P_tot`: `real_single_age_aging_births_deaths_international_interprovincial` RMSE=136.76, relative_RMSE=0.000037

## Interpretation
v2.4.3 estimates aging outflow fractions from the 2021 single-age census distribution and explicitly tests T_real != T_fixed and predictions_real != predictions_fixed.

The single-age census is a cross-sectional anchor, not a longitudinal transition series; this is a stronger pipeline test and practical re-estimation, not a final demographic law.

## Known limitations
- Observed demographic components are still used in accounting-mode predictions.
- Single-age distribution is a 2021 cross-sectional census anchor.
- No uncertainty propagation yet.
- Interprovincial net migration by age/gender is approximated.
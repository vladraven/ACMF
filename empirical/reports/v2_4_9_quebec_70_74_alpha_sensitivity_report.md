# v2.4.9 Quebec 70-74 Alpha Sensitivity

Status: **PASS_WITH_FINDINGS**

## Purpose
Local alpha sensitivity for Quebec 70-74 to determine whether the failure is tied to the 65-69 inflow / 70-74 stay rates.

## Model summary
- `best_grid_rmse`: alpha_source=0.255, alpha_target=0.270, RMSE=1957.91, MAE=1782.16, MaxAE=2579.69
- `best_grid_mae`: alpha_source=0.250, alpha_target=0.265, RMSE=2031.16, MAE=1613.93, MaxAE=3137.21
- `fixed20`: alpha_source=0.200, alpha_target=0.200, RMSE=2293.73, MAE=2138.69, MaxAE=3310.91
- `real_single_age`: alpha_source=0.182, alpha_target=0.191, RMSE=5386.37, MAE=4933.61, MaxAE=7760.62
- `fixed_source_low_target`: alpha_source=0.200, alpha_target=0.180, RMSE=10548.14, MAE=10387.23, MaxAE=12395.27
- `high_source_fixed_target`: alpha_source=0.230, alpha_target=0.200, RMSE=18346.79, MAE=18273.44, MaxAE=19991.54

## Findings
- This is a local sensitivity/counterfactual audit, not a production operator-selection model.
- Best grid RMSE is 1957.91 at alpha_source=0.255, alpha_target=0.270.
- Observed real_single_age alphas are source=0.181877, target=0.190637; fixed20 uses source=0.200000, target=0.200000.
- A local alpha pair can outperform both real_single_age and fixed20 for Quebec 70-74 in this window; this is evidence for local regime sensitivity, not a general rule.
- fixed20 outperforms real_single_age for Quebec 70-74, confirming the v2.4.8 localized failure mode.

## Limitations
- Grid is evaluated on the same Quebec 2023-2025 window; do not use best_grid as a production operator without out-of-sample validation.
- This is an explanatory counterfactual around one age bin and province.
- Observed components remain accounting-mode inputs.
# v2.4.2 Trace / Pipeline Audit

Status: **PASS_WITH_FINDINGS**

## Findings
- Aging operator coefficients did not change from fixed 20%; empirical calibration selected the same coefficients.
- Stage trace shows no difference at any stage between fixed and empirical transition outputs.
- Root cause: v2.4 transition matrix variant was effectively equivalent to fixed20; identical RMSE was a real pipeline finding, not independent evidence of improvement.

## Operator changed?
- `alpha_operator_changed`: `False`
- `stage_predictions_changed`: `False`

## Stage diff summary
- stage `after_aging` target `P1_0_14`: max_abs_diff=0.0, allclose=True
- stage `after_aging` target `P2_15_64`: max_abs_diff=0.0, allclose=True
- stage `after_aging` target `P3_65plus`: max_abs_diff=0.0, allclose=True
- stage `after_aging` target `P_tot`: max_abs_diff=0.0, allclose=True
- stage `after_births` target `P1_0_14`: max_abs_diff=0.0, allclose=True
- stage `after_births` target `P2_15_64`: max_abs_diff=0.0, allclose=True
- stage `after_births` target `P3_65plus`: max_abs_diff=0.0, allclose=True
- stage `after_births` target `P_tot`: max_abs_diff=0.0, allclose=True
- stage `after_deaths` target `P1_0_14`: max_abs_diff=0.0, allclose=True
- stage `after_deaths` target `P2_15_64`: max_abs_diff=0.0, allclose=True
- stage `after_deaths` target `P3_65plus`: max_abs_diff=0.0, allclose=True
- stage `after_deaths` target `P_tot`: max_abs_diff=0.0, allclose=True
- stage `after_international` target `P1_0_14`: max_abs_diff=0.0, allclose=True
- stage `after_international` target `P2_15_64`: max_abs_diff=0.0, allclose=True
- stage `after_international` target `P3_65plus`: max_abs_diff=0.0, allclose=True
- stage `after_international` target `P_tot`: max_abs_diff=0.0, allclose=True
- stage `after_interprovincial` target `P1_0_14`: max_abs_diff=0.0, allclose=True
- stage `after_interprovincial` target `P2_15_64`: max_abs_diff=0.0, allclose=True
- stage `after_interprovincial` target `P3_65plus`: max_abs_diff=0.0, allclose=True
- stage `after_interprovincial` target `P_tot`: max_abs_diff=0.0, allclose=True

## Best by target
- `P1_0_14`: `fixed20_aging_births_deaths_international_interprovincial` RMSE=2070.40, rel=0.003666
- `P2_15_64`: `fixed20_aging_births_deaths_international_interprovincial` RMSE=5704.65, rel=0.002336
- `P3_65plus`: `last_slope` RMSE=1920.09, rel=0.002698
- `P_tot`: `fixed20_aging_births_deaths_international_interprovincial` RMSE=136.76, rel=0.000037

## P_tot modes
- `fixed20_aging_births_deaths_international_interprovincial`: RMSE=136.76, rel=0.00003678
- `empirical_transition_aging_births_deaths_international_interprovincial`: RMSE=136.76, rel=0.00003678
- `empirical_transition_aging_births_deaths_international`: RMSE=15946.26, rel=0.00428862
- `fixed20_aging_births_deaths_international`: RMSE=15946.26, rel=0.00428862
- `last_slope`: RMSE=85872.03, rel=0.02309458
- `empirical_transition_aging_births`: RMSE=102930.84, rel=0.02768241
- `fixed20_aging_births`: RMSE=102930.84, rel=0.02768241
- `empirical_transition_aging_births_deaths`: RMSE=141570.23, rel=0.03807416
- `fixed20_aging_births_deaths`: RMSE=141570.23, rel=0.03807416
- `fixed20_aging_only`: RMSE=146963.86, rel=0.03952474
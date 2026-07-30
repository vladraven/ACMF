# Empirical Validation Protocol

Version: `3.3.1.8-clean-empirical-validation`.

The empirical validation stage asks whether ACMF works on real macroeconomic proxy data, not only synthetic trajectories.

## Questions

1. Does calibration converge?
2. Does the model reproduce historical dynamics?
3. Which parameters are stable across countries and seeds?
4. Which parameters are weak or non-identifiable?
5. Which observables matter most, based on ablation and Observation Designer ranking?
6. How does the model perform in retrospective backtests such as 2008?

## Default design

```text
Countries: Canada, Germany, Japan, Australia, Korea, Rep.
Training: 1995-2015
Validation: 2016-2024
Metrics: RMSE, MAE, MAPE, R², yearly dynamic error
```

Deployment smoke tasks use shorter windows for reproducible runtime.

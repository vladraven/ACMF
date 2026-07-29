# ACMF Phase II Calibration Scaffold

`src/acmf/calibration.py` implements a compact calibration pipeline for ACMF observed variables.

## Implemented components

- Huber loss for robust level residuals.
- Derivative mismatch term for local dynamic consistency.
- Differential Evolution for global search.
- L-BFGS-B for local refinement under bounds.
- Covariance/correlation diagnostics from the approximate inverse Hessian when available.
- Adaptive random-walk MCMC for posterior-like uncertainty exploration.
- Adequacy metrics: RMSE, MAE, R2, AIC, BIC.

## Status

This is a scaffold for Phase II calibration. It connects observed variables to the executable ACMF ODE core, but it is not a claim of completed empirical validation.

## Demo

```bash
PYTHONPATH=src python scripts/run_calibration_synthetic.py
```

## Notes

The demo intentionally uses small iteration counts for speed. Production calibration should increase `de_maxiter`, `popsize`, `mcmc_samples`, and use richer empirical data.

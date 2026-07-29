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


## Priors integration

`calibration.py` now integrates weak probabilistic priors directly into `ACMFObjective` through `PriorSpec`, `default_prior_specs`, `LossConfig.lambda_prior`, and `ACMFObjective.prior_penalty(theta)`.

Hard bounds remain the support constraints for Differential Evolution, L-BFGS-B, and MCMC proposals. Priors add an explicit negative-log-prior penalty to the objective, so they influence DE, local refinement, and MCMC acceptance through the same objective value.

Supported prior kinds:

- `uniform`
- `normal`
- `lognormal`
- `beta` on bounded intervals

This keeps the pipeline practical while making the prior layer operational rather than merely defined.

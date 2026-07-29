# ACMF Digital Twin and EnKF

`src/acmf/enkf.py` implements an Ensemble Kalman Filter for ACMF state tracking.

Observed variables are:

```text
P, Prod, A, Inst, F
```

Latent variables are:

```text
Ch, M, G, V, R
```

`src/acmf/digital_twin.py` wraps EnKF assimilation, state reporting, baseline forecasts, and scenario forecasts.

Demo:

```bash
PYTHONPATH=src python scripts/run_digital_twin.py
```

Status: experimental Phase III runtime scaffold. It is suitable for smoke tests and method development, but it is not a fully calibrated operational digital twin without empirical assimilation data and validated observation-noise/process-noise models.

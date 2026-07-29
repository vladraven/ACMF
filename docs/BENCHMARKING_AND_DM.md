# ACMF Benchmarking and Diebold-Mariano Tests

`src/acmf/benchmark_models.py` adds simple econometric benchmarks for forecast comparisons:

- RandomWalk / Persistence
- LinearTrend
- ARIMA(1,1,0) on first differences
- VAR(1) on first differences

`src/acmf/diebold_mariano.py` implements the Diebold-Mariano forecast accuracy test.

Demo:

```bash
PYTHONPATH=src python scripts/run_benchmark_dm.py
```

These benchmarks are intended as baselines for out-of-sample comparison. They do not replace ODE calibration.

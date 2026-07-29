# ACMF Runtime Diagnostics

`src/acmf/diagnostics.py` adds numerical diagnostics for the executable ODE system.

## Functions

- `numerical_jacobian(x, params)`
- `sign_matrix(J)`
- `check_demographic_decoupling(x, params)`
- `check_P_invariance(P_candidates, params)`
- `spectrum_analysis(x, params)`
- `feedback_loops_summary(x, params)`

## Sign of J[V,R]

`J[V,R]` is not universal. R has:

```text
positive indirect channel: R -> Education -> C -> Gap -> dV/dt
negative direct channel:  -beta12 * R * V
```

At default parameters, the direct stabilizing channel can dominate. When `beta12 = 0`, the indirect channel is positive.

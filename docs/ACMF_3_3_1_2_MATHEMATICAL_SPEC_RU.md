# ACMF 3.3.1.2 Mathematical Specification

Status: `ANALYTICAL CORE VALIDATED WITH ADAPTIVE DYNAMICS EXTENSION PROPOSED`.

## Corrected core

The ACMF 3.3.1.2 core inherits the corrected ACMF 3.3.1.1 structure:

- `Omega*_epsilon = [0,1]^8 * [0,4] * [epsilon, P_max]` is used for compactness and P-mode decoupling.
- `dSmin/dy = 0.5 * (1 + (x - y) / sqrt((x - y)^2 + epsilon))`.
- P-bound proofs use `K_bar = sup K_pop`, not an implicit `K0`.
- `dV/dR` is `mixed / parameter-dependent`.
- The L2 loop is not claimed positive without bifurcation analysis.
- Positive Bayesian parameters require LogNormal or truncated positive priors.
- Hamiltonian uses `<Psi, F_ODE(X, U, Theta)>`.
- `EI`, `Innovation`, and `StructuralLimits` are drivers unless explicitly bounded.

## State vector

```text
dim(X) = 10
X(t) = (A, Prod, Ch, M, G, V, Inst, R, F, P)
Omega = [0,1]^8 * [0,4] * R_+
Omega*_epsilon = [0,1]^8 * [0,4] * [epsilon, P_max]
```

## Adaptive Dynamics integration

ACMF 3.3.1.2 adds a diagnostic layer:

```text
States -> Dynamics -> Adaptive Dynamics Layer -> Criticality Index -> Phase Transition Probability -> Forecast
```

The extension is diagnostic by default. It does not automatically feed back into the ODE until empirical validation supports that step.


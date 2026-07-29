# ACMF 3.3.1.2 Audit Fixes

This document records the audit fixes applied to the deployable package.

## 1. Demographic mode separation

The invalid strict equality

```text
L_s / P = 0.6 * Smax(P, epsilon) / P = 0.6
```

has been removed from executable assumptions. The correct deployed relation is nonlinear near the smoothing layer:

```text
L_s / P = 0.6 * Smax(P, epsilon) / P
```

and it approaches `0.6` only asymptotically when `P >> sqrt(epsilon)`.

## 2. V-row Jacobian signs

The executable `V` equation keeps both R effects:

```text
positive indirect: R -> Education -> C -> Gap -> dV/dt
negative direct:   -beta12 * R * V
```

Therefore the universal claim `J[V,R] = +` or `J[V,R] = -` is not valid without a parameter/state region. At the default reference state, the direct stabilizing term dominates and `J[V,R] < 0`; when `beta12 = 0`, the indirect channel is positive. The audit regression tests document both cases.

## 3. L2 feedback loop

`L2` is a negative feedback loop because:

```text
Inst -> V : positive
V -> Inst : negative
```

## 4. P_max capacity bound

`K0` is retained. The function `1 - P/K` is increasing in `K`, so the worst-case upper estimate for the logistic birth component uses the maximum admissible carrying capacity, not `K_min`.

## 5. Positive and bounded parameter priors

The package now includes `src/acmf/priors.py` with positive and bounded transforms:

```text
LogNormalPrior
UnitIntervalPrior
BoundedPrior
```

## 6. Bounded indices

The deployed algebraic layer now bounds:

```text
EI
Innovation
StructuralLimits
```

Raw diagnostic values remain available as:

```text
EI_raw
Innovation_raw
StructuralLimits_raw
```

## 7. Hamiltonian notation

Documentation should use:

```text
H(X, U, Psi, Theta) = L(X, U, Theta) + <Psi, F(X, U, Theta)>
```

not `<Psi, F(X, Theta) U>`.

# ACMF Hypothesis Ladder

ACMF 3.3.1.2 uses a model-comparison ladder rather than a single-model confirmation strategy.

## H0

```text
Theta = const;
state space sufficient;
functional form correct.
```

## H2

```text
Theta = const;
state space incomplete.
```

Parameter drift may be compensation for omitted slow latent states.

## H1

```text
Theta = Theta(Regime)
```

Effective mechanisms change by regime.

## H3

```text
F(X, Theta) incomplete.
```

The functional form needs thresholds, delays, hysteresis, or new interactions.

## Order

```text
H0 -> H2 -> H1 -> H3
```

This order follows minimal model modification.

## Criticality hypotheses

```text
C0: Criticality has no explanatory value.
C1: Criticality explains parameter drift.
C2: Criticality predicts regime switches.
C3: TimeScaleMismatch is a leading indicator.
```


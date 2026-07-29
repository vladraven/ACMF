import numpy as np
import pandas as pd
from acmf.hypothesis_ladder import evaluate_hypothesis_ladder

SCENARIOS = {}
rng = np.random.default_rng(42)
t = np.arange(180)
x = 0.5 + 0.25 * np.sin(t / 18.0)
z = 0.4 + 0.2 * np.cos(t / 20.0)
stress = 1 - x
regime = np.where(stress > 0.55, "stress", "normal")

SCENARIOS["H0_constant"] = pd.DataFrame({"t": t, "x": x, "z": z, "stress": stress, "regime": regime, "dy": 0.7 * x + 0.02 + 0.01 * rng.normal(size=len(t))})
SCENARIOS["H2_missing_state"] = pd.DataFrame({"t": t, "x": x, "z": z, "stress": stress, "regime": regime, "dy": 0.4 * x + 0.8 * z + 0.01 * rng.normal(size=len(t))})
SCENARIOS["H1_regime"] = pd.DataFrame({"t": t, "x": x, "z": z, "stress": stress, "regime": regime, "dy": np.where(regime == "stress", 1.2 * x, 0.4 * x) + 0.01 * rng.normal(size=len(t))})
SCENARIOS["H3_functional_form"] = pd.DataFrame({"t": t, "x": x, "z": z, "stress": stress, "regime": regime, "dy": 0.4 * x + 2.5 * np.maximum(0, x - 0.6) ** 2 + 0.01 * rng.normal(size=len(t))})

for name, df in SCENARIOS.items():
    metrics, decision = evaluate_hypothesis_ladder(df)
    print("\n", name)
    print(decision)
    print(metrics.to_string(index=False))


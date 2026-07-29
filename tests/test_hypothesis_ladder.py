import numpy as np
import pandas as pd
from acmf.hypothesis_ladder import evaluate_hypothesis_ladder


def test_h0_selected_for_simple_constant_case():
    rng = np.random.default_rng(1)
    t = np.arange(120)
    x = 0.5 + 0.2 * np.sin(t / 12)
    dy = 0.7 * x + 0.02 + 0.01 * rng.normal(size=len(t))
    df = pd.DataFrame({"t": t, "x": x, "dy": dy, "stress": 1 - x, "z": np.r_[0, dy[:-1]], "regime": "normal"})
    metrics, decision = evaluate_hypothesis_ladder(df)
    assert decision["model"] == "A_const"

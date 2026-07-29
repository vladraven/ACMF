from __future__ import annotations
import numpy as np
import pandas as pd


def rmse(y, yhat):
    return float(np.sqrt(np.mean((np.asarray(y) - np.asarray(yhat)) ** 2)))


def design_constant(df):
    return np.column_stack([np.ones(len(df)), df["x"]]), ["intercept", "theta_x"]


def design_expanded_state(df):
    return np.column_stack([np.ones(len(df)), df["x"], df["z"]]), ["intercept", "theta_x", "theta_z"]


def design_regime(df):
    stress = (df.get("regime", pd.Series(["normal"] * len(df))).astype(str).to_numpy() == "stress").astype(float)
    if "stress" in df.columns:
        stress = np.where(df["stress"].to_numpy(float) > 0.55, 1.0, stress)
    normal = 1.0 - stress
    return np.column_stack([np.ones(len(df)), df["x"] * normal, df["x"] * stress]), ["intercept", "theta_x_normal", "theta_x_stress"]


def design_functional(df):
    threshold = np.maximum(0.0, df["x"].to_numpy(float) - 0.60) ** 2
    return np.column_stack([np.ones(len(df)), df["x"], threshold]), ["intercept", "theta_x", "theta_threshold"]


MODELS = {
    "A_const": (design_constant, ["t", "dy", "x"]),
    "B_expanded_state": (design_expanded_state, ["t", "dy", "x", "z"]),
    "C_regime": (design_regime, ["t", "dy", "x", "stress"]),
    "D_functional_form": (design_functional, ["t", "dy", "x"]),
}

HYPOTHESIS_FOR_MODEL = {
    "A_const": "H0_constant_parameters_sufficient",
    "B_expanded_state": "H2_incomplete_state_space_supported",
    "C_regime": "H1_regime_dependent_parameters_supported",
    "D_functional_form": "H3_incomplete_functional_form_supported",
}


def fit_linear(X, y):
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    return coef


def evaluate_hypothesis_ladder(df, train_frac=0.67):
    df = df.sort_values("t").reset_index(drop=True)
    n_train = int(len(df) * train_frac)
    train = df.iloc[:n_train]
    test = df.iloc[n_train:]
    rows = []
    for name, (design_fn, required) in MODELS.items():
        if not all(c in df.columns for c in required):
            continue
        Xtr, cols = design_fn(train)
        coef = fit_linear(Xtr, train["dy"].to_numpy(float))
        Xte, _ = design_fn(test)
        pred = Xte @ coef
        resid = test["dy"].to_numpy(float) - pred
        mse = max(float(np.mean(resid ** 2)), 1e-300)
        k = len(cols)
        bic_like = float(len(test) * np.log(mse) + k * np.log(len(test)))
        rows.append({
            "model": name,
            "supported_hypothesis": HYPOTHESIS_FOR_MODEL[name],
            "n_parameters": k,
            "test_rmse": rmse(test["dy"], pred),
            "test_bic_like": bic_like,
        })
    metrics = pd.DataFrame(rows).sort_values("test_bic_like") if rows else pd.DataFrame()
    decision = metrics.iloc[0].to_dict() if not metrics.empty else None
    return metrics, decision


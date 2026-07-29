from pathlib import Path
import pandas as pd
from .hypothesis_ladder import evaluate_hypothesis_ladder

REQUIRED_COLUMNS = ["t", "dy", "x"]


def load_research_csv(path):
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    for col in ["t", "dy", "x", "z", "stress", "y"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="raise")
    if "regime" in df.columns:
        df["regime"] = df["regime"].astype(str)
    return df.sort_values("t").reset_index(drop=True)


def run_empirical_csv(path):
    df = load_research_csv(path)
    metrics, decision = evaluate_hypothesis_ladder(df)
    return {"metrics": metrics, "decision": decision}

#!/usr/bin/env python3
"""
Synthetic Forecast Benchmark v2: ACMF vs linear baselines.

Two modes:
  response - target = dy (signed response); prediction = w_A*dA/dt + w_Prod*dProd/dt + w_Inst*dInst/dt + w_R*dR/dt
  state    - target = A,Prod,Inst,R (state proxies); prediction = forward-integrated ACMF states
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path
from typing import NamedTuple
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from acmf.core import STATE_NAMES, default_params, rhs
from acmf.solver import rk4_step

OBS_HEAD_WEIGHTS = {"A": 0.40, "Prod": 0.30, "Inst": 0.20, "R": 0.10}
OBS_HEAD_INDICES = {name: i for i, name in enumerate(STATE_NAMES)}

DIAGNOSTIC_SCENARIOS = (
    "low_stress_trend",
    "level_shift_shock_recovery",
    "saturation_curve",
    "regime_change_stress",
)

EXPECTED_WINNERS = {
    "state": {
        "low_stress_trend":           {"acmf"},
        "level_shift_shock_recovery": {"acmf"},
        "saturation_curve":           {"acmf"},
        "regime_change_stress":       {"acmf"},
    },
    "response": {
        "low_stress_trend":           {"linear_trend"},
        "level_shift_shock_recovery": {"acmf"},
        "saturation_curve":           {"acmf"},
        "regime_change_stress":       {"acmf"},
    },
}

EXPECTED_NOTES = {
    "low_stress_trend":           "state: ACMF tracks slowly rising A; response: linear_trend wins",
    "level_shift_shock_recovery": "expected winner: ACMF or nonlinear recovery model",
    "saturation_curve":           "expected winner: ACMF or logistic/saturation baseline",
    "regime_change_stress":       "expected winner: ACMF only if stress dynamics work",
}


class BenchmarkResult(NamedTuple):
    mode: str
    scenario: str
    model: str
    horizon: int
    rmse: float
    mae: float
    mape: float
    r2: float


class ForecastBenchmark:
    def __init__(self, scenario_name: str, seed: int = 42):
        self.scenario_name = scenario_name
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.results: list[BenchmarkResult] = []
        self.trace_rows: list[dict] = []
        self.trajectory_rows: list[dict] = []

    def generate_synthetic_data(self, n_steps: int = 200, noise_level: float = 0.01) -> dict:
        t = np.arange(n_steps)
        if self.scenario_name == "low_stress_trend":
            x = 0.5 + 0.1 * t / n_steps
            z = 0.4 + 0.05 * t / n_steps
            stress = 1 - x
            dy = 0.7 * x + 0.02 + noise_level * self.rng.normal(size=n_steps)
        elif self.scenario_name == "high_volatility":
            x = 0.5 + 0.25 * np.sin(t / 18.0)
            z = 0.4 + 0.2 * np.cos(t / 20.0)
            stress = 1 - x
            dy = 0.7 * x + 0.02 + noise_level * self.rng.normal(size=n_steps)
        elif self.scenario_name == "level_shift_shock_recovery":
            x = np.zeros(n_steps)
            x[:60] = 0.5 + 0.02 * np.sin(t[:60] / 30.0)
            x[60:100] = 0.3 - 0.1 * np.exp(-(t[60:100] - 60) / 10.0)
            x[100:] = 0.3 + 0.15 * (1 - np.exp(-(t[100:] - 100) / 20.0))
            z = 0.4 + 0.05 * np.sin(t / 40.0)
            stress = np.maximum(0.3, 1 - x)
            dy = 0.5 * x + 0.3 * stress + 0.02 + noise_level * self.rng.normal(size=n_steps)
        elif self.scenario_name == "saturation_curve":
            x = 0.3 / (1.0 + 2.0 * np.exp(-0.02 * (t - 90)))
            z = 0.2 / (1.0 + 2.5 * np.exp(-0.015 * (t - 80)))
            stress = 1 - x
            dy = 0.6 * x / (1.0 + 0.5 * x) + 0.01 + noise_level * self.rng.normal(size=n_steps)
        elif self.scenario_name == "regime_change_stress":
            t_stress = 1 - 0.5 * np.sin(t / 40.0) - 0.3 * np.cos(t / 60.0)
            stress = np.clip(t_stress, 0.2, 1.0)
            rsw = 90
            x = np.zeros(n_steps)
            x[:rsw] = 0.6 + 0.1 * np.sin(t[:rsw] / 20.0)
            x[rsw:] = 0.3 - 0.15 * (1 - np.exp(-(t[rsw:] - rsw) / 30.0))
            z = 0.4 + 0.08 * np.cos(t / 25.0)
            dy = np.where(stress > 0.7, 0.2 * x - 0.4 * (stress - 0.5), 0.7 * x - 0.1 * stress) + 0.01 + noise_level * self.rng.normal(size=n_steps)
        elif self.scenario_name == "regime_switch":
            x = 0.5 + 0.15 * np.sin(t / 25.0)
            z = 0.4 + 0.1 * np.cos(t / 30.0)
            stress = 1 - x
            regime = np.where(stress > 0.55, "stress", "normal")
            dy = np.where(regime == "stress", 1.2 * x, 0.4 * x) + 0.01 * self.rng.normal(size=n_steps)
        elif self.scenario_name == "nonlinear_transform":
            x = 0.5 + 0.2 * np.sin(t / 22.0)
            z = 0.4 + 0.15 * np.cos(t / 25.0)
            stress = 1 - x
            dy = 0.4 * x + 2.5 * np.maximum(0, x - 0.6) ** 2 + 0.01 * self.rng.normal(size=n_steps)
        else:
            raise ValueError(f"Unknown scenario: {self.scenario_name}")
        regime_out = np.where(stress > 0.55, "stress", "normal") if self.scenario_name not in ("regime_switch",) else regime
        return {"t": t, "x": x, "z": z, "stress": stress, "dy": dy, "regime": regime_out}

    @staticmethod
    def linear_trend_forecast(y: np.ndarray, horizon: int) -> np.ndarray:
        c = np.polyfit(np.arange(len(y)), y, 1)
        return np.polyval(c, np.arange(len(y), len(y) + horizon))

    @staticmethod
    def linear_ar1_forecast(y: np.ndarray, horizon: int) -> np.ndarray:
        phi = np.clip(np.corrcoef(y[:-1], y[1:])[0, 1], -0.99, 0.99)
        out = np.zeros(horizon); last = y[-1]
        for i in range(horizon): out[i] = phi * last; last = out[i]
        return out

    def _build_state(self, data: dict, idx: int) -> np.ndarray:
        return np.array([
            float(data["x"][idx]), 0.2, float(data["z"][idx]),
            0.5, 0.4, float(np.clip(data["stress"][idx], 0.0, 1.0)),
            0.5, 0.5, 2.0, 100.0,
        ], dtype=float)

    @staticmethod
    def _step(state: np.ndarray, params) -> np.ndarray:
        s = rk4_step(state, 1.0, params)
        s[:8] = np.clip(s[:8], 0.0, 1.0); s[8] = np.clip(s[8], 0.0, 4.0); s[9] = max(s[9], 0.0)
        return s

    def acmf_response_forecast(self, data: dict, train_size: int, horizon: int) -> np.ndarray:
        """Signed dy forecast via weighted sum of state derivatives (observation head P1)."""
        params = default_params()
        state = self._build_state(data, train_size - 1)
        out = np.zeros(horizon)
        for i in range(horizon):
            dx = rhs(state, params)
            out[i] = float(sum(OBS_HEAD_WEIGHTS[n] * dx[OBS_HEAD_INDICES[n]] for n in OBS_HEAD_WEIGHTS))
            state = self._step(state, params)
        return out

    def acmf_state_forecast(self, data: dict, train_size: int, horizon: int,
                             target_states: tuple) -> dict:
        """Forward-integrate ACMF and return per-state forecasts."""
        params = default_params()
        state = self._build_state(data, train_size - 1)
        trajs = {n: np.zeros(horizon) for n in target_states}
        for i in range(horizon):
            state = self._step(state, params)
            for n in target_states: trajs[n][i] = state[OBS_HEAD_INDICES[n]]
        return trajs

    @staticmethod
    def evaluate_forecast(actual: np.ndarray, predicted: np.ndarray) -> dict:
        r = actual - predicted
        rmse = float(np.sqrt(np.mean(r ** 2)))
        mae = float(np.mean(np.abs(r)))
        mask = actual != 0
        mape = float(100 * np.mean(np.abs(r[mask] / actual[mask])) if mask.any() else np.inf)
        ss_res = float(np.sum(r ** 2)); ss_tot = float(np.sum((actual - np.mean(actual)) ** 2))
        r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0
        return {"rmse": rmse, "mae": mae, "mape": mape, "r2": r2}

    def run_response_benchmark(self, horizon: int = 30, split: float = 0.8) -> list:
        data = self.generate_synthetic_data()
        y = data["dy"]; train_size = int(len(y) * split)
        test = y[train_size: train_size + horizon]
        if len(test) < horizon: return []
        preds = {
            "linear_trend": self.linear_trend_forecast(y[:train_size], horizon),
            "ar1":          self.linear_ar1_forecast(y[:train_size], horizon),
            "acmf":         self.acmf_response_forecast(data, train_size, horizon),
        }
        self.results = []
        for model, pred in preds.items():
            m = self.evaluate_forecast(test, pred)
            self.results.append(BenchmarkResult("response", self.scenario_name, model, horizon, m["rmse"], m["mae"], m["mape"], m["r2"]))
        self._store_trace(data, test, preds, train_size)
        return self.results

    def run_state_benchmark(self, horizon: int = 30, split: float = 0.8,
                             target_states: tuple = ("A", "Prod", "Inst", "R")) -> list:
        """Forward-integrate ACMF and return per-state forecasts."""
        data = self.generate_synthetic_data()
        train_size = int(len(data["t"]) * split)
        state_proxies = {
            "A":    data["x"],
            "Prod": data["x"] * 0.7,
            "Inst": data["z"],
            "R":    np.clip(1 - data["stress"], 0.0, 1.0),
        }
        acmf_trajs = self.acmf_state_forecast(data, train_size, horizon, target_states)
        self.results = []
        for sname in target_states:
            if sname not in state_proxies: continue
            actual = state_proxies[sname][train_size: train_size + horizon]
            if len(actual) < horizon: continue
            train_s = state_proxies[sname][:train_size]
            preds = {
                "linear_trend": self.linear_trend_forecast(train_s, horizon),
                "ar1":          self.linear_ar1_forecast(train_s, horizon),
                "acmf":         acmf_trajs[sname],
            }
            for model, pred in preds.items():
                m = self.evaluate_forecast(actual, pred)
                self.results.append(BenchmarkResult("state", self.scenario_name, f"{model}:{sname}", horizon, m["rmse"], m["mae"], m["mape"], m["r2"]))
        return self.results

    def run_benchmark(self, horizon: int = 30, mode: str = "response") -> list:
        if mode == "state": return self.run_state_benchmark(horizon=horizon)
        return self.run_response_benchmark(horizon=horizon)

    def _store_trace(self, data, test, preds, train_size):
        years = data["t"][train_size: train_size + len(test)]
        for i in range(len(test)):
            c = {"scenario": self.scenario_name, "year": int(years[i]), "actual": float(test[i]),
                 "x": float(data["x"][train_size + i]), "stress": float(data["stress"][train_size + i])}
            self.trajectory_rows.append(c | {"linear_trend_pred": float(preds["linear_trend"][i]),
                                              "ar1_pred": float(preds["ar1"][i]), "acmf_pred": float(preds["acmf"][i])})
            for model, pred in preds.items():
                err = float(test[i] - pred[i])
                self.trace_rows.append(c | {"model": model, "predicted": float(pred[i]),
                                             "error": err, "abs_error": abs(err), "squared_error": err * err})

    def print_results(self, mode: str = "response"):
        if not self.results: print("No results"); return
        df = pd.DataFrame(self.results)
        print(f"\n{'=' * 80}\n[{mode.upper()}] Benchmark: {self.scenario_name}\n{'=' * 80}")
        print(df.to_string(index=False))
        for metric in ("rmse", "mae", "r2"):
            idx = df[metric].idxmin() if metric != "r2" else df[metric].idxmax()
            direction = "[lower]" if metric != "r2" else "[higher]"
            row = df.iloc[idx]
            print(f"{metric.upper():6} | {row['model']:20} | {row[metric]:9.4f} {direction}")


def _winners_df(metrics_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (mode, scenario), g in metrics_df.groupby(["mode", "scenario"], sort=False):
        rows.append({"mode": mode, "scenario": scenario,
                     "best_rmse_model": g.loc[g["rmse"].idxmin(), "model"], "best_rmse_value": float(g["rmse"].min()),
                     "best_r2_model": g.loc[g["r2"].idxmax(), "model"], "best_r2_value": float(g["r2"].max())})
    return pd.DataFrame(rows)


def _expected_match_df(winners: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in winners.iterrows():
        mode, scenario = row["mode"], row["scenario"]
        expected = EXPECTED_WINNERS.get(mode, {}).get(scenario, set())
        rmse_win = row["best_rmse_model"].split(":")[0]
        r2_win = row["best_r2_model"].split(":")[0]
        rows.append({"mode": mode, "scenario": scenario,
                     "expected_models": ",".join(sorted(expected)),
                     "expected_note": EXPECTED_NOTES.get(scenario, ""),
                     "best_rmse_model": row["best_rmse_model"], "best_r2_model": row["best_r2_model"],
                     "expected_match": bool(rmse_win in expected or r2_win in expected)})
    return pd.DataFrame(rows)


def run_diagnostic_suite(seed: int = 42, horizon: int = 30,
                         output_dir: Path = Path("artifacts/diagnostics")) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics_rows, error_rows, traj_rows = [], [], []
    for mode in ("response", "state"):
        for scenario in DIAGNOSTIC_SCENARIOS:
            bench = ForecastBenchmark(scenario_name=scenario, seed=seed)
            results = bench.run_benchmark(horizon=horizon, mode=mode)
            metrics_rows.extend(r._asdict() for r in results)
            error_rows.extend(bench.trace_rows)
            traj_rows.extend(bench.trajectory_rows)
            bench.print_results(mode=mode)
    metrics_df = pd.DataFrame(metrics_rows)
    winners_df = _winners_df(metrics_df)
    expected_df = _expected_match_df(winners_df)
    out = {"synthetic_forecast_metrics.csv": metrics_df,
           "synthetic_forecast_winners.csv": winners_df,
           "synthetic_forecast_expected_match.csv": expected_df,
           "synthetic_forecast_error_by_year.csv": pd.DataFrame(error_rows),
           "synthetic_forecast_trajectories.csv": pd.DataFrame(traj_rows)}
    for name, df in out.items(): df.to_csv(output_dir / name, index=False)
    print(f"\nSaved to: {output_dir}")
    print(expected_df[["mode", "scenario", "best_rmse_model", "expected_match"]].to_string(index=False))
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=["low_stress_trend", "high_volatility", "regime_switch", "nonlinear_transform",
                                                "level_shift_shock_recovery", "saturation_curve", "regime_change_stress", "all_diagnostics"], default="high_volatility")
    parser.add_argument("--mode", choices=["response", "state"], default="response")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--horizon", type=int, default=30)
    parser.add_argument("--output-dir", default="artifacts/diagnostics")
    parser.add_argument("--export-csv", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    if args.scenario == "all_diagnostics":
        run_diagnostic_suite(seed=args.seed, horizon=args.horizon, output_dir=Path(args.output_dir))
        return 0
    bench = ForecastBenchmark(args.scenario, seed=args.seed)
    bench.run_benchmark(horizon=args.horizon, mode=args.mode)
    bench.print_results(mode=args.mode)
    if args.export_csv:
        od = Path(args.output_dir); od.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(r._asdict() for r in bench.results).to_csv(od / "synthetic_forecast_metrics.csv", index=False)
        pd.DataFrame(bench.trace_rows).to_csv(od / "synthetic_forecast_error_by_year.csv", index=False)
        pd.DataFrame(bench.trajectory_rows).to_csv(od / "synthetic_forecast_trajectories.csv", index=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())

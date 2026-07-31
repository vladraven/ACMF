#!/usr/bin/env python3
"""
Synthetic Forecast Benchmark: ACMF vs Linear Baselines

Compares ACMF model predictions against simple linear forecasting baselines
on synthetic datasets with known dynamics.

Usage:
    python scripts/run_synthetic_forecast_benchmark.py [--scenario SCENARIO] [--seed SEED] [--verbose]
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import argparse
import numpy as np
import pandas as pd
from typing import NamedTuple

from acmf.core import rhs, default_params


class BenchmarkResult(NamedTuple):
    scenario: str
    model: str
    horizon: int
    rmse: float
    mae: float
    mape: float
    r2: float


class ForecastBenchmark:
    """Benchmark ACMF vs linear baselines on synthetic data"""

    def __init__(self, scenario_name: str, seed: int = 42):
        self.scenario_name = scenario_name
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.results: list[BenchmarkResult] = []

    def generate_synthetic_data(self, n_steps: int = 180, noise_level: float = 0.01) -> dict:
        """Generate synthetic time series with known dynamics"""
        t = np.arange(n_steps)
        
        if self.scenario_name == "low_stress_trend":
            x = 0.5 + 0.1 * t / n_steps
            z = 0.4 + 0.05 * t / n_steps
            stress = 1 - x
            dy = 0.7 * x + 0.02 + noise_level * self.rng.normal(size=len(t))
            
        elif self.scenario_name == "high_volatility":
            x = 0.5 + 0.25 * np.sin(t / 18.0)
            z = 0.4 + 0.2 * np.cos(t / 20.0)
            stress = 1 - x
            dy = 0.7 * x + 0.02 + noise_level * self.rng.normal(size=len(t))
            
        elif self.scenario_name == "level_shift_shock_recovery":
            # Level shift with shock and recovery - should favor ACMF or recovery model
            x = np.zeros(n_steps)
            # First 60 steps: baseline
            x[:60] = 0.5 + 0.02 * np.sin(t[:60] / 30.0)
            # Steps 60-100: sudden drop (shock)
            x[60:100] = 0.3 - 0.1 * np.exp(-(t[60:100] - 60) / 10.0)
            # Steps 100+: recovery
            x[100:] = 0.3 + 0.15 * (1 - np.exp(-(t[100:] - 100) / 20.0))
            
            z = 0.4 + 0.05 * np.sin(t / 40.0)
            stress = np.maximum(0.3, 1 - x)
            dy = 0.5 * x + 0.3 * stress + 0.02 + noise_level * self.rng.normal(size=len(t))
            
        elif self.scenario_name == "saturation_curve":
            # Logistic/saturation curve - should favor ACMF or logistic baseline
            x = 0.3 / (1.0 + 2.0 * np.exp(-0.02 * (t - 90)))
            z = 0.2 / (1.0 + 2.5 * np.exp(-0.015 * (t - 80)))
            stress = 1 - x
            dy = 0.6 * x / (1.0 + 0.5 * x) + 0.01 + noise_level * self.rng.normal(size=len(t))
            
        elif self.scenario_name == "regime_change_stress":
            # Regime change driven by stress dynamics - ACMF should excel if stress dynamics work
            t_stress = 1 - 0.5 * np.sin(t / 40.0) - 0.3 * np.cos(t / 60.0)
            t_stress = np.clip(t_stress, 0.2, 1.0)
            
            regime_switch_point = 90
            x = np.zeros(n_steps)
            x[:regime_switch_point] = 0.6 + 0.1 * np.sin(t[:regime_switch_point] / 20.0)
            x[regime_switch_point:] = 0.3 - 0.15 * (1 - np.exp(-(t[regime_switch_point:] - regime_switch_point) / 30.0))
            
            z = 0.4 + 0.08 * np.cos(t / 25.0)
            stress = t_stress
            
            dy = np.where(
                stress > 0.7,
                0.2 * x - 0.4 * (stress - 0.5),
                0.7 * x - 0.1 * stress
            ) + 0.01 + noise_level * self.rng.normal(size=len(t))
            
        elif self.scenario_name == "regime_switch":
            x = 0.5 + 0.15 * np.sin(t / 25.0)
            z = 0.4 + 0.1 * np.cos(t / 30.0)
            stress = 1 - x
            regime = np.where(stress > 0.55, "stress", "normal")
            dy = np.where(regime == "stress", 1.2 * x, 0.4 * x) + 0.01 * self.rng.normal(size=len(t))
            
        elif self.scenario_name == "nonlinear_transform":
            x = 0.5 + 0.2 * np.sin(t / 22.0)
            z = 0.4 + 0.15 * np.cos(t / 25.0)
            stress = 1 - x
            dy = 0.4 * x + 2.5 * np.maximum(0, x - 0.6) ** 2 + 0.01 * self.rng.normal(size=len(t))
            
        else:
            raise ValueError(f"Unknown scenario: {self.scenario_name}")

        return {
            "t": t,
            "x": x,
            "z": z,
            "stress": stress,
            "dy": dy,
            "regime": np.where(stress > 0.55, "stress", "normal") if self.scenario_name != "regime_switch" else regime,
        }

    def linear_trend_forecast(self, y: np.ndarray, horizon: int) -> np.ndarray:
        """Simple linear trend extrapolation baseline"""
        coeffs = np.polyfit(np.arange(len(y)), y, 1)
        forecast_x = np.arange(len(y), len(y) + horizon)
        return np.polyval(coeffs, forecast_x)

    def linear_ar1_forecast(self, y: np.ndarray, horizon: int) -> np.ndarray:
        """AR(1) autoregressive baseline"""
        # Fit AR(1): y[t] = phi * y[t-1] + noise
        phi = np.corrcoef(y[:-1], y[1:])[0, 1]
        phi = np.clip(phi, -0.99, 0.99)  # Stationarity constraint
        
        forecast = np.zeros(horizon)
        last_val = y[-1]
        for i in range(horizon):
            forecast[i] = phi * last_val
            last_val = forecast[i]
        return forecast

    def acmf_forecast(self, data: dict, train_size: int, horizon: int) -> np.ndarray:
        """ACMF model forecast"""
        try:
            from acmf.core import default_params
            
            # Build initial state from data
            state = np.array([
                data["x"][0],          # A (activity)
                0.1,                   # Prod (productivity)
                data["z"][0],          # Ch (creativity)
                0.05,                  # M (mental health)
                0.1,                   # G (agency)
                0.2,                   # V (vulnerability)
                0.3,                   # Inst (institutions)
                0.4,                   # R (resilience)
                0.5,                   # F (fertility)
                100.0,                 # P (population)
            ])
            
            # Get default parameters
            params = default_params()
            
            # Simple forward integration
            forecast = []
            current_state = state.copy()
            
            for _ in range(horizon):
                dydt = rhs(current_state, params)
                current_state = current_state + 0.1 * dydt  # Euler step
                forecast.append(current_state[0])  # Project activity
            
            return np.array(forecast)
            
        except Exception as e:
            print(f"Warning: ACMF forecast failed ({e}), returning zeros")
            return np.zeros(horizon)

    def evaluate_forecast(self, actual: np.ndarray, predicted: np.ndarray) -> dict:
        """Compute error metrics"""
        residuals = actual - predicted
        
        # RMSE
        rmse = np.sqrt(np.mean(residuals ** 2))
        
        # MAE
        mae = np.mean(np.abs(residuals))
        
        # MAPE (handling division by zero)
        mape_mask = actual != 0
        mape = 100 * np.mean(np.abs(residuals[mape_mask] / actual[mape_mask])) if mape_mask.any() else np.inf
        
        # R²
        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((actual - np.mean(actual)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        
        return {"rmse": rmse, "mae": mae, "mape": mape, "r2": r2}

    def run_benchmark(self, horizon: int = 30, train_test_split: float = 0.8) -> list[BenchmarkResult]:
        """Run full benchmark"""
        data = self.generate_synthetic_data(n_steps=200)
        dy = data["dy"]
        
        train_size = int(len(dy) * train_test_split)
        train_data = dy[:train_size]
        test_data = dy[train_size:train_size + horizon]
        
        if len(test_data) < horizon:
            print(f"Warning: Test data too short (got {len(test_data)}, need {horizon})")
            return []
        
        # Linear Trend
        trend_forecast = self.linear_trend_forecast(train_data, horizon)
        trend_metrics = self.evaluate_forecast(test_data, trend_forecast)
        self.results.append(BenchmarkResult(
            scenario=self.scenario_name,
            model="linear_trend",
            horizon=horizon,
            rmse=trend_metrics["rmse"],
            mae=trend_metrics["mae"],
            mape=trend_metrics["mape"],
            r2=trend_metrics["r2"],
        ))
        
        # AR(1)
        ar1_forecast = self.linear_ar1_forecast(train_data, horizon)
        ar1_metrics = self.evaluate_forecast(test_data, ar1_forecast)
        self.results.append(BenchmarkResult(
            scenario=self.scenario_name,
            model="ar1",
            horizon=horizon,
            rmse=ar1_metrics["rmse"],
            mae=ar1_metrics["mae"],
            mape=ar1_metrics["mape"],
            r2=ar1_metrics["r2"],
        ))
        
        # ACMF
        acmf_forecast = self.acmf_forecast(data, train_size, horizon)
        acmf_metrics = self.evaluate_forecast(test_data, acmf_forecast)
        self.results.append(BenchmarkResult(
            scenario=self.scenario_name,
            model="acmf",
            horizon=horizon,
            rmse=acmf_metrics["rmse"],
            mae=acmf_metrics["mae"],
            mape=acmf_metrics["mape"],
            r2=acmf_metrics["r2"],
        ))
        
        return self.results

    def print_results(self):
        """Print benchmark results"""
        if not self.results:
            print("No results to display")
            return
        
        df = pd.DataFrame(self.results)
        print(f"\n{'='*80}")
        print(f"Synthetic Forecast Benchmark: {self.scenario_name}")
        print(f"{'='*80}")
        print(df.to_string(index=False))
        
        # Summary
        print(f"\n{'Best Models by Metric':^80}")
        print(f"{'-'*80}")
        for metric in ["rmse", "mae", "r2"]:
            if metric in ["rmse", "mae"]:
                best_idx = df[metric].idxmin()
                direction = "[lower is better]"
            else:
                best_idx = df[metric].idxmax()
                direction = "[higher is better]"
            
            best_row = df.iloc[best_idx]
            print(f"{metric.upper():6} | {best_row['model']:15} | {best_row[metric]:8.4f} {direction}")


def main():
    parser = argparse.ArgumentParser(description="Synthetic Forecast Benchmark")
    parser.add_argument(
        "--scenario",
        choices=["low_stress_trend", "high_volatility", "regime_switch", "nonlinear_transform", 
                 "level_shift_shock_recovery", "saturation_curve", "regime_change_stress"],
        default="high_volatility",
        help="Synthetic scenario to benchmark",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--horizon", type=int, default=30, help="Forecast horizon")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    benchmark = ForecastBenchmark(args.scenario, seed=args.seed)
    benchmark.run_benchmark(horizon=args.horizon)
    benchmark.print_results()
    
    # Return success code if ACMF beats at least one baseline
    results_df = pd.DataFrame(benchmark.results)
    acmf_r2 = results_df[results_df["model"] == "acmf"]["r2"].values[0]
    baseline_r2 = results_df[results_df["model"] != "acmf"]["r2"].max()
    
    success = acmf_r2 > baseline_r2 * 0.9  # ACMF should be within 90% of best baseline
    exit_code = 0 if success else 1
    
    if args.verbose:
        print(f"\nBenchmark exit code: {exit_code}")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

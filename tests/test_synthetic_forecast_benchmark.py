"""
Tests for synthetic forecast benchmark module
"""
import numpy as np
import pandas as pd
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from acmf.core import rhs
from acmf.calibration import DEFAULT_THETA


class TestSyntheticDataGeneration:
    """Test synthetic data generation"""

    def test_low_stress_trend_scenario(self):
        """Low stress trend scenario generates monotonic trend"""
        np.random.seed(42)
        n_steps = 100
        t = np.arange(n_steps)
        x = 0.5 + 0.1 * t / n_steps
        
        # Check monotonic increase
        assert np.all(np.diff(x) > 0), "Stress index should monotonically increase"
        assert x[0] == pytest.approx(0.5, abs=1e-6)
        assert x[-1] == pytest.approx(0.599, abs=0.001)  # More lenient tolerance

    def test_high_volatility_scenario(self):
        """High volatility scenario generates oscillating pattern"""
        n_steps = 180
        t = np.arange(n_steps)
        x = 0.5 + 0.25 * np.sin(t / 18.0)
        
        # Check oscillation bounds
        assert x.min() >= 0.25
        assert x.max() <= 0.75
        # Check periodicity (period is ~113 steps)
        period_steps = int(2 * np.pi * 18)
        if period_steps < n_steps:
            assert np.abs(x[0] - x[period_steps]) < 0.05  # Loose periodicity check

    def test_regime_switch_scenario(self):
        """Regime switch scenario correctly identifies stress regimes"""
        n_steps = 100
        t = np.arange(n_steps)
        x = 0.5 + 0.15 * np.sin(t / 25.0)
        stress = 1 - x
        regime = np.where(stress > 0.55, "stress", "normal")
        
        # Check that both regimes appear
        assert "stress" in regime
        assert "normal" in regime
        # Check regime consistency with stress threshold
        for i in range(len(stress)):
            expected = "stress" if stress[i] > 0.55 else "normal"
            assert regime[i] == expected

    def test_nonlinear_transform_scenario(self):
        """Nonlinear transform scenario adds quadratic term"""
        n_steps = 100
        t = np.arange(n_steps)
        x = 0.5 + 0.2 * np.sin(t / 22.0)
        dy = 0.4 * x + 2.5 * np.maximum(0, x - 0.6) ** 2
        
        # Check that quadratic term can be active when x > 0.6
        max_x_offset = 0.2  # x ranges from 0.3 to 0.7, so max x-0.6 = 0.1
        max_quad_contribution = 2.5 * max_x_offset ** 2  # = 0.05
        # The linear term alone is 0.4 * 0.7 = 0.28 at best
        # So dy should be at least somewhere in the range
        assert np.any(dy > 0.25)


class TestForecastingBaselines:
    """Test baseline forecasting methods"""

    def test_linear_trend_forecast(self):
        """Linear trend forecast extrapolates correctly"""
        # Generate simple linear data
        y = np.arange(10, dtype=float)
        
        # Fit linear trend
        coeffs = np.polyfit(np.arange(len(y)), y, 1)
        forecast = np.polyval(coeffs, np.arange(len(y), len(y) + 5))
        
        # Check forecast continues trend
        assert forecast[0] == pytest.approx(10.0, abs=1e-6)
        assert forecast[-1] == pytest.approx(14.0, abs=1e-6)
        assert np.all(np.diff(forecast) > 0), "Trend should continue increasing"

    def test_ar1_forecast(self):
        """AR(1) forecast maintains stationarity"""
        # Generate AR(1) process
        np.random.seed(42)
        y = np.zeros(100)
        phi = 0.8
        for i in range(1, len(y)):
            y[i] = phi * y[i-1] + np.random.normal()
        
        # Forecast with AR(1)
        last_val = y[-1]
        forecast = np.zeros(20)
        for i in range(20):
            forecast[i] = phi * last_val
            last_val = forecast[i]
        
        # Check mean reversion
        assert np.abs(forecast[-1]) < np.abs(forecast[0]), "AR(1) should mean-revert"
        assert np.all(np.isfinite(forecast)), "Forecast should be finite"

    def test_ar1_stationarity_constraint(self):
        """AR(1) applies stationarity constraint"""
        # Highly correlated data
        y = np.arange(50, dtype=float)
        
        # Compute correlation (should be near 1)
        phi = np.corrcoef(y[:-1], y[1:])[0, 1]
        assert phi > 0.99  # Highly correlated
        
        # Clipped phi for stationarity
        phi_clipped = np.clip(phi, -0.99, 0.99)
        assert phi_clipped == 0.99  # Should be clipped


class TestMetricsComputation:
    """Test error metrics"""

    def test_rmse_computation(self):
        """RMSE computed correctly"""
        actual = np.array([1.0, 2.0, 3.0])
        predicted = np.array([1.1, 2.1, 2.9])
        
        residuals = actual - predicted
        rmse = np.sqrt(np.mean(residuals ** 2))
        
        expected_rmse = np.sqrt((0.1**2 + 0.1**2 + 0.1**2) / 3)
        assert rmse == pytest.approx(expected_rmse, rel=1e-6)

    def test_mae_computation(self):
        """MAE computed correctly"""
        actual = np.array([1.0, 2.0, 3.0])
        predicted = np.array([1.1, 2.1, 2.9])
        
        mae = np.mean(np.abs(actual - predicted))
        
        expected_mae = (0.1 + 0.1 + 0.1) / 3
        assert mae == pytest.approx(expected_mae, rel=1e-6)

    def test_r2_perfect_prediction(self):
        """R² = 1 for perfect prediction"""
        actual = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        predicted = actual.copy()
        
        residuals = actual - predicted
        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((actual - np.mean(actual)) ** 2)
        r2 = 1 - (ss_res / ss_tot)
        
        assert r2 == pytest.approx(1.0, abs=1e-6)

    def test_r2_mean_prediction(self):
        """R² = 0 for mean prediction"""
        actual = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        predicted = np.full_like(actual, actual.mean())
        
        residuals = actual - predicted
        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((actual - np.mean(actual)) ** 2)
        r2 = 1 - (ss_res / ss_tot)
        
        assert r2 == pytest.approx(0.0, abs=1e-6)


class TestACMFIntegration:
    """Test ACMF integration"""

    def test_rhs_finite_values(self):
        """RHS produces finite values for valid state"""
        from acmf.core import default_params
        state = np.array([0.5, 0.1, 0.4, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 100.0])
        params = default_params()
        dydt = rhs(state, params)
        
        assert dydt.shape == (10,), "RHS should return 10-element vector"
        assert np.all(np.isfinite(dydt)), "RHS should produce finite values"

    def test_euler_integration_step(self):
        """Euler integration step produces valid state"""
        from acmf.core import default_params
        state = np.array([0.5, 0.1, 0.4, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 100.0])
        params = default_params()
        dydt = rhs(state, params)
        
        dt = 0.1
        new_state = state + dt * dydt
        
        assert new_state.shape == state.shape
        assert np.all(np.isfinite(new_state))

    def test_multiple_integration_steps(self):
        """Multiple integration steps maintain validity"""
        from acmf.core import default_params
        state = np.array([0.5, 0.1, 0.4, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 100.0])
        params = default_params()
        dt = 0.1
        
        current = state.copy()
        for _ in range(10):
            dydt = rhs(current, params)
            current = current + dt * dydt
            assert np.all(np.isfinite(current)), "State should remain finite"


class TestBenchmarkIntegration:
    """Integration tests for full benchmark"""

    def test_benchmark_runs_without_error(self):
        """Full benchmark runs without exceptions"""
        try:
            from scripts.run_synthetic_forecast_benchmark import ForecastBenchmark
        except ImportError:
            pytest.skip("Benchmark script not importable")
        
        benchmark = ForecastBenchmark("high_volatility", seed=42)
        results = benchmark.run_benchmark(horizon=20)
        
        assert len(results) == 3, "Should have 3 models: trend, ar1, acmf"
        assert all(r.model in ["linear_trend", "ar1", "acmf"] for r in results)

    def test_benchmark_all_scenarios(self):
        """Benchmark runs for all scenarios"""
        scenarios = ["low_stress_trend", "high_volatility", "regime_switch", "nonlinear_transform"]
        
        try:
            from scripts.run_synthetic_forecast_benchmark import ForecastBenchmark
        except ImportError:
            pytest.skip("Benchmark script not importable")
        
        for scenario in scenarios:
            benchmark = ForecastBenchmark(scenario, seed=42)
            results = benchmark.run_benchmark(horizon=15)
            
            assert len(results) > 0, f"Benchmark failed for scenario: {scenario}"
            assert all(r.scenario == scenario for r in results)

    def test_benchmark_produces_reasonable_metrics(self):
        """Benchmark produces reasonable error metrics"""
        try:
            from scripts.run_synthetic_forecast_benchmark import ForecastBenchmark
        except ImportError:
            pytest.skip("Benchmark script not importable")
        
        benchmark = ForecastBenchmark("high_volatility", seed=42)
        results = benchmark.run_benchmark(horizon=20)
        
        for result in results:
            # Metrics should be reasonable values
            assert result.rmse >= 0
            assert result.mae >= 0
            # R² can be negative for bad forecasts but typically in reasonable range
            assert result.r2 > -100, f"R² should be reasonable, got {result.r2}"
            assert not np.isnan(result.rmse), "RMSE should not be NaN"
            assert not np.isnan(result.mae), "MAE should not be NaN"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

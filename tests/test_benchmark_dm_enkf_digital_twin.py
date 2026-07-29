import numpy as np

from acmf import (
    ACMFEnKF, DigitalTwin, arima_110_fit, arima_110_forecast,
    compare_acmf_vs_benchmarks, default_params, dm_test,
    fit_all_benchmarks, forecast_all_benchmarks, linear_trend_fit,
    linear_trend_forecast, random_walk_forecast, simulate, var1_fit,
    var1_forecast,
)


def test_benchmark_models_shapes_and_basic_behavior():
    t = np.arange(10, dtype=float)
    y = 2.0 + 0.5 * t
    assert np.allclose(random_walk_forecast(y, 3), y[-1])
    a, b = linear_trend_fit(y, t)
    assert abs(a - 2.0) < 1e-10
    assert abs(b - 0.5) < 1e-10
    assert linear_trend_forecast(a, b, np.array([10.0])).shape == (1,)
    c, phi, sigma2 = arima_110_fit(y, t)
    assert np.isfinite(c) and np.isfinite(phi) and sigma2 >= 0.0
    assert arima_110_forecast(y, c, phi, 4).shape == (4,)


def test_var_and_all_benchmarks_forecast():
    t = np.arange(12, dtype=float)
    data = {
        "P": 100.0 + t,
        "A": 0.2 + 0.01 * t,
        "Prod": 0.4 + 0.02 * t,
    }
    var_params = var1_fit(data, t)
    var_forecast = var1_forecast(data, var_params, 5)
    assert set(var_forecast) == set(data)
    assert all(v.shape == (5,) for v in var_forecast.values())
    fitted = fit_all_benchmarks(data, t)
    forecasts = forecast_all_benchmarks(data, t, np.arange(12, 15), fitted)
    assert "RandomWalk" in forecasts
    assert "ARIMA(1,1,0)" in forecasts
    assert all(len(v) == 3 for v in forecasts.values())


def test_diebold_mariano_prefers_better_forecast():
    actual = np.arange(20, dtype=float)
    f_good = actual + 0.01
    f_bad = actual + 2.0
    result = dm_test(actual, f_good, f_bad)
    assert result["loss_diff_mean"] < 0.0
    assert result["better_model"] in {"Model1", "No significant difference"}
    comparison = compare_acmf_vs_benchmarks(actual, f_good, {"bad": f_bad})
    assert "bad" in comparison


def test_enkf_and_digital_twin_smoke():
    p = default_params()
    x0 = np.array([0.3, 0.4, 0.5, 0.5, 0.5, 0.3, 0.6, 0.5, 2.0, 500.0])
    enkf = ACMFEnKF(params=p, ensemble_size=12, obs_noise_std=0.01, process_noise_std=0.001, seed=123)
    enkf.initialize(x0)
    enkf.forecast_step()
    obs = np.array([500.0, 0.4, 0.3, 0.6, 2.0])
    enkf.analysis_step(obs)
    assert enkf.state_estimate().shape == (10,)
    assert "Ch" in enkf.latent_estimate()

    twin = DigitalTwin(params=p, enkf_ensemble_size=12, dt_enkf=1.0, seed=123)
    twin.assimilate(2000.0, obs, x0=x0)
    report = twin.get_state_report()
    assert report["time"] == 2000.0
    t, traj = twin.forecast(2, dt=1.0)
    assert traj.shape[1] == 10
    scenario = twin.scenario_forecast(2, {"NaturalDecay": 0.01}, dt=1.0)
    assert scenario["trajectory"].shape[1] == 10

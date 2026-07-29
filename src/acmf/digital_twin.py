"""ACMF Phase III Digital Twin engine."""
from __future__ import annotations
from typing import Dict, Tuple
import numpy as np
from .core import ACMFParams, default_params
from .enkf import ACMFEnKF
from .solver import scenario_run, simulate


class DigitalTwin:
    """Digital twin wrapper around ACMF EnKF and scenario forecasts."""

    STATE_NAMES = ["A", "Prod", "Ch", "M", "G", "V", "Inst", "R", "F", "P"]

    def __init__(self, params: ACMFParams | None = None, enkf_ensemble_size: int = 50,
                 dt_enkf: float = 1.0, seed: int | None = None):
        self.params = params or default_params()
        self.enkf = ACMFEnKF(params=self.params, ensemble_size=enkf_ensemble_size, dt=dt_enkf, seed=seed)
        self.history: list[np.ndarray] = []
        self.latent_history: list[Dict] = []
        self.time_history: list[float] = []

    def assimilate(self, t: float, y_obs: np.ndarray, x0: np.ndarray | None = None):
        """Assimilate one observation vector [P, Prod, A, Inst, F]."""
        if self.enkf.ensemble is None:
            if x0 is None:
                x0 = np.array([0.3, 0.4, 0.5, 0.5, 0.5, 0.3, 0.6, 0.5, 2.0, 500.0])
            self.enkf.initialize(x0)
        self.enkf.forecast_step()
        self.enkf.analysis_step(y_obs)
        est = self.enkf.state_estimate()
        latent = self.enkf.latent_estimate()
        self.history.append(est.copy())
        self.latent_history.append(latent)
        self.time_history.append(float(t))

    def forecast(self, n_years: int, dt: float = 0.5) -> Tuple[np.ndarray, np.ndarray]:
        current = self.enkf.state_estimate()
        t0 = self.time_history[-1] if self.time_history else 0.0
        return simulate(current, (t0, t0 + n_years), dt, self.params)

    def scenario_forecast(self, n_years: int, param_overrides: dict, dt: float = 0.5):
        current = self.enkf.state_estimate()
        return scenario_run("DigitalTwin_Scenario", x0=current, t_span=(0, n_years), dt=dt, **param_overrides)

    def get_state_report(self) -> Dict:
        est = self.enkf.state_estimate()
        std = self.enkf.state_std()
        return {
            "time": self.time_history[-1] if self.time_history else None,
            "state": {name: {"mean": float(est[i]), "std": float(std[i])} for i, name in enumerate(self.STATE_NAMES)},
            "latent": self.enkf.latent_estimate(),
        }

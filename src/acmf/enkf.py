"""ACMF Phase III Ensemble Kalman Filter."""
from __future__ import annotations
from typing import Dict
import numpy as np
from .core import ACMFParams, default_params, rhs
from .solver import project_state


class ACMFEnKF:
    """Ensemble Kalman Filter for ACMF latent-state tracking."""

    OBS_IDX = [9, 1, 0, 6, 8]      # P, Prod, A, Inst, F
    LATENT_IDX = [2, 3, 4, 5, 7]   # Ch, M, G, V, R
    STATE_DIM = 10

    def __init__(self, params: ACMFParams | None = None, ensemble_size: int = 50,
                 process_noise_std: float = 0.01, obs_noise_std: float = 0.02,
                 dt: float = 1.0, seed: int | None = None):
        if ensemble_size < 2:
            raise ValueError("ensemble_size must be at least 2")
        self.params = params or default_params()
        self.N = int(ensemble_size)
        self.Q = np.eye(self.STATE_DIM) * float(process_noise_std) ** 2
        self.R_obs = np.eye(len(self.OBS_IDX)) * float(obs_noise_std) ** 2
        self.dt = float(dt)
        self.rng = np.random.default_rng(seed)
        self.ensemble: np.ndarray | None = None

    def initialize(self, x0: np.ndarray, spread: float = 0.05):
        x0 = project_state(np.asarray(x0, dtype=float))
        noise = self.rng.normal(0.0, spread, size=(self.N, self.STATE_DIM))
        self.ensemble = np.array([project_state(member) for member in np.tile(x0, (self.N, 1)) + noise])

    def _require_ensemble(self):
        if self.ensemble is None:
            raise RuntimeError("EnKF ensemble is not initialized")

    def _rk4(self, x):
        k1 = rhs(x, self.params)
        k2 = rhs(x + 0.5 * self.dt * k1, self.params)
        k3 = rhs(x + 0.5 * self.dt * k2, self.params)
        k4 = rhs(x + self.dt * k3, self.params)
        return x + (self.dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)

    def forecast_step(self):
        """Forecast each ensemble member one step forward."""
        self._require_ensemble()
        new_ensemble = np.zeros_like(self.ensemble)
        for i in range(self.N):
            x = self._rk4(self.ensemble[i])
            x += self.rng.multivariate_normal(np.zeros(self.STATE_DIM), self.Q)
            new_ensemble[i] = project_state(x)
        self.ensemble = new_ensemble

    def analysis_step(self, y_obs: np.ndarray):
        """Assimilate [P, Prod, A, Inst, F] observations."""
        self._require_ensemble()
        y_obs = np.asarray(y_obs, dtype=float)
        if y_obs.shape != (len(self.OBS_IDX),):
            raise ValueError(f"y_obs must have shape ({len(self.OBS_IDX)},)")
        x_mean = np.mean(self.ensemble, axis=0)
        X_pert = self.ensemble - x_mean
        Y_pert = X_pert[:, self.OBS_IDX]
        P_xy = X_pert.T @ Y_pert / (self.N - 1)
        P_yy = Y_pert.T @ Y_pert / (self.N - 1) + self.R_obs
        K = P_xy @ np.linalg.pinv(P_yy)
        obs_noise = self.rng.multivariate_normal(np.zeros(len(self.OBS_IDX)), self.R_obs, size=self.N)
        for i in range(self.N):
            innovation = y_obs + obs_noise[i] - self.ensemble[i, self.OBS_IDX]
            self.ensemble[i] = project_state(self.ensemble[i] + K @ innovation)

    def state_estimate(self) -> np.ndarray:
        self._require_ensemble()
        return np.mean(self.ensemble, axis=0)

    def state_std(self) -> np.ndarray:
        self._require_ensemble()
        return np.std(self.ensemble, axis=0)

    def latent_estimate(self) -> Dict[str, dict]:
        mean = self.state_estimate()
        std = self.state_std()
        names = ["Ch", "M", "G", "V", "R"]
        return {name: {"mean": float(mean[idx]), "std": float(std[idx])} for name, idx in zip(names, self.LATENT_IDX)}

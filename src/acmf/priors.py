from __future__ import annotations
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class LogNormalPrior:
    """Positive prior: theta = exp(mu + sigma*z)."""
    mu: float
    sigma: float

    def transform(self, z: float) -> float:
        return math.exp(self.mu + self.sigma * z)


@dataclass(frozen=True)
class UnitIntervalPrior:
    """Unit interval prior: theta = sigmoid(mu + sigma*z)."""
    mu: float
    sigma: float

    def transform(self, z: float) -> float:
        x = self.mu + self.sigma * z
        if x >= 0:
            return 1.0 / (1.0 + math.exp(-x))
        ex = math.exp(x)
        return ex / (1.0 + ex)


@dataclass(frozen=True)
class BoundedPrior:
    """Bounded prior on [lower, upper]."""
    lower: float
    upper: float
    mu: float
    sigma: float

    def transform(self, z: float) -> float:
        if self.upper <= self.lower:
            raise ValueError("upper must be greater than lower")
        s = UnitIntervalPrior(self.mu, self.sigma).transform(z)
        return self.lower + (self.upper - self.lower) * s

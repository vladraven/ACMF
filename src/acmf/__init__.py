"""ACMF 3.3.1.2 package."""

from .smoothing import smax, smin, sigmoid
from .core import default_params, algebraic_layer, rhs
from .adaptive_dynamics import adaptive_dynamics_layer

__version__ = "3.3.1.2"

__all__ = [
    "smax",
    "smin",
    "sigmoid",
    "default_params",
    "algebraic_layer",
    "rhs",
    "adaptive_dynamics_layer",
]

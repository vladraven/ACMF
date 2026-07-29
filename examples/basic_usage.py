import numpy as np
from acmf import default_params, rhs, adaptive_dynamics_layer

params = default_params()
x = np.array([0.4, 0.5, 0.5, 0.5, 0.5, 0.3, 0.6, 0.5, 2.0, 500.0])

print("dx/dt:")
print(rhs(x, params))

print("adaptive dynamics:")
print(adaptive_dynamics_layer(x, params))


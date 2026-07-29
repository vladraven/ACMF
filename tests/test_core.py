import numpy as np
from acmf import default_params, algebraic_layer, rhs


def test_rhs_shape_and_finite():
    x = np.array([0.4, 0.5, 0.5, 0.5, 0.5, 0.3, 0.6, 0.5, 2.0, 500.0])
    dx = rhs(x, default_params())
    assert dx.shape == (10,)
    assert np.all(np.isfinite(dx))


def test_boundary_invariance_indices():
    p = default_params()
    base = np.array([0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 2.0, 500.0])
    for i in range(8):
        x = base.copy(); x[i] = 0.0
        assert rhs(x, p)[i] >= -1e-8
        x = base.copy(); x[i] = 1.0
        assert rhs(x, p)[i] <= 1e-8


def test_algebraic_layer_keys():
    x = np.array([0.4, 0.5, 0.5, 0.5, 0.5, 0.3, 0.6, 0.5, 2.0, 500.0])
    a = algebraic_layer(x)
    for k in ["Innovation", "S", "Gap", "K_pop", "BirthRate", "DeathRate"]:
        assert k in a


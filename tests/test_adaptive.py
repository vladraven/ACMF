import numpy as np
from acmf import adaptive_dynamics_layer, default_params


def test_adaptive_layer_outputs_are_finite_and_bounded_core_probs():
    x = np.array([0.4, 0.5, 0.5, 0.5, 0.5, 0.3, 0.6, 0.5, 2.0, 500.0])
    out = adaptive_dynamics_layer(x, default_params())
    for value in out.values():
        assert np.isfinite(value)
    assert 0.0 <= out["criticality"] <= 1.0
    assert 0.0 <= out["phase_transition_probability"] <= 1.0
    assert out["adaptive_capacity"] >= 0.0

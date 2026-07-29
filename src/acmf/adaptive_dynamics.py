from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from .smoothing import smax, smin, sigmoid, EPSILON
from .core import rhs, algebraic_layer, default_params, ACMFParams


@dataclass
class AdaptiveWeights:
    a_demographic: float = 0.25
    a_institutional: float = 0.25
    a_cultural: float = 0.25
    a_infrastructure: float = 0.25
    b_dA: float = 0.25
    b_dProd: float = 0.25
    b_innovation: float = 0.25
    b_automation_profit: float = 0.25
    c_M: float = 0.25
    c_R: float = 0.25
    c_Inst: float = 0.25
    c_Ch: float = 0.25
    w_V: float = 0.15
    w_S: float = 0.15
    w_mismatch: float = 0.25
    w_structural: float = 0.10
    w_corruption: float = 0.10
    w_EI: float = 0.10
    w_R: float = 0.05
    w_Inst: float = 0.05
    w_adaptive: float = 0.05
    k0: float = -2.0
    k_crit: float = 3.0
    k_dcrit: float = 1.0
    k_mismatch: float = 1.0
    k_V: float = 1.0
    k_R: float = 1.0
    k_Inst: float = 1.0


def adaptive_dynamics_layer(x, params: ACMFParams | None = None, weights: AdaptiveWeights | None = None, dx=None, previous_criticality=None):
    p = params or default_params()
    w = weights or AdaptiveWeights()
    dx = rhs(x, p) if dx is None else np.asarray(dx, dtype=float)
    a = algebraic_layer(x, p)
    A, Prod, Ch, M, G, V, Inst, R, F, P = np.asarray(x, dtype=float)

    demographic_inertia = smin(1.0, smax(0.0, P / smax(a["K_pop"], EPSILON)))
    institutional_inertia = smin(1.0, smax(0.0, Inst * (1.0 - p.NaturalDecay)))
    cultural_persistence = smin(1.0, smax(0.0, a["Cult"]))
    infrastructure_inertia = smin(1.0, smax(0.0, 1.0 - a["StructuralDecay"]))

    inertial_potential = (
        w.a_demographic * demographic_inertia
        + w.a_institutional * institutional_inertia
        + w.a_cultural * cultural_persistence
        + w.a_infrastructure * infrastructure_inertia
    )

    transformational_potential = (
        w.b_dA * abs(dx[0])
        + w.b_dProd * abs(dx[1])
        + w.b_innovation * a["Innovation"]
        + w.b_automation_profit * a["AutomationProfit"]
    )

    adaptive_capacity = w.c_M * M + w.c_R * R + w.c_Inst * Inst + w.c_Ch * Ch
    time_scale_mismatch = transformational_potential / smax(adaptive_capacity, EPSILON)
    structural_bounded = smin(1.0, smax(0.0, a["StructuralLimits"]))
    ei_bounded = smin(1.0, smax(0.0, a["EI"]))

    criticality_raw = (
        w.w_V * V
        + w.w_S * a["S"]
        + w.w_mismatch * time_scale_mismatch
        + w.w_structural * structural_bounded
        + w.w_corruption * a["Corruption"]
        + w.w_EI * ei_bounded
        - w.w_R * R
        - w.w_Inst * Inst
        - w.w_adaptive * adaptive_capacity
    )
    criticality = smin(1.0, smax(0.0, criticality_raw))
    dcriticality = 0.0 if previous_criticality is None else criticality - previous_criticality
    phase_transition_probability = sigmoid(
        w.k0
        + w.k_crit * criticality
        + w.k_dcrit * dcriticality
        + w.k_mismatch * time_scale_mismatch
        + w.k_V * V
        - w.k_R * R
        - w.k_Inst * Inst
    )

    return {
        "demographic_inertia": float(demographic_inertia),
        "institutional_inertia": float(institutional_inertia),
        "cultural_persistence": float(cultural_persistence),
        "infrastructure_inertia": float(infrastructure_inertia),
        "inertial_potential": float(inertial_potential),
        "transformational_potential": float(transformational_potential),
        "adaptive_capacity": float(adaptive_capacity),
        "time_scale_mismatch": float(time_scale_mismatch),
        "criticality_raw": float(criticality_raw),
        "criticality": float(criticality),
        "dcriticality": float(dcriticality),
        "phase_transition_probability": float(phase_transition_probability),
    }


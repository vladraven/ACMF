from __future__ import annotations
from dataclasses import dataclass, asdict
import numpy as np
from .smoothing import smax, smin, sigmoid, EPSILON

STATE_NAMES = ["A", "Prod", "Ch", "M", "G", "V", "Inst", "R", "F", "P"]


@dataclass
class ACMFParams:
    alpha1: float = 0.4
    alpha2: float = 0.3
    alpha3: float = 0.2
    alpha4: float = 0.25
    alpha5: float = 0.2
    alpha6: float = 0.25
    alpha7: float = 0.3
    alpha8: float = 0.25
    alpha9: float = 0.2
    alpha10: float = 0.2
    alpha11: float = 0.2
    alpha12: float = 0.2
    alpha13: float = 0.2
    alpha14: float = 0.2
    alpha15: float = 0.2
    alpha16: float = 0.2
    alpha17: float = 0.2
    alpha18: float = 0.2
    alpha19: float = 0.45
    alpha20: float = 0.2
    alpha_pos: float = 0.25
    gamma_inst: float = 0.3
    alpha_rec: float = 0.25
    alpha_fert: float = 0.25
    alpha_fert_env: float = 0.25
    beta1: float = 0.2
    beta2: float = 0.2
    beta3: float = 0.2
    beta4: float = 0.2
    beta5: float = 0.2
    beta6: float = 0.2
    beta7: float = 0.2
    beta8: float = 0.2
    beta9: float = 0.2
    beta10: float = 0.2
    beta11: float = 0.2
    beta12: float = 0.2
    NaturalDecay: float = 0.04
    beta_neg: float = 0.2
    beta_rec_stress: float = 0.2
    beta_fert_stress: float = 0.2
    beta_fert_inc: float = 0.2
    q1: float = 0.15
    q2: float = 0.6
    q3: float = 0.3
    s1: float = 4.0
    s2: float = 1.0
    we1: float = 0.55
    we2: float = 0.45
    wr1: float = 0.34
    wr2: float = 0.33
    wr3: float = 0.33
    g_sc: float = 0.2
    cu1: float = 0.34
    cu2: float = 0.33
    cu3: float = 0.33
    cu4: float = 0.2
    cu5: float = 0.2
    cu6: float = 0.2
    c1: float = 0.5
    c2: float = 0.5
    w1: float = 0.2
    w2: float = 0.2
    w3: float = 0.2
    w4: float = 0.2
    w5: float = 0.2
    e1: float = 0.6
    e2: float = 0.6
    e3: float = 0.6
    g_innov: float = 2.0
    g_ch: float = 2.0
    A_max: float = 1.0
    l1: float = 0.8
    l2: float = 0.8
    u_c: float = 0.5
    c_v: float = 0.5
    c_r: float = 0.5
    sd_a: float = 0.5
    p1: float = 0.4
    p2: float = 0.4
    p3: float = 0.4
    K_min: float = 0.2
    K0: float = 1000.0
    k1: float = 1 / 3
    k2: float = 1 / 3
    k3: float = 1 / 3
    b0: float = 0.01
    b1: float = 0.04
    d0: float = 0.005
    d1: float = 0.02
    d2: float = 0.02
    M_max: float = 50.0
    k_mig: float = 0.01
    P_target: float = 500.0
    K_g: float = 0.4
    n: float = 2.0
    H: float = 0.5
    Sec: float = 0.5
    Com: float = 0.5
    FP: float = 0.5
    Inc: float = 0.5
    Inf: float = 0.5
    HC: float = 0.5
    LTG: float = 0.5
    IG: float = 0.5
    U_corr: float = 0.5

    def to_dict(self):
        return asdict(self)


def default_params(**overrides) -> ACMFParams:
    p = ACMFParams()
    for k, v in overrides.items():
        setattr(p, k, v)
    return p


def unpack_state(x):
    x = np.asarray(x, dtype=float)
    if x.shape[-1] != 10:
        raise ValueError("ACMF state must have length 10")
    return x


def algebraic_layer(x, params: ACMFParams | None = None):
    p = params or default_params()
    A, Prod, Ch, M, G, V, Inst, R, F, P = unpack_state(x)
    P_safe = smax(P, EPSILON)
    L_s = 0.6 * P_safe
    L_d = P * smax(0.0, p.q1 + p.q2 * Prod - p.q3 * A)
    Emp = smin(L_s, L_d)
    Unemployment = smax(0.0, 1.0 - Emp / smax(L_s, EPSILON))
    S = sigmoid(p.s1 * Unemployment + p.s2 * p.Inf)
    Education = smin(1.0, smax(0.0, p.we1 * Inst + p.we2 * R))
    RecoveryDriver = smin(1.0, smax(0.0, p.wr1 * Inst + p.wr2 * Education + p.wr3 * p.Com))
    SocialCapital = smax(0.0, Inst * R * (1.0 + p.g_sc * M))
    Cult_raw = (p.cu1 * SocialCapital + p.cu2 * Education + p.cu3 * p.LTG) * np.exp(-(p.cu4 * p.IG + p.cu5 * V + p.cu6 * S))
    Cult = smin(1.0, smax(0.0, Cult_raw))
    C = smin(1.0, smax(0.0, p.c1 * Education + p.c2 * Cult))
    Gap = sigmoid(C - Ch)
    Env_raw = p.w1 * p.H + p.w2 * p.Sec + p.w3 * p.HC + p.w4 * Inst + p.w5 * p.FP
    Env = smin(1.0, smax(0.0, Env_raw))

    EI_raw = p.e1 * p.Inf + p.e2 * (1.0 - p.Inc) + p.e3 * Unemployment
    EI = smin(1.0, smax(0.0, EI_raw))

    Innovation_raw = Inst * smax(0.0, 1.0 - A) * (1.0 + p.g_innov * G) * (1.0 + p.g_ch * Ch)
    Innovation = smin(1.0, smax(0.0, Innovation_raw))
    RoutineAuto = A * Prod
    Aging = smax(0.0, 1.0 - F / 4.0)
    Comp = smax(0.0, 1.0 - Inst)
    HCE = M * (1.0 - S)
    LabourScarcity = smax(0.0, (L_d - L_s) / smax(L_d + L_s, EPSILON))
    AutomationProfit = 1.0 - np.exp(-(p.p1 * LabourScarcity + p.p2 * Prod + p.p3 * Innovation * HCE))
    TechSaturation = A / smax(p.A_max, EPSILON)
    StructuralLimits_raw = p.l1 * (1.0 - Inst) + p.l2 * p.Inf
    StructuralLimits = smin(1.0, smax(0.0, StructuralLimits_raw))
    Corruption = smin(1.0, smax(0.0, (1.0 - Inst) * (1.0 - p.u_c * p.U_corr) * (1.0 + p.c_v * V - p.c_r * R)))
    StructuralDecay = smin(1.0, smax(0.0, (1.0 - Inst * R) * (1.0 + p.sd_a * RoutineAuto)))
    K_pop = smax(p.K_min, p.K0 * (p.k1 * Prod + p.k2 * HCE + p.k3 * Inst))
    Hill = G ** p.n / (smax(p.K_g, EPSILON) ** p.n + G ** p.n)
    BirthRate = smax(0.5 * np.sqrt(EPSILON), p.b0 + p.b1 * (F / 4.0))
    DeathRate = smax(0.0, p.d0 + p.d1 * Aging + p.d2 * (1.0 - HCE))
    Migration = p.M_max * sigmoid(p.k_mig * (p.P_target - P))
    return locals()


def rhs(x, params: ACMFParams | None = None):
    p = params or default_params()
    A, Prod, Ch, M, G, V, Inst, R, F, P = unpack_state(x)
    a = algebraic_layer(x, p)
    dx = np.zeros(10, dtype=float)
    dx[0] = (p.alpha1 * a["Innovation"] + p.alpha2 * a["LabourScarcity"] + p.alpha3 * a["AutomationProfit"]) * (1 - A) - p.beta1 * A * (0.5 + 0.5 * Inst)
    dx[1] = (p.alpha4 * A + p.alpha5 * a["Innovation"] * a["HCE"] + p.alpha6 * Inst) * (1 - Prod) - (p.beta2 * a["TechSaturation"] + p.beta3 * a["StructuralLimits"]) * Prod
    dx[2] = (p.alpha7 * a["Innovation"] * a["Hill"] + p.alpha8 * a["Comp"] + p.alpha9 * R + p.alpha10 * a["Education"]) * (1 - Ch) - (p.beta4 * a["RoutineAuto"] + p.beta5 * a["S"]) * Ch
    dx[3] = (p.alpha11 * Ch + p.alpha12 * G + p.alpha13 * R + p.alpha14 * Inst) * (1 - M) - (p.beta6 * V + p.beta7 * a["S"]) * M
    dx[4] = (p.alpha15 * M + p.alpha16 * Ch + p.alpha17 * p.LTG + p.alpha18 * a["Education"]) * (1 - G) - (p.beta8 * V + p.beta9 * p.IG + p.beta10 * a["S"]) * G
    dx[5] = (p.alpha19 * a["Gap"] + p.alpha20 * a["S"]) * (1 - V) - (p.beta11 * M + p.beta12 * R) * V
    dx[6] = p.alpha_pos * (R * a["SocialCapital"] + p.gamma_inst * M * G) * (1 - Inst) - (p.NaturalDecay + p.beta_neg * (a["Corruption"] * V + a["StructuralDecay"])) * Inst
    dx[7] = p.alpha_rec * a["RecoveryDriver"] * (1 - R) - p.beta_rec_stress * (V + a["S"]) * R
    dx[8] = (p.alpha_fert * M * G + p.alpha_fert_env * a["Env"]) * (4 - F) - (p.beta_fert_stress * a["S"] + p.beta_fert_inc * a["EI"]) * F
    dx[9] = (a["BirthRate"] * (1 - P / a["K_pop"]) - a["DeathRate"]) * P + a["Migration"]
    return dx


from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ModelLevel:
    name: str
    observed_vars: tuple[str, ...]
    state_count: int
    description: str

MODEL_LEVELS: dict[str, ModelLevel] = {
    'R3': ModelLevel('R3', ('P', 'Prod', 'Inst'), 3, 'Reduced macro core: population, production, institutions.'),
    'R5': ModelLevel('R5', ('P', 'Prod', 'A', 'Inst', 'F'), 5, 'Reduced core used for stable local empirical validation.'),
    'R7': ModelLevel('R7', ('P', 'Prod', 'A', 'Inst', 'F', 'M', 'R'), 7, 'Reduced core plus economic pressure/resilience.'),
    'FULL10': ModelLevel('FULL10', ('P', 'Prod', 'A', 'Inst', 'F', 'Ch', 'M', 'G', 'V', 'R'), 10, 'Full observation set; use only after identifiability checks.'),
}

def available_model_levels() -> list[str]:
    return list(MODEL_LEVELS)

def get_model_level(name: str | None = None) -> ModelLevel:
    key = (name or 'R5').upper()
    if key not in MODEL_LEVELS:
        raise ValueError(f'Unknown model level {name!r}. Available: {available_model_levels()}')
    return MODEL_LEVELS[key]

def observed_vars_for_level(name: str | None = None) -> list[str]:
    return list(get_model_level(name).observed_vars)

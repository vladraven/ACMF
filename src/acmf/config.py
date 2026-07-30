from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import yaml

@dataclass(frozen=True)
class CalibrationProfile:
    profile: str
    max_nfev: int
    seeds: tuple[int, ...]
    purpose: str = ''
    notes: str = ''

@dataclass(frozen=True)
class ParameterConfig:
    profile: str
    parameters: dict
    bounds: dict
    source: str = ''

ROOT = Path(__file__).resolve().parents[2]
CONFIG_ROOT = ROOT / 'configs'

def _load_yaml(path: str | Path) -> dict:
    p=Path(path)
    if not p.exists():
        raise FileNotFoundError(f'Configuration file not found: {p}')
    data=yaml.safe_load(p.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError(f'Configuration must be a mapping: {p}')
    return data

def load_calibration_profile(name: str='smoke') -> CalibrationProfile:
    data=_load_yaml(CONFIG_ROOT / 'calibration' / f'{name}.yaml')
    max_nfev=int(data['max_nfev'])
    if name != 'smoke' and max_nfev < 100:
        raise ValueError(f'research calibration profile must have max_nfev >= 100, got {max_nfev}')
    return CalibrationProfile(profile=data['profile'], max_nfev=max_nfev, seeds=tuple(int(x) for x in data.get('seeds', [])), purpose=data.get('purpose',''), notes=data.get('notes',''))

def load_parameter_config(name: str='baseline') -> ParameterConfig:
    data=_load_yaml(CONFIG_ROOT / 'params' / f'{name}.yaml')
    params=data.get('parameters', {})
    bounds=data.get('bounds', {})
    for key, value in params.items():
        if key not in bounds:
            raise ValueError(f'Missing bounds for parameter {key}')
        lo, hi = bounds[key]
        if not (float(lo) <= float(value) <= float(hi)):
            raise ValueError(f'Parameter {key}={value} outside [{lo}, {hi}]')
    return ParameterConfig(profile=data.get('profile',name), parameters=params, bounds=bounds, source=data.get('source',''))

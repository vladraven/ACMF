from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Sequence
import json
import numpy as np
import pandas as pd

from .world_panel import load_world_panel, make_acmf_proxy_panel
from .data_fetchers.world_bank import complete_data_year

SCALE_ORDER = ['world', 'country', 'province', 'city', 'district']
STATE_VARS = ['P', 'Prod', 'A', 'Inst', 'F', 'Ch', 'M', 'G', 'V', 'R']
DEFAULT_AGGREGATION = {
    'P': 'sum',
    'Prod': 'weighted_mean',
    'A': 'weighted_mean',
    'Inst': 'weighted_mean',
    'F': 'weighted_mean',
    'Ch': 'weighted_mean',
    'M': 'weighted_mean',
    'G': 'weighted_mean',
    'V': 'weighted_mean',
    'R': 'weighted_mean',
}


@dataclass
class ScaleNode:
    node_id: str
    name: str
    level: str
    parent_id: str | None = None
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        if self.level not in SCALE_ORDER:
            raise ValueError(f'Unknown scale level: {self.level}')


@dataclass
class ScaleEdge:
    source_id: str
    target_id: str
    relation: str = 'contains'
    weight: float = 1.0
    metadata: Dict = field(default_factory=dict)


@dataclass
class MultiScaleFrame:
    nodes: pd.DataFrame
    edges: pd.DataFrame
    observations: pd.DataFrame
    aggregation_rules: Dict[str, str] = field(default_factory=lambda: DEFAULT_AGGREGATION.copy())

    def validate(self) -> Dict:
        required_node_cols = {'node_id', 'name', 'level', 'parent_id'}
        required_obs_cols = {'node_id', 'Year'}
        missing_node_cols = sorted(required_node_cols - set(self.nodes.columns))
        missing_obs_cols = sorted(required_obs_cols - set(self.observations.columns))
        node_ids = set(self.nodes['node_id']) if 'node_id' in self.nodes else set()
        obs_node_ids = set(self.observations['node_id']) if 'node_id' in self.observations else set()
        edge_sources = set(self.edges['source_id']) if len(self.edges) and 'source_id' in self.edges else set()
        edge_targets = set(self.edges['target_id']) if len(self.edges) and 'target_id' in self.edges else set()
        orphan_obs = sorted(obs_node_ids - node_ids)
        orphan_edges = sorted((edge_sources | edge_targets) - node_ids)
        bad_levels = sorted(set(self.nodes['level']) - set(SCALE_ORDER)) if 'level' in self.nodes else []
        return {
            'ok': not (missing_node_cols or missing_obs_cols or orphan_obs or orphan_edges or bad_levels),
            'missing_node_cols': missing_node_cols,
            'missing_obs_cols': missing_obs_cols,
            'orphan_observation_nodes': orphan_obs,
            'orphan_edge_nodes': orphan_edges,
            'bad_levels': bad_levels,
            'n_nodes': int(len(self.nodes)),
            'n_edges': int(len(self.edges)),
            'n_observations': int(len(self.observations)),
        }

    def children_of(self, node_id: str) -> List[str]:
        if self.edges.empty:
            return []
        mask = (self.edges['source_id'] == node_id) & (self.edges.get('relation', 'contains') == 'contains')
        return self.edges.loc[mask, 'target_id'].tolist()

    def ancestors_of(self, node_id: str) -> List[str]:
        out = []
        current = node_id
        parent_map = dict(zip(self.nodes['node_id'], self.nodes['parent_id']))
        while parent_map.get(current):
            current = parent_map[current]
            out.append(current)
        return out

    def observations_for(self, node_id: str) -> pd.DataFrame:
        return self.observations[self.observations['node_id'] == node_id].copy()

    def to_dict(self) -> Dict:
        return {
            'nodes': self.nodes.to_dict(orient='records'),
            'edges': self.edges.to_dict(orient='records'),
            'observations': self.observations.to_dict(orient='records'),
            'aggregation_rules': self.aggregation_rules,
        }

    @classmethod
    def from_dict(cls, payload: Dict) -> 'MultiScaleFrame':
        return cls(
            nodes=pd.DataFrame(payload.get('nodes', [])),
            edges=pd.DataFrame(payload.get('edges', [])),
            observations=pd.DataFrame(payload.get('observations', [])),
            aggregation_rules=payload.get('aggregation_rules', DEFAULT_AGGREGATION.copy()),
        )


def _node_id(level: str, name: str) -> str:
    safe = ''.join(ch.lower() if ch.isalnum() else '_' for ch in name).strip('_')
    safe = '_'.join(part for part in safe.split('_') if part)
    return f'{level}:{safe}'


def build_country_multiscale_frame(
    countries: Sequence[str],
    data_path: str | Path | None = None,
    start_year: int = 1995,
    end_year: int | None = None,
    include_world: bool = True,
) -> MultiScaleFrame:
    """Build a world->country multiscale frame from bundled world-panel proxy data."""
    end_year = int(end_year if end_year is not None else complete_data_year())
    panel = load_world_panel(data_path)
    nodes = []
    edges = []
    observations = []
    root_id = 'world:world'
    if include_world:
        nodes.append({'node_id': root_id, 'name': 'World', 'level': 'world', 'parent_id': None})
    for country in countries:
        cid = _node_id('country', country)
        nodes.append({'node_id': cid, 'name': country, 'level': 'country', 'parent_id': root_id if include_world else None})
        if include_world:
            edges.append({'source_id': root_id, 'target_id': cid, 'relation': 'contains', 'weight': 1.0})
        data = make_acmf_proxy_panel(panel, country, start_year=start_year, end_year=end_year)
        rows = []
        for i, year in enumerate(data['t'].astype(int)):
            row = {'node_id': cid, 'Year': int(year)}
            for var in STATE_VARS:
                row[var] = float(data[var][i]) if var in data else np.nan
            rows.append(row)
        observations.extend(rows)
    frame = MultiScaleFrame(pd.DataFrame(nodes), pd.DataFrame(edges), pd.DataFrame(observations))
    if include_world:
        world_obs = aggregate_children(frame, root_id)
        frame.observations = pd.concat([frame.observations, world_obs], ignore_index=True)
    return frame


def aggregate_children(frame: MultiScaleFrame, parent_id: str, years: Sequence[int] | None = None) -> pd.DataFrame:
    """Aggregate direct children observations into parent observations."""
    child_ids = frame.children_of(parent_id)
    if not child_ids:
        return pd.DataFrame(columns=['node_id', 'Year'] + STATE_VARS)
    obs = frame.observations[frame.observations['node_id'].isin(child_ids)].copy()
    if years is not None:
        obs = obs[obs['Year'].isin(list(years))]
    if obs.empty:
        return pd.DataFrame(columns=['node_id', 'Year'] + STATE_VARS)
    rows = []
    for year, g in obs.groupby('Year'):
        row = {'node_id': parent_id, 'Year': int(year)}
        weights = g['P'].replace(0, np.nan) if 'P' in g else pd.Series(np.nan, index=g.index)
        for var in STATE_VARS:
            rule = frame.aggregation_rules.get(var, 'weighted_mean')
            vals = pd.to_numeric(g[var], errors='coerce') if var in g else pd.Series(np.nan, index=g.index)
            if rule == 'sum':
                row[var] = float(vals.sum(skipna=True))
            elif rule == 'mean':
                row[var] = float(vals.mean(skipna=True))
            else:
                valid = vals.notna() & weights.notna()
                if valid.any() and float(weights[valid].sum()) > 0:
                    row[var] = float(np.average(vals[valid], weights=weights[valid]))
                else:
                    row[var] = float(vals.mean(skipna=True)) if vals.notna().any() else np.nan
        rows.append(row)
    return pd.DataFrame(rows).sort_values('Year').reset_index(drop=True)


def disaggregate_parent_to_children(
    frame: MultiScaleFrame,
    parent_id: str,
    variable: str,
    year: int,
    method: str = 'population_share',
) -> pd.DataFrame:
    """Allocate one parent variable value to direct children using population or equal shares."""
    if variable not in STATE_VARS:
        raise ValueError(f'Unknown ACMF state variable: {variable}')
    child_ids = frame.children_of(parent_id)
    parent = frame.observations[(frame.observations['node_id'] == parent_id) & (frame.observations['Year'] == int(year))]
    if parent.empty:
        raise ValueError(f'No parent observation for {parent_id} @ {year}')
    value = float(parent.iloc[0][variable])
    child_obs = frame.observations[(frame.observations['node_id'].isin(child_ids)) & (frame.observations['Year'] == int(year))].copy()
    if child_obs.empty:
        return pd.DataFrame(columns=['node_id', 'Year', variable, 'share', 'allocated_value'])
    if method == 'population_share' and 'P' in child_obs:
        weights = pd.to_numeric(child_obs['P'], errors='coerce').fillna(0.0)
        if float(weights.sum()) <= 0:
            weights = pd.Series(np.ones(len(child_obs)), index=child_obs.index)
    else:
        weights = pd.Series(np.ones(len(child_obs)), index=child_obs.index)
    shares = weights / float(weights.sum())
    child_obs['share'] = shares.values
    child_obs['allocated_value'] = value * child_obs['share']
    return child_obs[['node_id', 'Year', variable, 'share', 'allocated_value']].reset_index(drop=True)


def compare_scales(frame: MultiScaleFrame, variable: str, year: int) -> pd.DataFrame:
    """Return cross-scale values for one variable/year."""
    if variable not in STATE_VARS:
        raise ValueError(f'Unknown ACMF state variable: {variable}')
    cols = ['node_id', 'Year', variable]
    values = frame.observations.loc[frame.observations['Year'] == int(year), cols].merge(frame.nodes, on='node_id', how='left')
    return values[['node_id', 'name', 'level', 'Year', variable]].sort_values(['level', 'name']).reset_index(drop=True)


def save_multiscale_frame(frame: MultiScaleFrame, output: str | Path) -> Path:
    p = Path(output)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(frame.to_dict(), indent=2), encoding='utf-8')
    return p


def load_multiscale_frame(path: str | Path) -> MultiScaleFrame:
    return MultiScaleFrame.from_dict(json.loads(Path(path).read_text(encoding='utf-8')))

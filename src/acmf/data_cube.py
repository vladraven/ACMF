from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import shutil
import pandas as pd
import yaml

from . import __version__
from .panel_builder import build_panel_dataset, load_metadata, get_indicator_df, parse_year_range
from .data_fetchers.world_bank import complete_data_year
from .data_quality import indicator_quality_report, coverage_matrix, validate_cube_schema
from .provenance import make_provenance_record, append_provenance_record

CUBE_DIRS = [
    'raw/world_bank', 'raw/wgi', 'raw/oecd', 'raw/un', 'raw/unesco', 'raw/innovation',
    'raw/world_values_survey', 'raw/resilience', 'processed/minimal', 'processed/standard',
    'processed/research', 'metadata'
]

DEFAULT_SOURCES = {
    'sources': [
        {'id': 'world_bank', 'name': 'World Bank Open Data', 'type': 'api', 'backend': ['requests', 'wbdata'], 'url': 'https://api.worldbank.org/v2/'},
        {'id': 'wgi', 'name': 'Worldwide Governance Indicators', 'type': 'manual_or_wbdata', 'url': 'https://info.worldbank.org/governance/wgi/'},
        {'id': 'wipo_gii', 'name': 'WIPO Global Innovation Index', 'type': 'manual', 'url': 'https://www.wipo.int/global_innovation_index/'},
        {'id': 'wvs', 'name': 'World Values Survey', 'type': 'manual', 'url': 'https://www.worldvaluessurvey.org/WVSDocumentation.jsp'},
        {'id': 'vdem', 'name': 'V-Dem Dataset', 'type': 'manual', 'url': 'https://v-dem.net/data/the-v-dem-dataset/'},
        {'id': 'inform', 'name': 'INFORM Risk Index', 'type': 'manual', 'url': 'https://drmkc.jrc.ec.europa.eu/inform-index/'}
    ]
}


@dataclass
class DataCubeBuildResult:
    root: Path
    complete_data_year: int
    panels: dict
    quality_reports: dict
    validation: dict


def init_data_cube(root: str | Path = 'ACMF_DATA', metadata_source: str | Path = 'data/metadata/indicators.yaml') -> Path:
    root = Path(root)
    for d in CUBE_DIRS:
        (root / d).mkdir(parents=True, exist_ok=True)
    metadata_source = Path(metadata_source)
    if metadata_source.exists():
        shutil.copy2(metadata_source, root / 'metadata' / 'indicators.yaml')
    sources_path = root / 'metadata' / 'sources.yaml'
    if not sources_path.exists():
        sources_path.write_text(yaml.safe_dump(DEFAULT_SOURCES, sort_keys=False, allow_unicode=True), encoding='utf-8')
    prov_path = root / 'metadata' / 'provenance.yaml'
    if not prov_path.exists():
        prov_path.write_text(yaml.safe_dump({'records': []}, sort_keys=False), encoding='utf-8')
    return root


def build_data_cube(root: str | Path = 'ACMF_DATA', years: str | tuple[int, int | None] | None = None,
                    base_data_path: str | Path = 'data/world_data_level1_1995_2025.csv',
                    budgets=('minimal', 'standard', 'research'), current_year: int | None = None) -> DataCubeBuildResult:
    root = init_data_cube(root)
    start, end = parse_year_range(years or '1995:auto', current_year=current_year)
    meta_path = root / 'metadata' / 'indicators.yaml'
    metadata = load_metadata(meta_path)
    ind_df = get_indicator_df(metadata)
    panels, reports = {}, {}
    budget_map = {'research': 'comprehensive'}
    for budget in budgets:
        b = budget_map.get(budget, budget)
        out = root / 'processed' / budget / 'panel_dataset.csv'
        qout = root / 'processed' / budget / 'quality_report.csv'
        result = build_panel_dataset(budget=b, years=(start, end), metadata_path=meta_path, base_data_path=base_data_path, output=out, quality_output=qout)
        quality = indicator_quality_report(result.panel, result.selected_indicators)
        quality.to_csv(root / 'processed' / budget / 'indicator_quality.csv', index=False)
        coverage_matrix(result.panel).to_csv(root / 'processed' / budget / 'coverage_by_country.csv', index=False)
        panels[budget] = str(out)
        reports[budget] = str(qout)
        rec = make_provenance_record(
            dataset_id=f'{budget}_panel', version=__version__, source='world_bank_level1_plus_metadata',
            source_path=base_data_path, output_path=out, complete_data_year=end,
            notes=f'Built ACMF {budget} panel for {start}:{end}; complete year rule current_year_minus_2.'
        )
        append_provenance_record(root / 'metadata' / 'provenance.yaml', rec)
    validation = validate_cube_schema(root)
    return DataCubeBuildResult(root=root, complete_data_year=end, panels=panels, quality_reports=reports, validation=validation)


def load_data_cube(root: str | Path = 'ACMF_DATA', tier: str = 'standard') -> pd.DataFrame:
    return pd.read_csv(Path(root) / 'processed' / tier / 'panel_dataset.csv')

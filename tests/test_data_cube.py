from pathlib import Path
import yaml
from acmf import __version__
from acmf.data_cube import init_data_cube, build_data_cube, load_data_cube
from acmf.data_quality import validate_cube_schema, coverage_matrix
from acmf.provenance import load_provenance


def test_version_incremented_to_datacube():
    assert __version__ == '3.3.1.6-clean-real-identifiability'


def test_init_data_cube_schema(tmp_path):
    root = init_data_cube(tmp_path / 'ACMF_DATA', metadata_source=Path('data/metadata/indicators.yaml'))
    validation = validate_cube_schema(root)
    assert validation['ok']
    assert (root / 'metadata' / 'sources.yaml').exists()
    assert (root / 'metadata' / 'provenance.yaml').exists()


def test_build_data_cube_minimal_tier(tmp_path):
    root = tmp_path / 'ACMF_DATA'
    result = build_data_cube(root=root, years=(1995, 2024), base_data_path=Path('data/world_data_level1_1995_2025.csv'), budgets=('minimal',), current_year=2026)
    assert result.validation['ok']
    assert result.complete_data_year == 2024
    panel_path = root / 'processed' / 'minimal' / 'panel_dataset.csv'
    assert panel_path.exists()
    panel = load_data_cube(root, 'minimal')
    assert len(panel) == 31 * 30
    assert panel['Year'].max() == 2024
    cov = coverage_matrix(panel)
    assert 'country_name' in cov.columns
    prov = load_provenance(root / 'metadata' / 'provenance.yaml')
    assert len(prov['records']) >= 1
    assert prov['records'][0]['complete_data_year'] == 2024

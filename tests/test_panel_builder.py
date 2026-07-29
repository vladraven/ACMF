from pathlib import Path
import pandas as pd
from acmf.panel_builder import parse_year_range, load_metadata, get_indicator_df, select_indicators, build_panel_dataset
from acmf.data_fetchers.world_bank import complete_data_year


def test_complete_data_year_rule_current_year_minus_two():
    assert complete_data_year(current_year=2026) == 2024
    assert parse_year_range('1995:auto', current_year=2026) == (1995, 2024)
    assert parse_year_range('1995:complete', current_year=2026) == (1995, 2024)


def test_metadata_yaml_loads_and_scores():
    meta = load_metadata(Path('data/metadata/indicators.yaml'))
    df = get_indicator_df(meta)
    assert len(df) >= 40
    assert 'oed_score' in df.columns
    assert df['oed_score'].notna().all()
    assert {'POP','BIRTH','GDPC'}.issubset(set(df['id']))


def test_select_indicators_and_build_minimal_panel(tmp_path):
    meta = load_metadata(Path('data/metadata/indicators.yaml'))
    ind = get_indicator_df(meta)
    selected = select_indicators(ind, meta, budget='minimal')
    assert len(selected) > 0
    out = tmp_path / 'panel.csv'
    qout = tmp_path / 'quality.csv'
    result = build_panel_dataset(budget='minimal', years='1995:2024', output=out, quality_output=qout, metadata_path=Path('data/metadata/indicators.yaml'), base_data_path=Path('data/world_data_level1_1995_2025.csv'))
    assert out.exists() and qout.exists()
    assert len(result.panel) == 31 * 30
    assert result.panel['Year'].max() == 2024
    assert 'Population' in result.panel.columns


def test_builder_construct_filter(tmp_path):
    out = tmp_path / 'panel.csv'
    result = build_panel_dataset(budget='standard', years=(1995, 2024), constructs=['Ch','M','Y'], output=out, quality_output=tmp_path/'quality.csv', metadata_path=Path('data/metadata/indicators.yaml'), base_data_path=Path('data/world_data_level1_1995_2025.csv'))
    assert out.exists()
    assert len(result.selected_indicators) > 0
    assert set(['country_name','country_code','Year']).issubset(result.panel.columns)

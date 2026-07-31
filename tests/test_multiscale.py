from pathlib import Path
from acmf import __version__
from acmf.multiscale import (
    build_country_multiscale_frame,
    aggregate_children,
    disaggregate_parent_to_children,
    compare_scales,
    save_multiscale_frame,
    load_multiscale_frame,
)


def test_version_incremented_to_multiscale():
    assert __version__ == '3.3.1.10-clean-empirical-validation'


def test_build_country_multiscale_frame_validates():
    frame = build_country_multiscale_frame(['Canada','Germany'], start_year=2018, end_year=2020)
    validation = frame.validate()
    assert validation['ok']
    assert validation['n_nodes'] == 3
    assert validation['n_edges'] == 2
    assert 'world:world' in set(frame.nodes['node_id'])
    assert set(frame.nodes['level']) == {'world','country'}


def test_aggregate_and_disaggregate_population():
    frame = build_country_multiscale_frame(['Canada','Germany'], start_year=2020, end_year=2020)
    world = frame.observations[(frame.observations['node_id'] == 'world:world') & (frame.observations['Year'] == 2020)]
    countries = frame.observations[(frame.observations['node_id'] != 'world:world') & (frame.observations['Year'] == 2020)]
    assert abs(float(world.iloc[0]['P']) - float(countries['P'].sum())) < 1e-6
    alloc = disaggregate_parent_to_children(frame, 'world:world', 'P', 2020)
    assert len(alloc) == 2
    assert abs(float(alloc['allocated_value'].sum()) - float(world.iloc[0]['P'])) < 1e-6


def test_compare_save_load(tmp_path):
    frame = build_country_multiscale_frame(['Canada'], start_year=2020, end_year=2020)
    comparison = compare_scales(frame, 'P', 2020)
    assert set(comparison['level']) == {'world','country'}
    out = save_multiscale_frame(frame, tmp_path / 'frame.json')
    loaded = load_multiscale_frame(out)
    assert loaded.validate()['ok']
    assert len(loaded.nodes) == len(frame.nodes)

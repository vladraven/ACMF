from pathlib import Path
from acmf import __version__
from acmf.world_panel import load_world_panel
from acmf.real_identifiability import analyze_country_identifiability, build_real_identifiability_report, summarize_real_identifiability


def test_version_incremented_to_real_identifiability():
    assert __version__ == '3.3.1.7-clean-multiscale'


def test_analyze_country_identifiability_canada_short_window():
    panel = load_world_panel()
    report = analyze_country_identifiability(panel, 'Canada', start_year=1995, end_year=2002, design_k=1, target_rank=6, max_observables=6)
    assert report.country == 'Canada'
    assert report.rank >= 1
    assert len(report.greedy_design['selected_observables']) >= 5
    assert isinstance(report.weak_directions, list)


def test_build_real_identifiability_report_one_country():
    report = build_real_identifiability_report(countries=['Canada'], start_year=1995, end_year=2002, design_k=1, target_rank=6, max_observables=6)
    assert report['summary']['n_countries'] == 1
    assert report['reports'][0]['country'] == 'Canada'
    assert report['errors'] == []

import pandas as pd
from acmf.data_fetchers.world_bank import complete_data_year, fetch_world_bank_requests, fetch_world_bank


def test_complete_data_year():
    assert complete_data_year(2026) == 2024


def test_fetch_world_bank_dispatcher_uses_requests_backend(monkeypatch):
    import acmf.data_fetchers.world_bank as wb
    called = {}
    def fake_requests(**kwargs):
        called['backend'] = 'requests'
        return pd.DataFrame({'country_name':['Canada'], 'country_code':['CA'], 'Year':[2024], 'Population':[1]})
    monkeypatch.setattr(wb, 'fetch_world_bank_requests', fake_requests)
    df = wb.fetch_world_bank(years=(2024,2024), backend='requests')
    assert called['backend'] == 'requests'
    assert len(df) == 1


def test_fetch_world_bank_wbdata_missing_is_clean_error(monkeypatch):
    import acmf.data_fetchers.world_bank as wb
    def fake_import(name, *args, **kwargs):
        if name == 'wbdata':
            raise ImportError('no wbdata')
        return __import__(name, *args, **kwargs)
    monkeypatch.setattr('builtins.__import__', fake_import)
    try:
        wb.fetch_world_bank(years=(2024,2024), backend='wbdata')
    except RuntimeError as exc:
        assert 'wbdata' in str(exc)
    else:
        raise AssertionError('expected RuntimeError')

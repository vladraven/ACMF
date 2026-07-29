"""Data fetchers for ACMF panel construction.

The package exposes two World Bank download backends:
- requests backend: direct public World Bank REST API;
- wbdata backend: optional wrapper backend when wbdata is installed.
"""
from .world_bank import COUNTRIES, WB_INDICATORS, fetch_world_bank_requests, fetch_world_bank_wbdata, fetch_world_bank
from .wgi import fetch_wgi_manual, fetch_wgi_wbdata
from .innovation import fetch_gii_manual, fetch_unesco_rd_template
from .world_values import fetch_wvs_manual, fetch_ess_manual, aggregate_trust_by_country
from .resilience import fetch_vdem_manual, fetch_inform_manual

__all__ = [
    'COUNTRIES','WB_INDICATORS','fetch_world_bank_requests','fetch_world_bank_wbdata','fetch_world_bank',
    'fetch_wgi_manual','fetch_wgi_wbdata','fetch_gii_manual','fetch_unesco_rd_template',
    'fetch_wvs_manual','fetch_ess_manual','aggregate_trust_by_country','fetch_vdem_manual','fetch_inform_manual'
]

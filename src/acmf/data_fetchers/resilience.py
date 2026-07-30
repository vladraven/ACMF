from __future__ import annotations
from .manual_sources import fetch_local_table, require_manual_source
VDEM_URL='https://v-dem.net/data/the-v-dem-dataset/'
INFORM_URL='https://drmkc.jrc.ec.europa.eu/inform-index/'
def fetch_vdem_manual(filepath=None):
    if filepath is None: require_manual_source('V-Dem', VDEM_URL, 'data/raw/resilience')
    return fetch_local_table(filepath)
def fetch_inform_manual(filepath=None):
    if filepath is None: require_manual_source('INFORM Risk', INFORM_URL, 'data/raw/resilience')
    return fetch_local_table(filepath)

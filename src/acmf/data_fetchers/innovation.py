from __future__ import annotations
from .manual_sources import fetch_local_table, require_manual_source
GII_URL='https://www.wipo.int/global_innovation_index/'
UNESCO_RD_URL='https://api.uis.unesco.org/'
def fetch_gii_manual(filepath=None):
    if filepath is None: require_manual_source('WIPO Global Innovation Index', GII_URL, 'data/raw/innovation')
    return fetch_local_table(filepath)
def fetch_unesco_rd(filepath=None):
    if filepath is None: require_manual_source('UNESCO UIS R&D', UNESCO_RD_URL, 'data/raw/unesco')
    return fetch_local_table(filepath)

from __future__ import annotations
from .manual_sources import fetch_local_table, require_manual_source
WVS_URL='https://www.worldvaluessurvey.org/WVSDocumentation.jsp'
ESS_URL='https://www.europeansocialsurvey.org/data/download.html'
def fetch_wvs_manual(filepath=None):
    if filepath is None: require_manual_source('World Values Survey', WVS_URL, 'data/raw/world_values_survey')
    return fetch_local_table(filepath)
def fetch_ess_manual(filepath=None):
    if filepath is None: require_manual_source('European Social Survey', ESS_URL, 'data/raw/world_values_survey')
    return fetch_local_table(filepath)

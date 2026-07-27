from __future__ import annotations
from pathlib import Path
import pandas as pd
from .common import read_csv_rows, carry_forward, to_number, parse_period

COMPONENT_RENAME = {
    "Births 7": "births", "Deaths 8": "deaths", "Immigrants 9": "immigrants",
    "Emigrants 10 11 12": "emigrants", "Returning emigrants 11 12 13": "returning_emigrants",
    "Net temporary emigration 11 12 14": "net_temporary_emigration",
    "Net interprovincial migration 15": "net_interprovincial_migration",
    "Net intraprovincial migration 16": "net_intraprovincial_migration",
    "Net non-permanent residents 17 18 19": "net_non_permanent_residents",
    "Residual deviation 20": "residual_deviation",
}
PROVINCES = {"Newfoundland and Labrador", "Prince Edward Island", "Nova Scotia", "New Brunswick", "Quebec", "Ontario", "Manitoba", "Saskatchewan", "Alberta", "British Columbia", "Yukon", "Northwest Territories", "Nunavut", "Canada"}

def parse(path: str | Path) -> pd.DataFrame:
    rows = read_csv_rows(Path(path)); components = carry_forward(rows[8]); genders = rows[9]; age_groups = rows[10]; periods = rows[11]
    records=[]
    for row in rows[13:]:
        if not row or str(row[0]).startswith("Symbol legend"): break
        geo=row[0]
        if not geo: continue
        level = "country" if geo == "Canada" else ("province" if geo in PROVINCES else "economic_region")
        for j in range(1, min(len(row), len(components))):
            comp=COMPONENT_RENAME.get(components[j])
            if not comp: continue
            ys, ye = parse_period(periods[j])
            records.append({"geo":geo,"geography_level":level,"component":comp,"gender":genders[j],"age_group":age_groups[j],"period":periods[j],"start_year":ys,"end_year":ye,"value":to_number(row[j])})
    return pd.DataFrame(records)

def province_component_summary(df):
    return df[df.geography_level.eq("province")].groupby(["geo","component"], as_index=False)["value"].sum()

def province_vs_er_reconciliation(df):
    provinces=sorted(df[df.geography_level.eq("province")].geo.unique()); rows=[]
    for prov in provinces:
        prow=df[(df.geography_level=="province")&(df.geo==prov)].groupby("component")["value"].sum()
        er=df[(df.geography_level=="economic_region")&(df.geo.str.endswith(", "+prov, na=False))].groupby("component")["value"].sum()
        for c in sorted(set(prow.index)|set(er.index)):
            pv=float(prow.get(c,0.0)); ev=float(er.get(c,0.0)); rows.append({"province":prov,"component":c,"province_value":pv,"economic_region_sum":ev,"difference":pv-ev})
    return pd.DataFrame(rows)

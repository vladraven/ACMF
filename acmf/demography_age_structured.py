from __future__ import annotations
from dataclasses import dataclass
import pandas as pd

P1_AGES = {"-1 year", "0 to 4 years", "5 to 9 years", "10 to 14 years"}
P2_AGES = {"15 to 19 years", "20 to 24 years", "25 to 29 years", "30 to 34 years", "35 to 39 years", "40 to 44 years", "45 to 49 years", "50 to 54 years", "55 to 59 years", "60 to 64 years"}
P3_AGES = {"65 to 69 years", "70 to 74 years", "75 to 79 years", "80 to 84 years", "85 to 89 years", "90 to 94 years", "95 to 99 years", "100 years and older"}

@dataclass(frozen=True)
class DemographyConfig:
    validation_mode: str = "observed_components"
    scenario_mode: str = "endogenous_acmf_mechanisms"
    newborn_age_group: str = "-1 year"

def cohort_label(age_group: str) -> str | None:
    if age_group in P1_AGES: return "P1"
    if age_group in P2_AGES: return "P2"
    if age_group in P3_AGES: return "P3"
    return None

def aggregate_to_p123(pop_age_gender: pd.DataFrame) -> pd.DataFrame:
    required = {"geo", "year", "age_group", "population"}
    missing = required - set(pop_age_gender.columns)
    if missing: raise ValueError(f"missing required columns: {sorted(missing)}")
    df = pop_age_gender.copy()
    df["cohort"] = df["age_group"].map(cohort_label)
    df = df.dropna(subset=["cohort"])
    out = df.groupby(["geo", "year", "cohort"], as_index=False)["population"].sum()
    wide = out.pivot_table(index=["geo", "year"], columns="cohort", values="population", aggfunc="sum").reset_index()
    wide.columns.name = None
    for c in ["P1", "P2", "P3"]:
        if c not in wide: wide[c] = 0.0
    wide["P_tot"] = wide[["P1", "P2", "P3"]].sum(axis=1)
    return wide[["geo", "year", "P1", "P2", "P3", "P_tot"]]

def apply_observed_components(pop_start: pd.DataFrame, components: pd.DataFrame) -> pd.DataFrame:
    required_pop = {"geo", "year", "gender", "age_group", "population"}
    required_comp = {"geo", "gender", "age_group", "component", "value"}
    if required_pop - set(pop_start.columns): raise ValueError(f"pop_start missing {sorted(required_pop - set(pop_start.columns))}")
    if required_comp - set(components.columns): raise ValueError(f"components missing {sorted(required_comp - set(components.columns))}")
    signs = {
        "births": 1, "deaths": -1, "immigrants": 1, "emigrants": -1,
        "returning_emigrants": 1, "net_temporary_emigration": -1,
        "net_non_permanent_residents": 1, "net_interprovincial_migration": 1,
        "net_intraprovincial_migration": 1, "residual_deviation": 1,
        "in_migrants": 1, "out_migrants": -1,
    }
    comp = components.copy()
    comp["signed_value"] = comp["value"] * comp["component"].map(signs).fillna(1.0)
    delta = comp.groupby(["geo", "gender", "age_group"], as_index=False)["signed_value"].sum()
    out = pop_start.merge(delta, on=["geo", "gender", "age_group"], how="left")
    out["signed_value"] = out["signed_value"].fillna(0.0)
    out["population_next"] = out["population"] + out["signed_value"]
    return out

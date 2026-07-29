#!/usr/bin/env python3
"""
ACMF Panel Dataset Builder
==========================
Orchestrates multi-source data collection for ACMF (Agent-Capital-Model-Framework)
with Fisher Information-based Optimal Experimental Design.

Usage:
    python build_panel_dataset.py --budget comprehensive --years 1995:2024
    python build_panel_dataset.py --budget minimal --constructs Ch,M,Y
    python build_panel_dataset.py --list-indicators
    python build_panel_dataset.py --fisher-rank

Structure:
    data/
        raw/          — fetched but unprocessed data per source
        processed/    — merged, harmonized, imputed panel
        metadata/     — indicator definitions, OED parameters
    fetchers/         — one module per data source
"""

import argparse
import json
import os
import sys
import warnings
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

warnings.filterwarnings('ignore')

# =============================================================================
# PATHS
# =============================================================================

PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / 'data'
RAW_DIR = DATA_DIR / 'raw'
PROCESSED_DIR = DATA_DIR / 'processed'
METADATA_DIR = DATA_DIR / 'metadata'
FETCHERS_DIR = PROJECT_ROOT / 'fetchers'

sys.path.insert(0, str(FETCHERS_DIR))

# =============================================================================
# COUNTRY MAPPING
# =============================================================================

COUNTRIES = {
    # Anglo
    'Canada': 'CA', 'United States': 'US', 'Australia': 'AU', 'New Zealand': 'NZ',
    # Western Europe
    'Germany': 'DE', 'France': 'FR', 'Netherlands': 'NL', 'Sweden': 'SE', 'Norway': 'NO',
    # Southern Europe
    'Italy': 'IT', 'Spain': 'ES', 'Portugal': 'PT',
    # Eastern Europe
    'Poland': 'PL', 'Czechia': 'CZ', 'Romania': 'RO', 'Hungary': 'HU',
    # East Asia
    'Japan': 'JP', 'South Korea': 'KR', 'Taiwan': 'TWN', 'Singapore': 'SG',
    # China
    'China': 'CN',
    # South Asia
    'India': 'IN', 'Bangladesh': 'BD',
    # Latin America
    'Brazil': 'BR', 'Chile': 'CL', 'Mexico': 'MX',
    # Middle East
    'Israel': 'IL', 'United Arab Emirates': 'AE', 'Saudi Arabia': 'SA',
    # Africa
    'South Africa': 'ZA', 'Nigeria': 'NG', 'Kenya': 'KE'
}

COUNTRY_CODES_WB = {k: v for k, v in COUNTRIES.items() if k != 'Taiwan'}

# =============================================================================
# METADATA LOADER
# =============================================================================

def load_metadata():
    """Load indicator metadata from YAML."""
    meta_path = METADATA_DIR / 'indicators.yaml'
    with open(meta_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_indicator_df(metadata):
    """Convert indicator list to DataFrame for analysis."""
    rows = []
    for ind in metadata['indicators']:
        rows.append({
            'id': ind['id'],
            'name': ind['name'],
            'level': ind['level'],
            'construct': ind['construct'],
            'coverage': ind['coverage'],
            'cost': ind['cost'],
            'ovi': ind['ovi'],
            'source': ind['source'],
            'api_code': ind['api_code'],
            'frequency': ind['frequency'],
            'lag': ind['lag'],
            'quality': ind['quality'],
            'unit': ind.get('unit', ''),
        })
    return pd.DataFrame(rows)


# =============================================================================
# FISHER INFORMATION & OPTIMAL EXPERIMENTAL DESIGN
# =============================================================================

def compute_fisher_score(row):
    """
    Fisher Information proxy score for indicator selection.
    Higher = more information per unit cost.
    """
    # Expected information gain = OVI * coverage * quality
    # Normalized by cost
    info_gain = row['ovi'] * row['coverage'] * (row['quality'] / 5.0)
    return info_gain / row['cost']


def select_indicators(ind_df, budget, required_constructs=None, min_level1=True):
    """
    Greedy selection of indicators under budget constraint.
    Ensures coverage of all required constructs.
    """
    ind_df = ind_df.copy()
    ind_df['fisher_score'] = ind_df.apply(compute_fisher_score, axis=1)
    ind_df = ind_df.sort_values('fisher_score', ascending=False)

    selected = []
    total_cost = 0
    constructs_covered = set()
    required_constructs = required_constructs or ['Ch', 'M', 'G', 'V', 'R', 'Y', 'I']

    # Phase 1: Ensure at least one indicator per required construct
    for construct in required_constructs:
        candidates = ind_df[
            (ind_df['construct'] == construct) &
            (~ind_df['id'].isin([s['id'] for s in selected]))
        ]
        if len(candidates) == 0:
            print(f"  ⚠️  No indicator found for construct '{construct}'")
            continue
        best = candidates.iloc[0]
        if total_cost + best['cost'] <= budget:
            selected.append(best.to_dict())
            total_cost += best['cost']
            constructs_covered.add(construct)

    # Phase 2: Fill remaining budget by Fisher score
    for _, row in ind_df.iterrows():
        if row['id'] in [s['id'] for s in selected]:
            continue
        if total_cost + row['cost'] > budget:
            continue
        selected.append(row.to_dict())
        total_cost += row['cost']
        constructs_covered.add(row['construct'])

    return pd.DataFrame(selected), constructs_covered, total_cost


# =============================================================================
# DATA FETCHERS
# =============================================================================

def fetch_world_bank(indicators, years):
    """Fetch World Bank indicators via wbdata."""
    print("  [WB] Fetching World Bank Open Data...")
    try:
        import wbdata
    except ImportError:
        print("  [WB] ⚠️  wbdata not installed. Run: pip install wbdata")
        return pd.DataFrame()

    wb_codes = {ind['api_code']: ind['id'] for ind in indicators if ind['source'] == 'World Bank'}
    if not wb_codes:
        return pd.DataFrame()

    try:
        df = wbdata.get_dataframe(
            indicators=wb_codes,
            country=list(COUNTRY_CODES_WB.values()),
            data_date=f"{years[0]}-01-01",
            convert_date=False
        )
        df = df.reset_index()
        df = df.rename(columns={'country': 'country_name', 'date': 'Year'})
        df['Year'] = df['Year'].astype(int)
        df = df[df['Year'].between(years[0], years[1])]

        # Melt to long format
        df_long = df.melt(
            id_vars=['country_name', 'Year'],
            var_name='indicator_id',
            value_name='value'
        )
        df_long = df_long.dropna(subset=['value'])
        return df_long
    except Exception as e:
        print(f"  [WB] ⚠️  Error: {e}")
        return pd.DataFrame()


def fetch_wgi(years):
    """Fetch Worldwide Governance Indicators."""
    print("  [WGI] Fetching Worldwide Governance Indicators...")
    try:
        import wbdata
    except ImportError:
        print("  [WGI] ⚠️  wbdata not installed.")
        return pd.DataFrame()

    wgi_codes = {
        'GE.EST': 'GOVEFF',
        'RL.EST': 'RULELAW',
        'PV.EST': 'POLSTAB'
    }

    try:
        df = wbdata.get_dataframe(
            indicators=wgi_codes,
            country=list(COUNTRY_CODES_WB.values()),
            data_date=f"{years[0]}-01-01",
            convert_date=False
        )
        df = df.reset_index()
        df = df.rename(columns={'country': 'country_name', 'date': 'Year'})
        df['Year'] = df['Year'].astype(int)
        df = df[df['Year'].between(years[0], years[1])]

        df_long = df.melt(
            id_vars=['country_name', 'Year'],
            var_name='indicator_id',
            value_name='value'
        )
        df_long = df_long.dropna(subset=['value'])
        return df_long
    except Exception as e:
        print(f"  [WGI] ⚠️  Error: {e}")
        print("  [WGI] Manual download: https://info.worldbank.org/governance/wgi/")
        return pd.DataFrame()


def fetch_innovation_proxies(years):
    """
    Fetch innovation proxies: GII, high-tech exports, researchers, scientific papers.
    Sources: WIPO (GII), World Bank, UNESCO.
    """
    print("  [INNO] Fetching innovation proxies...")

    # World Bank available codes
    wb_innovation_codes = {
        'IP.PAT.RESD': 'PATENTS',
        'GB.XPD.RSDV.GD.ZS': 'RD_EXP',
        'TX.VAL.TECH.CD': 'HIGHTECH_X',
        'IP.JRN.ARTC.SC': 'SCI_PAPERS',
        'SP.POP.SCIE.RD.P6': 'RESEARCHERS',
    }

    try:
        import wbdata
        df = wbdata.get_dataframe(
            indicators=wb_innovation_codes,
            country=list(COUNTRY_CODES_WB.values()),
            data_date=f"{years[0]}-01-01",
            convert_date=False
        )
        df = df.reset_index()
        df = df.rename(columns={'country': 'country_name', 'date': 'Year'})
        df['Year'] = df['Year'].astype(int)
        df = df[df['Year'].between(years[0], years[1])]

        df_long = df.melt(
            id_vars=['country_name', 'Year'],
            var_name='indicator_id',
            value_name='value'
        )
        df_long = df_long.dropna(subset=['value'])

        # Note: GII, Knowledge Creation, Creative Outputs require WIPO API or CSV
        print("  [INNO] ⚠️  GII sub-indices require WIPO API key or manual CSV download")
        print("         https://www.wipo.int/global_innovation_index/")

        return df_long
    except Exception as e:
        print(f"  [INNO] ⚠️  Error: {e}")
        return pd.DataFrame()


def fetch_motivation_proxies(years):
    """Fetch motivation/engagement proxies: LFPR, youth unemployment, HDI, etc."""
    print("  [MOTI] Fetching motivation proxies...")

    wb_codes = {
        'SL.TLF.CACT.ZS': 'LFPR',
        'SL.UEM.1524.ZS': 'YOUTH_UNEMP',
        'SL.EMP.TOTL.SP.ZS': 'WORKING_AGE_EMP',
        'SL.EMP.SELF.ZS': 'SELF_EMP',
    }

    try:
        import wbdata
        df = wbdata.get_dataframe(
            indicators=wb_codes,
            country=list(COUNTRY_CODES_WB.values()),
            data_date=f"{years[0]}-01-01",
            convert_date=False
        )
        df = df.reset_index()
        df = df.rename(columns={'country': 'country_name', 'date': 'Year'})
        df['Year'] = df['Year'].astype(int)
        df = df[df['Year'].between(years[0], years[1])]

        df_long = df.melt(
            id_vars=['country_name', 'Year'],
            var_name='indicator_id',
            value_name='value'
        )
        df_long = df_long.dropna(subset=['value'])

        # HDI from UNDP requires separate API or CSV
        print("  [MOTI] ⚠️  HDI requires UNDP API or manual download")
        print("         https://hdr.undp.org/data-center")

        return df_long
    except Exception as e:
        print(f"  [MOTI] ⚠️  Error: {e}")
        return pd.DataFrame()


def fetch_agency_proxies(years):
    """Fetch agency/entrepreneurship proxies."""
    print("  [AGEN] Fetching agency proxies...")

    wb_codes = {
        'IC.BUS.NDNS.ZS': 'NEW_BUS',
        'IC.BUS.NREG': 'BUSINESS_FORMATIONS',
        'IC.BUS.EASE.XQ': 'EODB',
    }

    try:
        import wbdata
        df = wbdata.get_dataframe(
            indicators=wb_codes,
            country=list(COUNTRY_CODES_WB.values()),
            data_date=f"{years[0]}-01-01",
            convert_date=False
        )
        df = df.reset_index()
        df = df.rename(columns={'country': 'country_name', 'date': 'Year'})
        df['Year'] = df['Year'].astype(int)
        df = df[df['Year'].between(years[0], years[1])]

        df_long = df.melt(
            id_vars=['country_name', 'Year'],
            var_name='indicator_id',
            value_name='value'
        )
        df_long = df_long.dropna(subset=['value'])

        print("  [AGEN] ⚠️  VC investment requires PitchBook / EMPEA / OECD data")
        print("  [AGEN] ⚠️  Ease of Doing Business discontinued 2020; use B-READY after 2024")

        return df_long
    except Exception as e:
        print(f"  [AGEN] ⚠️  Error: {e}")
        return pd.DataFrame()


def fetch_values_proxies(years):
    """Fetch values/social cohesion proxies."""
    print("  [VALU] Fetching values proxies...")

    wb_codes = {
        'SI.POV.GINI': 'GINI',
    }

    try:
        import wbdata
        df = wbdata.get_dataframe(
            indicators=wb_codes,
            country=list(COUNTRY_CODES_WB.values()),
            data_date=f"{years[0]}-01-01",
            convert_date=False
        )
        df = df.reset_index()
        df = df.rename(columns={'country': 'country_name', 'date': 'Year'})
        df['Year'] = df['Year'].astype(int)
        df = df[df['Year'].between(years[0], years[1])]

        df_long = df.melt(
            id_vars=['country_name', 'Year'],
            var_name='indicator_id',
            value_name='value'
        )
        df_long = df_long.dropna(subset=['value'])

        print("  [VALU] ⚠️  World Values Survey data requires manual download")
        print("         https://www.worldvaluessurvey.org/WVSDocumentation.jsp")
        print("  [VALU] ⚠️  European Social Survey: https://www.europeansocialsurvey.org/")
        print("  [VALU] ⚠️  General Social Survey (US): https://gss.norc.org/")

        return df_long
    except Exception as e:
        print(f"  [VALU] ⚠️  Error: {e}")
        return pd.DataFrame()


def fetch_resilience_proxies(years):
    """Fetch resilience/institutional buffer proxies."""
    print("  [RESI] Fetching resilience proxies...")

    wb_codes = {
        'GC.NLD.TOTL.GD.ZS': 'FISCAL_BUFFER',
        'FI.RES.TOTL.CD': 'FOREX_RESERVES',
    }

    try:
        import wbdata
        df = wbdata.get_dataframe(
            indicators=wb_codes,
            country=list(COUNTRY_CODES_WB.values()),
            data_date=f"{years[0]}-01-01",
            convert_date=False
        )
        df = df.reset_index()
        df = df.rename(columns={'country': 'country_name', 'date': 'Year'})
        df['Year'] = df['Year'].astype(int)
        df = df[df['Year'].between(years[0], years[1])]

        df_long = df.melt(
            id_vars=['country_name', 'Year'],
            var_name='indicator_id',
            value_name='value'
        )
        df_long = df_long.dropna(subset=['value'])

        print("  [RESI] ⚠️  V-Dem institutional continuity: https://v-dem.net/")
        print("  [RESI] ⚠️  INFORM disaster risk: https://drmkc.jrc.ec.europa.eu/inform-index/")
        print("  [RESI] ⚠️  OECD resilience framework: https://www.oecd.org/governance/")

        return df_long
    except Exception as e:
        print(f"  [RESI] ⚠️  Error: {e}")
        return pd.DataFrame()


# =============================================================================
# PANEL ASSEMBLY
# =============================================================================

def build_panel(selected_indicators, years):
    """Fetch all selected indicators and merge into balanced panel."""
    print("\n📥 FETCHING DATA FROM ALL SOURCES\n")

    all_data = []

    # Group indicators by fetcher
    wb_indicators = [ind for ind in selected_indicators if ind['source'] == 'World Bank']
    wgi_indicators = [ind for ind in selected_indicators if 'WGI' in ind['source']]
    innovation_indicators = [ind for ind in selected_indicators if ind['construct'] == 'Ch' and ind['level'] == 3]
    motivation_indicators = [ind for ind in selected_indicators if ind['construct'] == 'M']
    agency_indicators = [ind for ind in selected_indicators if ind['construct'] == 'G']
    values_indicators = [ind for ind in selected_indicators if ind['construct'] == 'V']
    resilience_indicators = [ind for ind in selected_indicators if ind['construct'] == 'R']

    # Fetch by source
    if wb_indicators:
        df_wb = fetch_world_bank(wb_indicators, years)
        if len(df_wb) > 0:
            all_data.append(df_wb)
            print(f"      -> {len(df_wb)} rows")

    if wgi_indicators:
        df_wgi = fetch_wgi(years)
        if len(df_wgi) > 0:
            all_data.append(df_wgi)
            print(f"      -> {len(df_wgi)} rows")

    if innovation_indicators:
        df_inno = fetch_innovation_proxies(years)
        if len(df_inno) > 0:
            all_data.append(df_inno)
            print(f"      -> {len(df_inno)} rows")

    if motivation_indicators:
        df_moti = fetch_motivation_proxies(years)
        if len(df_moti) > 0:
            all_data.append(df_moti)
            print(f"      -> {len(df_moti)} rows")

    if agency_indicators:
        df_agen = fetch_agency_proxies(years)
        if len(df_agen) > 0:
            all_data.append(df_agen)
            print(f"      -> {len(df_agen)} rows")

    if values_indicators:
        df_valu = fetch_values_proxies(years)
        if len(df_valu) > 0:
            all_data.append(df_valu)
            print(f"      -> {len(df_valu)} rows")

    if resilience_indicators:
        df_resi = fetch_resilience_proxies(years)
        if len(df_resi) > 0:
            all_data.append(df_resi)
            print(f"      -> {len(df_resi)} rows")

    if not all_data:
        print("\n❌ No data fetched. Check API connectivity and dependencies.")
        return pd.DataFrame()

    # Combine
    combined = pd.concat(all_data, ignore_index=True)
    print(f"\n📊 Total raw observations: {len(combined):,}")

    # Pivot to wide format
    panel = combined.pivot_table(
        index=['country_name', 'Year'],
        columns='indicator_id',
        values='value',
        aggfunc='first'
    ).reset_index()

    # Add country codes
    code_map = {v: k for k, v in COUNTRIES.items()}
    panel['country_code'] = panel['country_name'].map({v: k for k, v in COUNTRIES.items()})

    # Reorder columns
    id_cols = ['country_name', 'country_code', 'Year']
    data_cols = [c for c in panel.columns if c not in id_cols]
    panel = panel[id_cols + sorted(data_cols)]

    return panel


def apply_interpolation(panel, metadata_df):
    """Interpolate missing values based on indicator frequency."""
    print("\n🔧 INTERPOLATING MISSING VALUES")

    for _, ind in metadata_df.iterrows():
        col = ind['id']
        if col not in panel.columns:
            continue

        freq = ind['frequency']
        if freq == 'Annual':
            panel[col] = panel.groupby('country_name')[col].transform(
                lambda x: x.interpolate(method='linear', limit=2)
            )
        elif freq in ('Biennial', 'Quinquennial'):
            panel[col] = panel.groupby('country_name')[col].transform(
                lambda x: x.interpolate(method='linear', limit_direction='both', limit=5)
            )

    return panel


def generate_quality_report(panel, metadata_df, output_path):
    """Generate data quality and Fisher information report."""
    print("\n📋 GENERATING QUALITY REPORT")

    report = []
    for _, ind in metadata_df.iterrows():
        col = ind['id']
        if col not in panel.columns:
            continue

        non_null = panel[col].notna().sum()
        total = len(panel)
        coverage = non_null / total

        report.append({
            'indicator_id': col,
            'indicator_name': ind['name'],
            'construct': ind['construct'],
            'level': ind['level'],
            'coverage_actual': round(coverage, 3),
            'coverage_expected': ind['coverage'],
            'non_null': non_null,
            'total': total,
            'cost': ind['cost'],
            'ovi': ind['ovi'],
            'fisher_score': round(compute_fisher_score(ind), 4),
            'source': ind['source'],
        })

    report_df = pd.DataFrame(report)
    report_df = report_df.sort_values('fisher_score', ascending=False)
    report_df.to_csv(output_path, index=False)
    print(f"   -> Saved to: {output_path}")
    return report_df


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='ACMF Panel Dataset Builder with Optimal Experimental Design'
    )
    parser.add_argument(
        '--budget', choices=['minimal', 'standard', 'comprehensive', 'unlimited'],
        default='standard',
        help='Budget scenario for indicator selection'
    )
    parser.add_argument(
        '--years', type=str, default='1995:2024',
        help='Year range as START:END'
    )
    parser.add_argument(
        '--constructs', type=str, default='',
        help='Comma-separated constructs to include (e.g., Ch,M,Y)'
    )
    parser.add_argument(
        '--list-indicators', action='store_true',
        help='List all indicators and exit'
    )
    parser.add_argument(
        '--fisher-rank', action='store_true',
        help='Rank indicators by Fisher score and exit'
    )
    parser.add_argument(
        '--output', type=str, default='panel_dataset.csv',
        help='Output filename'
    )

    args = parser.parse_args()

    # Parse years
    start_year, end_year = map(int, args.years.split(':'))
    years = (start_year, end_year)

    # Load metadata
    print("\n📖 Loading indicator metadata...")
    metadata = load_metadata()
    ind_df = get_indicator_df(metadata)
    print(f"   -> {len(ind_df)} indicators loaded")

    if args.list_indicators:
        print("\n" + "="*80)
        print("AVAILABLE INDICATORS")
        print("="*80)
        for _, row in ind_df.iterrows():
            print(f"  {row['id']:15s} | L{row['level']} | {row['construct']:3s} | "
                  f"{row['name']:40s} | {row['source']}")
        return

    if args.fisher_rank:
        ind_df['fisher_score'] = ind_df.apply(compute_fisher_score, axis=1)
        ind_df = ind_df.sort_values('fisher_score', ascending=False)
        print("\n" + "="*80)
        print("FISHER INFORMATION RANKING (Information per Unit Cost)")
        print("="*80)
        print(f"{'Rank':<6}{'ID':<15}{'Name':<40}{'Construct':<10}{'Score':>10}{'Cost':>6}")
        print("-"*80)
        for i, (_, row) in enumerate(ind_df.iterrows(), 1):
            print(f"{i:<6}{row['id']:<15}{row['name'][:38]:<40}"
                  f"{row['construct']:<10}{row['fisher_score']:>10.4f}{row['cost']:>6}")
        return

    # Budget
    budget_map = {
        'minimal': 20,
        'standard': 50,
        'comprehensive': 100,
        'unlimited': 999
    }
    budget = budget_map[args.budget]

    # Constructs
    required_constructs = None
    if args.constructs:
        required_constructs = [c.strip() for c in args.constructs.split(',')]

    # Select indicators
    print(f"\n🎯 BUDGET SCENARIO: {args.budget.upper()} (budget={budget})")
    selected, constructs_covered, total_cost = select_indicators(
        ind_df, budget, required_constructs
    )

    print(f"   -> Selected {len(selected)} indicators")
    print(f"   -> Constructs covered: {', '.join(sorted(constructs_covered))}")
    print(f"   -> Total cost: {total_cost}")
    print(f"   -> Remaining budget: {budget - total_cost}")

    print("\n📋 SELECTED INDICATORS:")
    for _, row in selected.iterrows():
        print(f"   [{row['construct']}] {row['id']:15s} — {row['name']:<45s} "
              f"(cost={row['cost']}, OVI={row['ovi']})")

    # Build panel
    panel = build_panel(selected.to_dict('records'), years)

    if len(panel) == 0:
        print("\n❌ Build failed. No data retrieved.")
        return

    # Interpolate
    panel = apply_interpolation(panel, selected)

    # Save
    output_path = PROCESSED_DIR / args.output
    panel.to_csv(output_path, index=False)
    print(f"\n✅ Panel dataset saved: {output_path}")
    print(f"   Shape: {panel.shape[0]} rows × {panel.shape[1]} columns")
    print(f"   Countries: {panel['country_name'].nunique()}")
    print(f"   Years: {panel['Year'].min()}-{panel['Year'].max()}")

    # Quality report
    report_path = PROCESSED_DIR / f"quality_report_{args.budget}.csv"
    report_df = generate_quality_report(panel, selected, report_path)

    print("\n" + "="*70)
    print("TOP 10 INDICATORS BY ACTUAL FISHER SCORE")
    print("="*70)
    print(report_df.head(10)[['indicator_id', 'construct', 'coverage_actual', 'fisher_score']].to_string(index=False))

    print("\n" + "="*70)
    print("NEXT STEPS")
    print("="*70)
    print("1. Review quality report for coverage gaps")
    print("2. For missing WGI data: download manually and place in data/raw/wgi/")
    print("3. For GII / innovation: use WIPO API or CSV export")
    print("4. For WVS / ESS: download survey microdata and aggregate")
    print("5. Run again with --budget comprehensive after manual data integration")
    print("="*70)


if __name__ == '__main__':
    main()

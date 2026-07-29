#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from acmf.panel_builder import load_metadata, get_indicator_df, select_indicators, build_panel_dataset, parse_year_range


def main():
    parser = argparse.ArgumentParser(description='ACMF panel dataset builder with OED priority scoring')
    parser.add_argument('--budget', choices=['minimal','standard','comprehensive','unlimited'], default='standard')
    parser.add_argument('--years', default='1995:auto', help='START:END, START:auto, or START:complete. auto = current year - 2')
    parser.add_argument('--constructs', default='', help='Comma-separated constructs, e.g. Ch,M,Y')
    parser.add_argument('--list-indicators', action='store_true')
    parser.add_argument('--fisher-rank', action='store_true', help='Rank indicators by OED/Fisher proxy score')
    parser.add_argument('--metadata', default=None)
    parser.add_argument('--base-data', default=None)
    parser.add_argument('--output', default='data/processed/panel_dataset.csv')
    parser.add_argument('--quality-output', default='data/processed/quality_report.csv')
    args = parser.parse_args()
    metadata = load_metadata(args.metadata)
    ind_df = get_indicator_df(metadata)
    if args.list_indicators:
        print(ind_df[['id','name','level','construct','source','api_code','cost','coverage','quality','oed_score']].to_string(index=False))
        return 0
    if args.fisher_rank:
        print(ind_df.sort_values('oed_score', ascending=False)[['id','name','level','construct','source','cost','coverage','quality','oed_score']].to_string(index=False))
        return 0
    constructs = [c.strip() for c in args.constructs.split(',') if c.strip()] or None
    result = build_panel_dataset(budget=args.budget, years=args.years, constructs=constructs, metadata_path=args.metadata, base_data_path=args.base_data, output=args.output, quality_output=args.quality_output)
    print(json.dumps({
        'output': str(result.output_path),
        'rows': int(len(result.panel)),
        'columns': int(len(result.panel.columns)),
        'selected_indicators': int(len(result.selected_indicators)),
        'years': list(parse_year_range(args.years)),
    }, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

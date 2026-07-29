#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from acmf.real_identifiability import DEFAULT_REAL_COUNTRIES, build_real_identifiability_report, save_real_identifiability_report
from acmf.data_fetchers.world_bank import complete_data_year


def main():
    parser = argparse.ArgumentParser(description='Run real-country practical identifiability diagnostics on ACMF world panel')
    parser.add_argument('--countries', nargs='*', default=DEFAULT_REAL_COUNTRIES)
    parser.add_argument('--data', default=None)
    parser.add_argument('--start-year', type=int, default=1995)
    parser.add_argument('--end-year', default='auto')
    parser.add_argument('--design-k', type=int, default=3)
    parser.add_argument('--target-rank', type=int, default=12)
    parser.add_argument('--max-observables', type=int, default=10)
    parser.add_argument('--output', default='output/real_identifiability_world_panel.json')
    args = parser.parse_args()
    end = complete_data_year() if str(args.end_year).lower() in {'auto','complete',''} else int(args.end_year)
    report = build_real_identifiability_report(
        countries=args.countries,
        data_path=args.data,
        start_year=args.start_year,
        end_year=end,
        design_k=args.design_k,
        target_rank=args.target_rank,
        max_observables=args.max_observables,
    )
    out = save_real_identifiability_report(report, args.output)
    compact = {
        'start_year': report['start_year'],
        'end_year': report['end_year'],
        'summary': report['summary'],
        'errors': report['errors'],
    }
    print(json.dumps(compact, indent=2))
    print(f'saved: {out}')
if __name__ == '__main__':
    main()

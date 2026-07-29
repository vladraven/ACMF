#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from acmf.observation_designer import design_for_world_panel_country, result_to_dict
from acmf.data_fetchers.world_bank import complete_data_year


def main():
    parser = argparse.ArgumentParser(description='Run ACMF observation designer on world-panel proxy data')
    parser.add_argument('--countries', nargs='*', default=['Canada','Germany','Japan','Korea, Rep.','Australia'])
    parser.add_argument('--data', default=None)
    parser.add_argument('--start-year', type=int, default=1995)
    parser.add_argument('--end-year', default='auto')
    parser.add_argument('--k', type=int, default=5)
    parser.add_argument('--output', default='output/observation_designer_world_panel.json')
    args = parser.parse_args()
    end = complete_data_year() if str(args.end_year).lower() in {'auto','complete',''} else int(args.end_year)
    results = {}
    for country in args.countries:
        try:
            res = design_for_world_panel_country(country, data_path=args.data, start_year=args.start_year, end_year=end, k=args.k)
            results[country] = result_to_dict(res)
        except Exception as exc:
            results[country] = {'error': str(exc)}
    out = {'start_year': args.start_year, 'end_year': end, 'k': args.k, 'results': results}
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(out, indent=2), encoding='utf-8')
    compact = {c: {'selected': r.get('selected_observables'), 'rank': r.get('final_rank'), 'condition_number': r.get('final_condition_number')} for c, r in results.items() if 'error' not in r}
    print(json.dumps(compact, indent=2))
    print(f'saved: {args.output}')
if __name__ == '__main__':
    main()

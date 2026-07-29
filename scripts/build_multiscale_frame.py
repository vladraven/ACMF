#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from acmf.multiscale import build_country_multiscale_frame, save_multiscale_frame, compare_scales
from acmf.data_fetchers.world_bank import complete_data_year


def main():
    parser = argparse.ArgumentParser(description='Build ACMF multiscale frame from country world-panel proxies')
    parser.add_argument('--countries', nargs='*', default=['Canada','Germany','Japan','Korea, Rep.','Australia'])
    parser.add_argument('--data', default=None)
    parser.add_argument('--start-year', type=int, default=1995)
    parser.add_argument('--end-year', default='auto')
    parser.add_argument('--output', default='output/multiscale_frame.json')
    parser.add_argument('--compare-variable', default='P')
    args = parser.parse_args()
    end = complete_data_year() if str(args.end_year).lower() in {'auto','complete',''} else int(args.end_year)
    frame = build_country_multiscale_frame(args.countries, data_path=args.data, start_year=args.start_year, end_year=end)
    validation = frame.validate()
    out = save_multiscale_frame(frame, args.output)
    comparison = compare_scales(frame, args.compare_variable, end).to_dict(orient='records')
    print(json.dumps({'output': str(out), 'validation': validation, 'comparison_year': end, 'comparison': comparison[:12]}, indent=2))
    return 0 if validation['ok'] else 2
if __name__ == '__main__':
    raise SystemExit(main())

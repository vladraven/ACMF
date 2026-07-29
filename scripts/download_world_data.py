#!/usr/bin/env python3
from __future__ import annotations
import argparse, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from acmf.data_fetchers.world_bank import fetch_world_bank, complete_data_year


def main():
    parser = argparse.ArgumentParser(description='Download World Bank indicators using requests or wbdata backend')
    parser.add_argument('--start-year', type=int, default=1995)
    parser.add_argument('--end-year', default='auto', help='Year or auto/complete; auto = current year - 2')
    parser.add_argument('--backend', choices=['requests','wbdata','auto'], default='requests')
    parser.add_argument('--output', default='data/world_data_level1_1995_2025.csv')
    parser.add_argument('--countries', nargs='*')
    parser.add_argument('--sleep', type=float, default=0.05)
    args = parser.parse_args()
    end = complete_data_year() if str(args.end_year).lower() in {'auto','complete',''} else int(args.end_year)
    df = fetch_world_bank(years=(args.start_year, end), backend=args.backend, countries=args.countries, sleep=args.sleep, save_path=args.output)
    print(f'saved: {args.output} rows={len(df)} cols={len(df.columns)} years={args.start_year}:{end} backend={args.backend}')
    return 0
if __name__ == '__main__':
    raise SystemExit(main())

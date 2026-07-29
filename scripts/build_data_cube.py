#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from acmf.data_cube import build_data_cube, init_data_cube


def main():
    parser = argparse.ArgumentParser(description='Build ACMF data cube tiers and provenance')
    parser.add_argument('--root', default='ACMF_DATA')
    parser.add_argument('--years', default='1995:auto')
    parser.add_argument('--base-data', default='data/world_data_level1_1995_2025.csv')
    parser.add_argument('--tiers', nargs='*', default=['minimal','standard','research'])
    parser.add_argument('--init-only', action='store_true')
    args = parser.parse_args()
    if args.init_only:
        root = init_data_cube(args.root)
        print(json.dumps({'root': str(root), 'initialized': True}, indent=2))
        return 0
    result = build_data_cube(root=args.root, years=args.years, base_data_path=args.base_data, budgets=args.tiers)
    print(json.dumps({'root': str(result.root), 'complete_data_year': result.complete_data_year, 'panels': result.panels, 'validation': result.validation}, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

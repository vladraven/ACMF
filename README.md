# ACMF 3.3.1.2 Clean Package

Clean, single-source ACMF package using a strict `src/` layout.

## What was removed

- root `acmf/` stub package;
- root `acmf_core.py` / `acmf_solver.py` legacy stubs;
- `index.php` repository bundler;
- generated stdout files and obsolete flat module duplicates;
- missing `v2_4_7` / `v2_4_8` task references.

## Canonical package

The only canonical Python package is:

```text
src/acmf/
```

## Quick start

```bash
python -m pip install -e .
python main.py --task health
python main.py --task empirical_canada
python main.py --task synthetic_ladder
python main.py --task world_profile
python main.py --task world_ident
```

## World panel data

The package includes `data/world_data_1995_2025.csv` and a World Bank downloader:

```bash
python scripts/download_world_data.py --start-year 1995 --end-year 2025 --output data/world_data_1995_2025.csv
```

## Tests

```bash
PYTHONPATH=src pytest -q
```

## Deployment

See `README_DEPLOY.md`.

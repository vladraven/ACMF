# ACMF Clean Datafetch Deployment

This package is a cleaned src-layout deployment bundle. The canonical implementation lives only in `src/acmf/`.

## Install

```bash
python -m pip install -e .
```

## Available tasks

```bash
python main.py --task health
python main.py --task empirical_canada
python main.py --task synthetic_ladder
python main.py --task world_profile
python main.py --task world_ident
python main.py --task data_list_indicators
python main.py --task data_fisher_rank
python main.py --task data_build_minimal
python main.py --task data_build_standard
python main.py --task datacube_init
python main.py --task datacube_build
python main.py --task v2_4_9
```

## Complete-year rule

Panel builds default to:

```text
complete_data_year = current_calendar_year - 2
```

For 2026, the complete-data default is 2024.

## Refresh World Bank data

Requests backend:

```bash
python scripts/download_world_data.py --backend requests --start-year 1995 --end-year auto --output data/world_data_level1_1995_2025.csv
```

wbdata backend:

```bash
python scripts/download_world_data.py --backend wbdata --start-year 1995 --end-year auto --output data/world_data_level1_1995_2025.csv
```

## API wrapper

```bash
export ACMF_API_TOKEN='change-me'
uvicorn app:app --host 0.0.0.0 --port 8000
```

Then call:

```bash
curl -X POST -H "Authorization: Bearer change-me" http://localhost:8000/run/health
```

## Security notes

- No `index.php` is shipped.
- No root-level `acmf/` stub is shipped.
- No `ACMF_PROJECT_BUNDLE.txt` dump is shipped.
- `/run/{task}` supports bearer-token protection through `ACMF_API_TOKEN`.

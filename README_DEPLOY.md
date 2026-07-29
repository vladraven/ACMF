# ACMF Clean Deployment

This package is a cleaned src-layout deployment bundle. The root-level stub package, PHP bundle helper, and obsolete generated text outputs have been removed. The canonical implementation lives only in `src/acmf/`.

## Install

```bash
python -m pip install -e .
```

## Health check

```bash
python main.py --task health
```

## Available tasks

```bash
python main.py --task empirical_canada
python main.py --task synthetic_ladder
python main.py --task world_profile
python main.py --task world_ident
python main.py --task v2_4_9
```

Removed historical tasks `v2_4_7` and `v2_4_8` from the entrypoint because their modules are not present in this bundle. Only physically present, tested tasks are exposed.

## World Bank data refresh

```bash
python scripts/download_world_data.py --start-year 1995 --end-year 2025 --output data/world_data_1995_2025.csv
```

## Optional API wrapper

```bash
export ACMF_API_TOKEN='change-me'
uvicorn app:app --host 0.0.0.0 --port 8000
```

Then call:

```bash
curl -X POST -H "Authorization: Bearer change-me" http://localhost:8000/run/health
```

If `ACMF_API_TOKEN` is unset, `/run/{task}` remains open for local development only.

## Security notes

- No `index.php` is shipped.
- No root-level `acmf/` stub package is shipped.
- No `ACMF_PROJECT_BUNDLE.txt` dump is shipped.
- `/run/{task}` supports bearer-token protection through `ACMF_API_TOKEN`.

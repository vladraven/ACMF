# ACMF 3.3.1.4 Clean Datacube Package

Clean, single-source ACMF package using a strict `src/` layout.

## Version

```text
3.3.1.4-clean-datacube
```

## Canonical package

The only canonical Python package is:

```text
src/acmf/
```

No root `acmf/` stub, no `index.php`, no repo-dump bundle.

## Quick start

```bash
python main.py --task health
python main.py --task empirical_canada
python main.py --task synthetic_ladder
python main.py --task world_profile
python main.py --task world_ident
```

## Datafetch and panel builder

```bash
python main.py --task data_list_indicators
python main.py --task data_fisher_rank
python main.py --task data_build_minimal
python main.py --task data_build_standard
python main.py --task datacube_init
python main.py --task datacube_build
```

Direct builder calls:

```bash
python scripts/build_panel_dataset.py --list-indicators
python scripts/build_panel_dataset.py --fisher-rank
python scripts/build_panel_dataset.py --budget standard --years 1995:auto
```

`auto` means `current_calendar_year - 2`. In 2026, this resolves to 2024.

## World Bank downloaders

Two backends are available:

```bash
python scripts/download_world_data.py --backend requests --start-year 1995 --end-year auto
python scripts/download_world_data.py --backend wbdata --start-year 1995 --end-year auto
```

## Tests

```bash
PYTHONPATH=src pytest -q
```

## Deployment

See `README_DEPLOY.md`.

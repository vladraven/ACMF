# ACMF Data Fetch and Panel Builder

Version line: `3.3.1.5-clean-observation-designer`.

## Complete-data year rule

The default complete-data cutoff is:

```text
complete_year = current_calendar_year - 2
```

For example, in calendar year 2026 the default complete-data year is 2024. This avoids treating partially populated 2025 observations as complete calibration data.

## World Bank downloaders

Two World Bank backends are available:

```bash
python scripts/download_world_data.py --backend requests --start-year 1995 --end-year auto
python scripts/download_world_data.py --backend wbdata --start-year 1995 --end-year auto
```

- `requests`: direct World Bank REST API backend.
- `wbdata`: optional `wbdata` package backend.
- `auto`: tries `wbdata`, then falls back to `requests`.

## Metadata-driven panel builder

Indicator metadata lives at:

```text
data/metadata/indicators.yaml
src/acmf/data/indicators.yaml
```

Build commands:

```bash
python scripts/build_panel_dataset.py --list-indicators
python scripts/build_panel_dataset.py --fisher-rank
python scripts/build_panel_dataset.py --budget minimal --years 1995:auto
python scripts/build_panel_dataset.py --budget standard --constructs Ch,M,Y --years 1995:auto
```

The score named `oed_score` is an observation-design priority heuristic:

```text
oed_score = ovi * coverage * (quality / 5) / cost
```

It is not the same as the model-level Fisher Information Matrix computed from ACMF sensitivities in `acmf.identifiability`.

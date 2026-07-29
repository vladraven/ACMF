# ACMF Clean Package Report

## Purpose

This package removes the deployment blockers and stale artifacts reported in the audit:

- root-level `acmf/` stub package removed;
- root-level `acmf_core.py` / `acmf_solver.py` legacy stubs removed;
- `index.php` repository-dump utility removed;
- `ACMF_PROJECT_BUNDLE.txt` excluded from the package;
- obsolete flat duplicate modules removed from the repository root;
- `main.py` no longer exposes missing `v2_4_7` / `v2_4_8` tasks;
- `README_DEPLOY.md` now documents only physically present tasks;
- `MANIFEST.txt` regenerated from the actual file tree;
- `app.py` now supports bearer-token protection through `ACMF_API_TOKEN`;
- world-panel data and direct World Bank downloader retained/integrated.

## Canonical package layout

The only canonical Python package is now:

```text
src/acmf/
```

There is no root-level `acmf/` package, so the previous import shadowing problem is removed.

## Available tasks

```bash
python main.py --task health
python main.py --task empirical_canada
python main.py --task synthetic_ladder
python main.py --task world_profile
python main.py --task world_ident
python main.py --task v2_4_9
```

## Validation performed

### Pytest

```text
13 passed
```

### Runtime smoke tests

All these commands returned status `0`:

```text
python main.py --task health
python main.py --task empirical_canada
python main.py --task synthetic_ladder
python main.py --task world_profile
python main.py --task world_ident
python main.py --task v2_4_9
```

## Manifest

`MANIFEST.txt` was regenerated from the live cleaned tree and covers `129` files.

## Security/deploy hygiene

- No `index.php` is shipped.
- No root-level `acmf/` stub is shipped.
- No repo-dump text bundle is shipped.
- API task execution can be protected by setting `ACMF_API_TOKEN`.

## Notes

The package keeps the existing empirical pipeline and adds the world-panel identifiability workflow. Historical task names whose modules are absent were removed rather than left as broken deployment entrypoints.

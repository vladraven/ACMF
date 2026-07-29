# ACMF deploy entrypoint patch

Copy these files into the repository root.

## Batch / worker deployment

Start command:

```bash
python main.py --task v2_4_9
```

or set:

```bash
TASK=v2_4_9
```

and run:

```bash
python main.py
```

## Web deployment

If the platform requires a long-running web process, install `fastapi` and `uvicorn`, then use:

```bash
uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}
```

Health endpoint:

```text
GET /health
```

Run endpoint:

```text
POST /run/v2_4_9
```

## Important

`main.py` expects the existing package structure:

```text
empirical/scripts/run_v2_4_9_quebec_70_74_alpha_sensitivity.py
empirical/scripts/run_v2_4_8_quebec_70_74_case_study.py
empirical/scripts/run_v2_4_7_regional_regime_explanation.py
```


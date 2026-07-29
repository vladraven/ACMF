from __future__ import annotations
from pathlib import Path
import pandas as pd

ID_COLUMNS = ['country_name', 'country_code', 'Year']


def coverage_matrix(panel: pd.DataFrame, by_country: bool = True) -> pd.DataFrame:
    value_cols = [c for c in panel.columns if c not in ID_COLUMNS]
    if by_country and 'country_name' in panel.columns:
        rows = []
        for country, g in panel.groupby('country_name'):
            row = {'country_name': country, 'rows': len(g)}
            row.update({c: float(g[c].notna().mean()) for c in value_cols})
            rows.append(row)
        return pd.DataFrame(rows)
    return pd.DataFrame([{'indicator': c, 'coverage': float(panel[c].notna().mean())} for c in value_cols])


def indicator_quality_report(panel: pd.DataFrame, metadata_df: pd.DataFrame | None = None) -> pd.DataFrame:
    value_cols = [c for c in panel.columns if c not in ID_COLUMNS]
    rows = []
    meta_by_col = {}
    if metadata_df is not None and 'column' in metadata_df.columns:
        meta_by_col = {r['column']: r for _, r in metadata_df.iterrows()}
    for col in value_cols:
        m = meta_by_col.get(col, {})
        actual = float(panel[col].notna().mean())
        expected = float(m.get('coverage', actual)) if hasattr(m, 'get') else actual
        quality = float(m.get('quality', 3.0)) if hasattr(m, 'get') else 3.0
        rows.append({
            'indicator': col,
            'id': m.get('id', col) if hasattr(m, 'get') else col,
            'construct': m.get('construct', '') if hasattr(m, 'get') else '',
            'source': m.get('source', '') if hasattr(m, 'get') else '',
            'coverage_actual': actual,
            'coverage_expected': expected,
            'quality_metadata': quality,
            'quality_adjusted_coverage': actual * quality / 5.0,
        })
    return pd.DataFrame(rows).sort_values('quality_adjusted_coverage', ascending=False).reset_index(drop=True)


def validate_cube_schema(root: str | Path) -> dict:
    root = Path(root)
    required_dirs = [
        root / 'raw', root / 'processed', root / 'processed' / 'minimal',
        root / 'processed' / 'standard', root / 'processed' / 'research', root / 'metadata'
    ]
    required_files = [root / 'metadata' / 'indicators.yaml', root / 'metadata' / 'sources.yaml', root / 'metadata' / 'provenance.yaml']
    missing_dirs = [str(p) for p in required_dirs if not p.exists()]
    missing_files = [str(p) for p in required_files if not p.exists()]
    return {'ok': not missing_dirs and not missing_files, 'missing_dirs': missing_dirs, 'missing_files': missing_files}

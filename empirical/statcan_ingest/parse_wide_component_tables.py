"""Generic parser helpers for StatCan compact wide component tables.

These are used for 17-10-0014, 17-10-0015, 17-10-0006-like files when present.
The build script detects files and uses specialized wrappers over this generic parser.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
from .common import read_csv_rows, carry_forward, to_number, parse_period

def parse_generic_wide(path: str | Path, header_rows: dict, row_start: int, row_key: str = "age_group", stop_prefix: str = "Symbol legend") -> pd.DataFrame:
    rows = read_csv_rows(Path(path))
    headers = {name: carry_forward(rows[idx]) for name, idx in header_rows.items()}
    records=[]
    for row in rows[row_start:]:
        if not row or str(row[0]).startswith(stop_prefix): break
        key=row[0]
        if not key: continue
        for j in range(1, len(row)):
            rec={row_key:key, "value":to_number(row[j])}
            for name, vals in headers.items():
                if j < len(vals): rec[name]=vals[j]
            if "period" in rec:
                ys, ye=parse_period(rec["period"]); rec["start_year"]=ys; rec["end_year"]=ye
            records.append(rec)
    return pd.DataFrame(records)

from __future__ import annotations
import csv, hashlib, re
from pathlib import Path
import numpy as np

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read_csv_rows(path: Path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.reader(fh))

def carry_forward(row):
    out=[]; last=""
    for v in row:
        if v != "": last = v
        out.append(last)
    return out

def to_number(x):
    s = str(x).replace(",", "").replace("t", "").strip()
    if s in {"", "..", "...", "x", "nan"}: return np.nan
    try: return float(s)
    except Exception: return np.nan

def parse_period(p: str):
    m = re.match(r"(\d{4}) / (\d{4})", str(p))
    if not m: return None, None
    return int(m.group(1)), int(m.group(2))

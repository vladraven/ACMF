from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import yaml


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def file_sha256(path: str | Path) -> str:
    p = Path(path)
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


@dataclass
class ProvenanceRecord:
    dataset_id: str
    version: str
    source: str
    source_path: str
    output_path: str
    retrieval_date: str
    build_date: str
    complete_data_year: int
    sha256: str
    notes: str = ''


def make_provenance_record(dataset_id: str, version: str, source: str, source_path: str | Path,
                           output_path: str | Path, complete_data_year: int, notes: str = '') -> ProvenanceRecord:
    source_path = Path(source_path)
    return ProvenanceRecord(
        dataset_id=dataset_id,
        version=version,
        source=source,
        source_path=str(source_path),
        output_path=str(output_path),
        retrieval_date=utc_now_iso(),
        build_date=utc_now_iso(),
        complete_data_year=int(complete_data_year),
        sha256=file_sha256(source_path) if source_path.exists() else '',
        notes=notes,
    )


def load_provenance(path: str | Path) -> dict:
    p = Path(path)
    if not p.exists():
        return {'records': []}
    data = yaml.safe_load(p.read_text(encoding='utf-8'))
    return data or {'records': []}


def append_provenance_record(path: str | Path, record: ProvenanceRecord | dict) -> dict:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = load_provenance(p)
    rec = asdict(record) if hasattr(record, '__dataclass_fields__') else dict(record)
    data.setdefault('records', []).append(rec)
    p.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding='utf-8')
    return data

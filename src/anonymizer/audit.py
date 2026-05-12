from __future__ import annotations

import hashlib
import json
import socket
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import __version__
from .profile import Profile, profile_sha256


def file_sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def make_audit_record(
    *,
    input_file: str | Path,
    output_file: str | Path | None,
    profile: Profile,
    key_version: int,
    rows_in: int | None,
    rows_out: int | None,
    operations: dict[str, list[str]],
    exit_code: int,
    started_at: float,
    error: str | None = None,
) -> dict[str, Any]:
    duration_ms = int((time.time() - started_at) * 1000)
    record: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "tool_version": __version__,
        "run_id": str(uuid.uuid4()),
        "input_file": str(input_file),
        "output_file": str(output_file) if output_file else None,
        "input_sha256": file_sha256(input_file) if Path(input_file).exists() else None,
        "output_sha256": file_sha256(output_file) if output_file and Path(output_file).exists() else None,
        "rows_in": rows_in,
        "rows_out": rows_out,
        "profile": {
            "id": profile.id,
            "version": profile.version,
            "sha256": profile_sha256(profile),
        },
        "key_version": key_version,
        "operations": operations,
        "execution": {
            "duration_ms": duration_ms,
            "exit_code": exit_code,
            "mode": "headless",
            "host": socket.gethostname(),
        },
    }
    if error:
        record["error"] = error
    return record


def write_audit(record: dict[str, Any], audit_path: str | Path) -> None:
    p = Path(audit_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

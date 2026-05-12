from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class KeyMaterial:
    version: int
    key: bytes


def load_keyfile(path: str | Path) -> KeyMaterial:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))
    raw = p.read_bytes()

    try:
        obj = json.loads(raw.decode("utf-8"))
        version = int(obj.get("version", 1))
        key_hex = obj.get("key_hex")
        if not key_hex:
            raise ValueError("missing key_hex")
        key = bytes.fromhex(key_hex)
    except json.JSONDecodeError:
        version = 1
        key = raw

    if not key:
        raise ValueError("empty key")
    return KeyMaterial(version=version, key=key)

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import polars as pl

from .crypto import pseudonymize
from .profile import Action, Profile


@dataclass
class RunStats:
    rows_in: int
    rows_out: int
    operations: dict[str, list[str]] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


def _mask_value(value: Any, pattern: str) -> Any:
    if value is None:
        return None
    s = str(value)
    digits = [c for c in s if c.isdigit()]
    keep_count = pattern.count("#")
    kept = "".join(digits[-keep_count:]) if keep_count else ""
    kept_iter = iter(kept)
    out = []
    for ch in pattern:
        if ch == "#":
            out.append(next(kept_iter, ""))
        else:
            out.append(ch)
    return "".join(out)


def _generalize_value(value: Any, bins: list) -> Any:
    if value is None or value == "":
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    for b in bins:
        lo, hi = b.range
        if lo <= number <= hi:
            return b.label
    return None


def run_pipeline(input_path: str | Path, output_path: str | Path, profile: Profile, key: bytes) -> RunStats:
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = pl.read_csv(input_path, separator=profile.defaults.delimiter)
    rows_in = df.height
    warnings: list[str] = []
    operations: dict[str, list[str]] = {a.value: [] for a in Action}

    for rule in profile.columns:
        if rule.name not in df.columns:
            msg = f"missing column: {rule.name}"
            if profile.defaults.on_missing_column == "fail":
                raise ValueError(msg)
            warnings.append(msg)
            continue

        operations[rule.action.value].append(rule.name)

        if rule.action == Action.keep:
            continue
        if rule.action == Action.drop:
            df = df.drop(rule.name)
            continue
        if rule.action == Action.pseudonymize:
            prefix = rule.prefix or ""
            length = rule.length or 16
            df = df.with_columns(
                pl.col(rule.name).map_elements(
                    lambda v: pseudonymize(None if v is None else str(v), key, prefix=prefix, length=length),
                    return_dtype=pl.String,
                )
            )
            continue
        if rule.action == Action.mask:
            assert rule.pattern is not None
            df = df.with_columns(
                pl.col(rule.name).map_elements(lambda v: _mask_value(v, rule.pattern), return_dtype=pl.String)
            )
            continue
        if rule.action == Action.generalize:
            assert rule.bins is not None
            df = df.with_columns(
                pl.col(rule.name).map_elements(lambda v: _generalize_value(v, rule.bins), return_dtype=pl.String)
            )
            continue

    df.write_csv(output_path, separator=profile.defaults.delimiter)
    return RunStats(rows_in=rows_in, rows_out=df.height, operations={k: v for k, v in operations.items() if v}, warnings=warnings)

from __future__ import annotations

import hashlib
import json
from enum import Enum
from pathlib import Path
from typing import List, Literal

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator


class Action(str, Enum):
    pseudonymize = "pseudonymize"
    mask = "mask"
    drop = "drop"
    keep = "keep"
    generalize = "generalize"


class Bin(BaseModel):
    range: List[int] = Field(..., min_length=2, max_length=2)
    label: str

    @field_validator("range")
    @classmethod
    def valid_range(cls, value: List[int]) -> List[int]:
        if value[0] > value[1]:
            raise ValueError("bin range start must be <= end")
        return value


class ColumnRule(BaseModel):
    name: str
    action: Action
    prefix: str | None = None
    length: int | None = None
    pattern: str | None = None
    bins: List[Bin] | None = None

    @field_validator("length")
    @classmethod
    def length_positive(cls, value: int | None) -> int | None:
        if value is not None and value <= 0:
            raise ValueError("length must be > 0")
        return value

    @model_validator(mode="after")
    def validate_action_config(self) -> "ColumnRule":
        if self.action == Action.mask and not self.pattern:
            raise ValueError("mask action requires a pattern")
        if self.action == Action.generalize and not self.bins:
            raise ValueError("generalize action requires bins")
        return self


class Defaults(BaseModel):
    on_missing_column: Literal["warn", "fail"] = "warn"
    on_null: Literal["keep_null", "empty_string"] = "keep_null"
    delimiter: Literal[",", ";"] = ","


class Profile(BaseModel):
    id: str = Field(..., description="Stable profile id, e.g. crm-basic")
    version: str = Field(..., description="Profile version, e.g. 1.0.0")
    name: str
    key_version: int = 1
    columns: List[ColumnRule]
    defaults: Defaults = Defaults()


def load_profile(path: str | Path) -> Profile:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))
    raw = p.read_text(encoding="utf-8")
    try:
        data = yaml.safe_load(raw)
    except Exception as exc:
        raise ValueError(f"failed to parse profile: {exc}") from exc
    try:
        return Profile.model_validate(data)
    except ValidationError as exc:
        raise ValueError(exc.errors()) from exc


def profile_sha256(profile: Profile) -> str:
    canonical = json.dumps(profile.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

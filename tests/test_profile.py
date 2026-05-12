from pathlib import Path
import textwrap

import pytest

from anonymizer.profile import load_profile, profile_sha256


def write(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "profile.yaml"
    p.write_text(content, encoding="utf-8")
    return p


def test_valid_profile(tmp_path):
    p = write(tmp_path, textwrap.dedent("""
    id: crm-basic
    version: 1.0.0
    name: CRM Basic
    key_version: 1
    columns:
      - name: email
        action: pseudonymize
        prefix: PID_
        length: 16
      - name: phone
        action: mask
        pattern: "****-####"
    defaults:
      on_missing_column: warn
      on_null: keep_null
      delimiter: ","
    """))
    profile = load_profile(p)
    assert profile.id == "crm-basic"
    assert len(profile_sha256(profile)) == 64


def test_invalid_action_fails(tmp_path):
    p = write(tmp_path, textwrap.dedent("""
    id: bad
    version: 1.0.0
    name: Bad
    columns:
      - name: email
        action: unknown
    """))
    with pytest.raises(ValueError):
        load_profile(p)


def test_mask_requires_pattern(tmp_path):
    p = write(tmp_path, textwrap.dedent("""
    id: bad
    version: 1.0.0
    name: Bad
    columns:
      - name: phone
        action: mask
    """))
    with pytest.raises(ValueError):
        load_profile(p)

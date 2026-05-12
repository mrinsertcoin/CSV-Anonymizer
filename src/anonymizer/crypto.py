from __future__ import annotations

import base64
import hashlib
import hmac
from typing import Optional


def _b32_nopad(data: bytes) -> str:
    """Return Base32 encoded data without '=' padding."""
    return base64.b32encode(data).decode("ascii").rstrip("=")


def pseudonymize(value: Optional[str], key: bytes, prefix: str = "", length: int = 16) -> Optional[str]:
    """Deterministically pseudonymize a value with HMAC-SHA256.

    This is not encryption. It is a keyed one-way transformation. The original
    value is not recoverable from the pseudonym, but the same input with the
    same key produces the same pseudonym.
    """
    if value is None:
        return None
    if not isinstance(key, (bytes, bytearray)) or len(key) == 0:
        raise ValueError("key must be non-empty bytes")
    if length <= 0:
        raise ValueError("length must be > 0")

    digest = hmac.new(bytes(key), str(value).encode("utf-8"), hashlib.sha256).digest()
    token = _b32_nopad(digest)
    return f"{prefix}{token}"[:length]

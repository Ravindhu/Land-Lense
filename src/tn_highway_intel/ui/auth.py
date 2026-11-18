"""Dashboard password check (docs/API.md section 1.2, docs/SECURITY_AND_LEGAL.md section 4).

UI_PASSWORD_SHA256 holds the SHA-256 hex digest of the password, never the password itself.
Comparison is constant-time. A missing hash locks the dashboard instead of opening it.
"""

from __future__ import annotations

import hashlib
import hmac
from typing import Optional


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def check_password(entered: str, expected_sha256: Optional[str]) -> bool:
    if not expected_sha256:
        return False
    return hmac.compare_digest(hash_password(entered), expected_sha256.strip().lower())

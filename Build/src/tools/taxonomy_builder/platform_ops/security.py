

"""platform_ops.security

Redaction helpers for logs/metrics. Keep stdlib-only.

Public API:
    redact(value: str) -> str
        - masks emails, obvious key/value secrets, bearer tokens, and long token-like blobs.

Notes:
- This is intentionally conservative: it preserves surrounding text and structure while
  replacing sensitive substrings with placeholders.
- Extend patterns as you learn your real-world payload shapes.
"""
from __future__ import annotations

import re
from typing import Match

# --- Patterns ---
_EMAIL_RE = re.compile(r"([A-Za-z0-9._%+-])[A-Za-z0-9._%+-]*(@[A-Za-z0-9.-]+\.[A-Za-z]{2,})")
# key=value style: password=..., api_key: ..., token = ...
_KV_SECRET_RE = re.compile(r"(?i)\b(password|pass|secret|token|api[_-]?key|authorization)\s*[:=]\s*([^\s,;]+)")
# Authorization: Bearer <token>
_BEARER_RE = re.compile(r"(?i)\bBearer\s+([A-Za-z0-9._\-]+)")
# Generic long token-like sequences (>= 24 chars) of common alphabets
_LONG_TOKEN_RE = re.compile(r"([A-Za-z0-9_\-\.]{24,})")


def _mask_email(m: Match[str]) -> str:
    first = m.group(1)
    domain = m.group(2)
    return f"{first}***{domain}"


def _mask_token_str(token: str) -> str:
    # keep only first/last 4 to retain some debuggability
    if len(token) <= 8:
        return "***"  # very short — just nuke
    return f"{token[:4]}…{token[-4:]}"  # unicode ellipsis ok in logs


def _mask_kv(m: Match[str]) -> str:
    key = m.group(1)
    # Use placeholder that indicates redaction type
    return f"{key}=***"


def redact(value: str | object) -> str:
    """Best-effort redaction suitable for log lines.

    - Emails: `a.b@example.com` -> `a***@example.com`
    - Key/Value secrets: `password=foo` -> `password=***`
    - Bearer tokens: `Bearer eyJ...` -> `Bearer ****`
    - Long tokens: `sk_live_...` or long base64-like strings -> `sk_l…abcd`
    """
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)

    # 1) Emails
    value = _EMAIL_RE.sub(_mask_email, value)

    # 2) KV secrets (password=, token:, api_key=, authorization=)
    value = _KV_SECRET_RE.sub(_mask_kv, value)

    # 3) Bearer tokens
    value = _BEARER_RE.sub("Bearer ****", value)

    # 4) Long token-like strings — but avoid masking URLs by skipping patterns with '://'
    def _maybe_mask_long(m: Match[str]) -> str:
        s = m.group(1)
        if "://" in s:
            return s
        return _mask_token_str(s)

    value = _LONG_TOKEN_RE.sub(_maybe_mask_long, value)

    return value


__all__ = ["redact"]
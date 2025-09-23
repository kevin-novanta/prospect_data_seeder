

"""HTTP cache token helpers (no-op stubs).

This module exposes a tiny interface for conditional requests using ETag and
Last-Modified. In Phase 3 (offline-first), we implement no-ops so callers can
import and call these functions without side effects. Later phases can replace
these with an on-disk cache or key-value store.

Public API:
    get_conditional_headers(url: str) -> dict
        Return headers to send with a request (If-None-Match / If-Modified-Since).
        Currently returns an empty dict.

    remember_response(url: str, etag: str | None, last_modified: str | None) -> None
        Persist received validators for future calls. Currently a no-op.

    read_tokens(url: str) -> tuple[str | None, str | None]
        Return previously stored (etag, last_modified) for `url`. Currently (None, None).
"""
from __future__ import annotations

from typing import Optional, Tuple, Dict


def get_conditional_headers(url: str) -> Dict[str, str]:
    """Return headers for conditional GET. No-op in Phase 3.

    Examples (future implementation):
        {
            "If-None-Match": etag,
            "If-Modified-Since": last_modified,
        }
    """
    return {}


def remember_response(url: str, etag: Optional[str], last_modified: Optional[str]) -> None:
    """Store cache validators for `url`. No-op in Phase 3."""
    return None


def read_tokens(url: str) -> Tuple[Optional[str], Optional[str]]:
    """Read previously stored (etag, last_modified). Returns (None, None)."""
    return (None, None)


__all__ = [
    "get_conditional_headers",
    "remember_response",
    "read_tokens",
]
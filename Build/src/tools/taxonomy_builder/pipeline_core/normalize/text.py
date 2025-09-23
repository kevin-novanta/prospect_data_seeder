"""Text normalization helpers.

Phase 5 goals:
  - clean(s): trim, collapse whitespace, normalize unicode
  - slugify(s): lowercase, ASCII-safe, dash-separated slugs

Both functions are stdlib-only and safe for general use in parsing/normalizing.
"""
from __future__ import annotations

import re
import unicodedata as _ud
from typing import Optional

# precompiled patterns
_WS_RE = re.compile(r"\s+", re.UNICODE)
# control chars except common whitespace (tab, nl, cr) — remove them
_CTRL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
# anything that's not alphanumeric becomes a dash during slugify
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


def _nfkc(s: str) -> str:
    # Normalize to a compatibility form first (handles full-width, ligatures)
    return _ud.normalize("NFKC", s)


def clean(value: Optional[str]) -> str:
    """Return a tidy string: unicode-normalized, controls removed, spaces collapsed.

    Examples
    --------
    >>> clean("  SEO\u00a0\u00a0 &  PPC  ")
    'SEO & PPC'
    >>> clean(None)
    ''
    """
    if not value:
        return ""
    s = str(value)
    s = _nfkc(s)
    s = _CTRL_RE.sub("", s)
    # Collapse all whitespace (including non-breaking) to single spaces
    s = _WS_RE.sub(" ", s)
    return s.strip()


def slugify(value: Optional[str]) -> str:
    """ASCII-safe, lowercase, dash-separated slug.

    Steps:
      1) clean + NFKD (compat decomposition)
      2) strip diacritics by encoding to ASCII (ignore errors)
      3) lowercase
      4) non-alnum -> single dash; trim dashes

    Examples
    --------
    >>> slugify('Email Marketing')
    'email-marketing'
    >>> slugify('Café & SEO — 2025!')
    'cafe-seo-2025'
    >>> slugify(None)
    ''
    """
    s = clean(value)
    if not s:
        return ""
    # NFKD then drop diacritics
    s = _ud.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = s.lower()
    s = _NON_ALNUM_RE.sub("-", s)
    s = s.strip("-")
    # collapse consecutive dashes (in case of multiple symbol runs)
    s = re.sub(r"-+", "-", s)
    return s


__all__ = ["clean", "slugify"]

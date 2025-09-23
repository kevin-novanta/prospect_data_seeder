

"""Type helpers for taxonomy items.

Phase 5: keep this intentionally tiny and dependency-free.  Other stages
(tagging, lineage) can import these helpers without pulling parsing logic.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from .text import clean


class ItemType(str, Enum):
    CATEGORY = "category"
    SUBCATEGORY = "subcategory"
    ALL_IN = "all_in"

    @classmethod
    def coerce(cls, value: Optional[str]) -> Optional["ItemType"]:
        if not value:
            return None
        v = str(value).strip().lower()
        try:
            return cls(v)  # type: ignore[arg-type]
        except ValueError:
            return None


def is_all_in(name: Optional[str], href: Optional[str]) -> bool:
    """Best-effort check whether an item represents an "All in …" link.

    Heuristics (conservative):
      - If the display name contains the phrase "all in" (case-insensitive).
      - If the href contains common all-in patterns like "all-in", "/all", "all/",
        or a trailing "/all" segment.

    Notes:
      - This deliberately avoids language-specific patterns beyond English.
      - Callers should not rely on this for i18n without augmenting patterns.
    """
    n = clean(name).lower()
    if "all in" in n:
        return True

    if not href:
        return False

    h = href.strip().lower()
    # quick exits for non-http relative paths are fine; we only check substrings
    if "all-in" in h:
        return True
    # common path segment endings
    if h.endswith("/all") or "/all/" in h:
        return True
    # sometimes query hints like ?all=1 or &all=true
    if "?all=" in h or "&all=" in h:
        return True

    return False


__all__ = ["ItemType", "is_all_in"]
"""Type helpers for taxonomy items.

Phase 5: keep this intentionally tiny and dependency-free. Other stages
(tagging, lineage) can import these helpers without pulling parsing logic.
"""
from __future__ import annotations

import re
from enum import Enum
from typing import Optional, Mapping, Tuple

from .text import clean, slugify


# URL fragments that commonly indicate a directory/listing root. Parsers can
# pass additional hints via attrs if the site deviates.
ROOT_HINTS = ("/directory/", "/categories", "/category/")


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


# Precompile case-insensitive pattern for speed and clarity.
_RE_ALL_IN = re.compile(r"^\s*all\s+in\b", re.IGNORECASE)


def is_all_in(
    name: Optional[str],
    href: Optional[str],
    attrs: Optional[Mapping[str, str]] = None,
    *,
    root_hints: Tuple[str, ...] = ROOT_HINTS,
) -> bool:
    """Best-effort check whether an item represents an "All in …" link.

    Heuristics (ordered, short-circuiting):
      1) Text rule: display text starts with or contains "All in" (case-insensitive).
      2) Attribute rule: aria-label/title contain "All in" (if attrs provided by parser).
      3) URL rule: href contains a root-hint fragment like "/directory/".

    Notes:
      - "attrs" is optional to keep callsites simple; parsers may pass a tag's
        attribute mapping (e.g., {'aria-label': 'All in SEO'}) for stronger signal.
      - For i18n sites, pass a different regex or additional hints via arguments.
    """
    # 1) Text rule
    n = clean(name)
    if n and _RE_ALL_IN.search(n):
        return True

    # 2) Attribute rule (optional)
    if attrs:
        aria = clean(attrs.get("aria-label"))
        title = clean(attrs.get("title"))
        if (aria and _RE_ALL_IN.search(aria)) or (title and _RE_ALL_IN.search(title)):
            return True

    # 3) URL rule
    if href:
        h = href.strip().lower()
        for frag in root_hints:
            if frag and frag.lower() in h:
                return True
        # keep a few legacy fallbacks for common patterns
        if h.endswith("/all") or "/all/" in h or "all-in" in h or "?all=" in h or "&all=" in h:
            return True

    return False


def normalize_all_in_name(display: Optional[str]) -> Tuple[str, str]:
    """Return a canonical label and slug for an "All in …" display name.

    Examples:
      "All in Email Marketing" -> ("Email Marketing", "email-marketing")
      "all in   SEO"           -> ("SEO", "seo")
      None / ""                 -> ("All", "all")  # conservative fallback
    """
    text = clean(display)
    if not text:
        return ("All", "all")

    # Strip leading "All in" phrase if present; leave rest as the label.
    m = _RE_ALL_IN.match(text)
    if m:
        label = text[m.end():].strip(" :\u2013-\u2014")  # trim separators
        label = label or "All"
    else:
        label = text

    return (label, slugify(label))


__all__ = ["ItemType", "is_all_in", "normalize_all_in_name", "ROOT_HINTS"]
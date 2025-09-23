"""Build lineage and stable IDs for parsed taxonomy items.

Input items (from parser):
    {"type": "category"|"subcategory"|"all_in",
     "name": str,
     "href": str | None,
     "parent": str | None}

Output items (normalized):
    {
      "id": str,             # stable ID based on type/slug/parent_slug
      "parent_id": str|None,
      "type": str,           # one of ItemType values
      "name": str,           # cleaned display name
      "slug": str,           # slugified name
      "url": str,            # canonical absolute url or ""
      "parent": str|None,    # cleaned parent name (if any)
      "parent_slug": str|None
    }

Rules:
- Category IDs:          "category:{slug}"
- Subcategory IDs:       "subcategory:{parent_slug}:{slug}"
- All-in link IDs:       "all_in:{parent_slug}:{slug}" (slug from link text)
- Parent lookup by cleaned name (case-insensitive) → parent_slug
- URL canonicalized relative to `base_url` (optional); empty string if unknown
- Items missing a valid name are skipped
- Unknown parents: keep parent fields, parent_id=None
"""
from __future__ import annotations

from typing import Iterable, List, Dict, Optional, Tuple

from .text import clean, slugify
from .urls import canonicalize
from .types import ItemType, is_all_in


def _build_id(item_type: ItemType, slug: str, parent_slug: Optional[str]) -> str:
    if item_type == ItemType.CATEGORY:
        return f"{item_type.value}:{slug}"
    p = parent_slug or ""
    return f"{item_type.value}:{p}:{slug}"


def _coerce_type(v: Optional[str], name: Optional[str], href: Optional[str]) -> Optional[ItemType]:
    t = ItemType.coerce(v)
    if t is None:
        return None
    if t != ItemType.ALL_IN and is_all_in(name, href):
        return ItemType.ALL_IN
    return t


def attach_lineage(items: Iterable[Dict], base_url: Optional[str] = None) -> List[Dict]:
    """Normalize parsed items and attach lineage.

    Rules implemented here:
    - Categories have **no** parent fields in output.
    - URLs are never empty: if `href` is missing/blank, fall back to `base_url` (or "").
    - `parent_id` is only present for non-category items when known; otherwise omitted.
    """
    # First pass: register categories (name → (slug, id))
    categories: Dict[str, Tuple[str, str]] = {}
    interim: List[Dict] = []

    for raw in items or []:
        name = clean(raw.get("name"))
        if not name:
            continue
        href = (raw.get("href") or "").strip()
        parent_name = clean(raw.get("parent")) or None
        t = _coerce_type(raw.get("type"), name, href)
        if t is None:
            continue
        slug = slugify(name)
        # Guarantee non-empty absolute URL when possible
        url = canonicalize(base_url, href) if href else (base_url or "")

        interim.append({
            "type": t,
            "name": name,
            "slug": slug,
            "url": url,
            "parent": parent_name,
        })

        if t == ItemType.CATEGORY:
            cid = _build_id(t, slug, None)
            categories[name.lower()] = (slug, cid)

    # Second pass: attach parent linkage and finalize items
    normalized: List[Dict] = []

    for it in interim:
        t: ItemType = it["type"]
        name: str = it["name"]
        slug: str = it["slug"]
        url: str = it["url"]
        parent_name: Optional[str] = it.get("parent")

        parent_slug: Optional[str] = None
        parent_id: Optional[str] = None
        if parent_name:
            key = parent_name.lower()
            if key in categories:
                parent_slug, parent_id = categories[key]

        _id = _build_id(t, slug, parent_slug)

        # Base fields present on all items
        out: Dict[str, object] = {
            "id": _id,
            "type": t.value,
            "name": name,
            "slug": slug,
            "url": url,
        }

        # Only add parent fields for non-category rows
        if t != ItemType.CATEGORY:
            out["parent"] = parent_name
            if parent_slug is not None:
                out["parent_slug"] = parent_slug
            if parent_id is not None:
                out["parent_id"] = parent_id

        normalized.append(out)

    return normalized

__all__ = ["attach_lineage"]

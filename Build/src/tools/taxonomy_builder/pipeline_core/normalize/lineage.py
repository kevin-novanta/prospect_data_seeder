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

Special handling for ALL_IN:
- If an "All in … X" record appears within a subcategory context, parent should
  be the subcategory, not the top-level category.
- We detect this by:
  (a) If the incoming `parent` already names a known subcategory, use that; else
  (b) Parse the target label from the All-in text and see if that subcategory
      exists under the category; if so, parent to that subcategory; else
  (c) Fall back to the category.
"""
from __future__ import annotations

from typing import Iterable, List, Dict, Optional, Tuple

from .text import clean, slugify
from .urls import canonicalize
from .types import ItemType, is_all_in, normalize_all_in_name


def _build_id(item_type: ItemType, slug: str, parent_slug: Optional[str]) -> str:
    if item_type == ItemType.CATEGORY:
        return f"{item_type.value}:{slug}"
    p = parent_slug or ""
    return f"{item_type.value}:{p}:{slug}"


def _coerce_type(v: Optional[str], name: Optional[str], href: Optional[str]) -> Optional[ItemType]:
    t = ItemType.coerce(v)
    if t is None:
        return None
    # If caller mislabeled and it looks like an All-in, coerce
    if t != ItemType.ALL_IN and is_all_in(name, href):
        return ItemType.ALL_IN
    return t


def attach_lineage(items: Iterable[Dict], base_url: Optional[str] = None) -> List[Dict]:
    """Normalize parsed items and attach lineage.

    Strategy:
      1) First pass → normalize base fields; collect candidates.
      2) Build registries for categories and subcategories.
      3) Second pass → finalize with parent linkage and IDs. For ALL_IN, prefer
         subcategory parent when identifiable, else category.
    """
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
        url = canonicalize(base_url, href) if href else (base_url or "")

        interim.append({
            "type": t,
            "name": name,
            "slug": slug,
            "url": url,
            "parent": parent_name,
            # Keep raw href for potential downstream hints (not exported)
            "_href": href or None,
        })

    # Build registries
    categories: Dict[str, Tuple[str, str, str]] = {}
    # name_lower -> (cat_name, cat_slug, cat_id)

    subcategories_by_name: Dict[Tuple[str, str], Tuple[str, str, str]] = {}
    # (cat_slug, sub_name_lower) -> (sub_name, sub_slug, sub_id)

    subcategories_by_slug: Dict[Tuple[str, str], Tuple[str, str, str]] = {}
    # (cat_slug, sub_slug) -> (sub_name, sub_slug, sub_id)

    # First register categories (need cat slug/id for subcats)
    for it in interim:
        if it["type"] == ItemType.CATEGORY:
            cat_name = it["name"]
            cat_slug = it["slug"]
            cat_id = _build_id(ItemType.CATEGORY, cat_slug, None)
            categories[cat_name.lower()] = (cat_name, cat_slug, cat_id)

    # Register subcategories
    for it in interim:
        if it["type"] == ItemType.SUBCATEGORY:
            parent_name = it.get("parent")
            if not parent_name:
                continue
            cat_key = parent_name.lower()
            if cat_key not in categories:
                continue
            _cat_name, cat_slug, cat_id = categories[cat_key]
            sub_name = it["name"]
            sub_slug = it["slug"]
            sub_id = _build_id(ItemType.SUBCATEGORY, sub_slug, cat_slug)
            subcategories_by_name[(cat_slug, sub_name.lower())] = (sub_name, sub_slug, sub_id)
            subcategories_by_slug[(cat_slug, sub_slug)] = (sub_name, sub_slug, sub_id)

    # Finalize with lineage
    normalized: List[Dict] = []

    for it in interim:
        t: ItemType = it["type"]
        name: str = it["name"]
        slug: str = it["slug"]
        url: str = it["url"]
        parent_name: Optional[str] = it.get("parent")

        parent_slug: Optional[str] = None
        parent_id: Optional[str] = None
        parent_display: Optional[str] = None

        if t == ItemType.CATEGORY:
            _id = _build_id(t, slug, None)
            out: Dict[str, object] = {
                "id": _id,
                "type": t.value,
                "name": name,
                "slug": slug,
                "url": url,
            }
            normalized.append(out)
            continue

        # Resolve category if provided
        cat_slug: Optional[str] = None
        cat_id: Optional[str] = None
        if parent_name:
            cat_rec = categories.get(parent_name.lower())
            if cat_rec:
                _cat_name, cat_slug, cat_id = cat_rec

        if t == ItemType.SUBCATEGORY:
            if cat_slug:
                parent_slug, parent_id, parent_display = cat_slug, cat_id, parent_name
            _id = _build_id(t, slug, parent_slug)
            out: Dict[str, object] = {
                "id": _id,
                "type": t.value,
                "name": name,
                "slug": slug,
                "url": url,
                "parent": parent_display,
            }
            if parent_slug:
                out["parent_slug"] = parent_slug
            if parent_id:
                out["parent_id"] = parent_id
            normalized.append(out)
            continue

        # ALL_IN: prefer subcategory parent when identifiable
        if t == ItemType.ALL_IN:
            # Case A: incoming parent is already a subcategory name (parser gave subcontext)
            if cat_slug:
                # Try to interpret parent_name as subcategory under cat
                sub_by_name = subcategories_by_name.get((cat_slug, parent_name.lower())) if parent_name else None
                if sub_by_name:
                    sub_name, sub_slug, sub_id = sub_by_name
                    parent_display, parent_slug, parent_id = sub_name, sub_slug, sub_id
                else:
                    # Case B: infer subcategory from "All in … X" label
                    label, target_slug = normalize_all_in_name(name)
                    hit = subcategories_by_name.get((cat_slug, label.lower())) or \
                          subcategories_by_slug.get((cat_slug, target_slug))
                    if hit:
                        sub_name, sub_slug, sub_id = hit
                        parent_display, parent_slug, parent_id = sub_name, sub_slug, sub_id

            # Case C: fall back to category parent if no subcategory match
            if not parent_slug and cat_slug:
                parent_display, parent_slug, parent_id = parent_name, cat_slug, cat_id

            _id = _build_id(t, slug, parent_slug)
            out: Dict[str, object] = {
                "id": _id,
                "type": t.value,
                "name": name,
                "slug": slug,
                "url": url,
                "parent": parent_display,
            }
            if parent_slug:
                out["parent_slug"] = parent_slug
            if parent_id:
                out["parent_id"] = parent_id
            normalized.append(out)
            continue

        # Default (should not happen): treat as leaf with unresolved parent
        _id = _build_id(t, slug, parent_slug)
        out = {
            "id": _id,
            "type": t.value,
            "name": name,
            "slug": slug,
            "url": url,
        }
        if parent_name:
            out["parent"] = parent_name
        normalized.append(out)

    return normalized

__all__ = ["attach_lineage"]

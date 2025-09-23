"""Index helpers for normalized taxonomy items.

Input shape (from normalize.lineage.attach_lineage):
{
  "id": str,
  "parent_id": str | None,
  "type": str,              # "category" | "subcategory" | "all_in"
  "name": str,
  "slug": str,
  "url": str,
  "parent": str | None,
  "parent_slug": str | None
}

Provided helpers:
- build_by_category(items) -> dict
    {
      category_slug: {
         "category": <category item dict>,
         "children": [<child items with parent_slug == category_slug>]
      },
      ...
    }
  Categories without children still appear with an empty list.

- build_by_slug(items) -> dict
    {
      slug: [<all items with this slug in encounter order>],
      ...
    }

Both helpers are stable with respect to input order.
"""
from __future__ import annotations

from typing import Dict, List, Iterable


def build_by_category(items: Iterable[dict]) -> Dict[str, dict]:
    """Group items under their category slug.

    Returns a mapping of category_slug -> {category: item|None, children: list}.
    If a category record is missing in `items` but children reference it, the
    entry is still created with category=None.
    """
    out: Dict[str, dict] = {}

    # First pass: ensure buckets for each referenced category
    for it in items or []:
        cat_slug = it.get("slug") if it.get("type") == "category" else it.get("parent_slug")
        if not cat_slug:
            continue
        out.setdefault(cat_slug, {"category": None, "children": []})

    # Second pass: assign category and children
    for it in items or []:
        t = (it.get("type") or "").lower()
        if t == "category":
            bucket = out.setdefault(it.get("slug", ""), {"category": None, "children": []})
            bucket["category"] = it
        else:
            cat_slug = it.get("parent_slug")
            if not cat_slug:
                # orphan (no parent); skip from grouping
                continue
            bucket = out.setdefault(cat_slug, {"category": None, "children": []})
            bucket["children"].append(it)

    return out


def build_by_slug(items: Iterable[dict]) -> Dict[str, List[dict]]:
    """Index items by their own slug (encounter order)."""
    idx: Dict[str, List[dict]] = {}
    for it in items or []:
        slug = it.get("slug")
        if not slug:
            continue
        idx.setdefault(slug, []).append(it)
    return idx


__all__ = ["build_by_category", "build_by_slug"]

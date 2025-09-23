"""Dedupe utilities for normalized taxonomy items.

Rule: drop duplicates by the compound key (type, slug, parent_slug).
We keep the *first* instance seen, but will opportunistically backfill
missing lightweight fields (`url`, `name`) from later duplicates.

Expected input shape (from normalize.lineage.attach_lineage):
{
  "id": str,
  "parent_id": str | None,
  "type": str,              # "category" | "subcategory" | "all_in"
  "name": str,
  "slug": str,
  "url": str,               # may be "" if unknown
  "parent": str | None,
  "parent_slug": str | None
}

Public API
----------
- dedupe_items(items: Iterable[dict]) -> list[dict]
"""
from __future__ import annotations

from typing import Dict, Iterable, List, Tuple

_KEY_FIELDS = ("type", "slug", "parent_slug")


def _key(d: dict) -> Tuple[str, str, str | None]:
    return (
        (d.get("type") or "").lower(),
        (d.get("slug") or "").lower(),
        (d.get("parent_slug") or None),
    )


def dedupe_items(items: Iterable[dict]) -> List[dict]:
    """Drop duplicates by (type, slug, parent_slug).

    First occurrence wins; later duplicates are ignored, except we will
    backfill empty `url` or `name` on the kept record if the duplicate has
    those fields populated.
    """
    seen: Dict[Tuple[str, str, str | None], dict] = {}
    order: List[Tuple[str, str, str | None]] = []

    for it in items or []:
        k = _key(it)
        if k not in seen:
            seen[k] = dict(it)  # shallow copy to avoid mutating caller's list
            order.append(k)
            continue
        # Backfill on duplicate
        kept = seen[k]
        if not kept.get("url") and it.get("url"):
            kept["url"] = it["url"]
        if not kept.get("name") and it.get("name"):
            kept["name"] = it["name"]
        # prefer earliest parent_id but keep a non-empty one if missing
        if kept.get("parent_id") is None and it.get("parent_id") is not None:
            kept["parent_id"] = it["parent_id"]

    return [seen[k] for k in order]


__all__ = ["dedupe_items"]

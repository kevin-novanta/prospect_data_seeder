"""Dedupe utilities for normalized taxonomy items.

Rules
-----
- Default key: (type, slug, parent_slug)
- Special for ALL_IN:
  * Prefer (type, parent_id) if parent_id exists
  * Else (type, parent_slug, target_slug) where target_slug is derived from
    the display text (e.g., "All in Email Marketing" -> "email-marketing")

Winner selection (when duplicates share the same key):
- Prefer entry with an absolute URL (http/https) over relative/empty
- If tie, prefer longer non-empty name (more informative)
- If still tie, keep first seen (stable)

We still opportunistically backfill missing lightweight fields (`url`, `name`)
from the loser into the kept record if those are empty.

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

from ..normalize.types import normalize_all_in_name

_KEY_FIELDS = ("type", "slug", "parent_slug")


def _is_abs_url(u: str | None) -> bool:
    if not u:
        return False
    s = u.strip().lower()
    return s.startswith("http://") or s.startswith("https://")


def _all_in_key(d: dict) -> Tuple[str, str, str | None]:
    """Key for ALL_IN items.

    Priority:
      1) ("all_in", parent_id, "") if parent_id present
      2) ("all_in", parent_slug, target_slug) where target_slug is derived from name
    """
    parent_id = d.get("parent_id")
    if parent_id:
        return ("all_in", str(parent_id), "")

    parent_slug = d.get("parent_slug") or None
    # Derive target_slug from the display text (strip the "All in" prefix)
    name = d.get("name") or ""
    _, target_slug = normalize_all_in_name(name)
    return ("all_in", parent_slug, target_slug)


def _default_key(d: dict) -> Tuple[str, str, str | None]:
    return (
        (d.get("type") or "").lower(),
        (d.get("slug") or "").lower(),
        (d.get("parent_slug") or None),
    )


def _key(d: dict) -> Tuple[str, str, str | None]:
    t = (d.get("type") or "").lower()
    if t == "all_in":
        return _all_in_key(d)
    return _default_key(d)


def _score(record: dict) -> Tuple[int, int]:
    """Return a tuple used to pick a winner among duplicates.

    Higher is better. First component = URL quality, second = name length.
    """
    url_score = 2 if _is_abs_url(record.get("url")) else (1 if record.get("url") else 0)
    name_len = len((record.get("name") or "").strip())
    return (url_score, name_len)


def dedupe_items(items: Iterable[dict]) -> List[dict]:
    """Drop duplicates by key with specialized ALL_IN handling.

    First occurrence wins unless a later duplicate has a strictly better
    score according to `_score`. Regardless, we backfill empty `url`/`name`
    (and `parent_id` if missing) on the kept record from the candidate.
    """
    seen: Dict[Tuple[str, str, str | None], dict] = {}
    order: List[Tuple[str, str, str | None]] = []

    for it in items or []:
        k = _key(it)
        if k not in seen:
            seen[k] = dict(it)  # shallow copy to avoid mutating caller's list
            order.append(k)
            continue

        kept = seen[k]
        # Decide if the newcomer is a better representative
        if _score(it) > _score(kept):
            # Before replacing, carry forward any fields from kept that the new one lacks
            new = dict(it)
            if not new.get("name") and kept.get("name"):
                new["name"] = kept["name"]
            if not new.get("url") and kept.get("url"):
                new["url"] = kept["url"]
            if new.get("parent_id") is None and kept.get("parent_id") is not None:
                new["parent_id"] = kept["parent_id"]
            seen[k] = new
        else:
            # Keep existing, but opportunistically backfill
            if not kept.get("url") and it.get("url"):
                kept["url"] = it["url"]
            if not kept.get("name") and it.get("name"):
                kept["name"] = it["name"]
            if kept.get("parent_id") is None and it.get("parent_id") is not None:
                kept["parent_id"] = it["parent_id"]

    return [seen[k] for k in order]


__all__ = ["dedupe_items"]



"""choices.py — build and write a compact choices.json for UIs.

Goal
----
Produce a small structure the app can load to present selectable category
options without scanning the full taxonomy. Includes top-level categories
and their subcategory lists, and can optionally include "all_in" entries.

**Option A behavior (resilient)**
If explicit category records are missing, synthesize categories by grouping
subcategories on their recorded parent/parent_slug so choices.json is never empty.

Public API
----------
- build_choices(items_or_doc, include_all_in=False) -> dict
- write_choices(items_or_doc, out_path="./data/choices.json", include_all_in=False) -> Path

Input can be either:
  • the normalized items list from normalize.lineage.attach_lineage, OR
  • a full taxonomy document that has {"items":[...]}.
"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Iterable, Any, Tuple
from collections import defaultdict

# We keep this import for the "explicit category present" path,
# but the synthesis path does not depend on it.
from ..assemble_validate.index import build_by_category


# ---------- helpers ----------

def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ensure_dir(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


def _atomic_write_text(path: Path, text: str, *, mode: int = 0o644) -> None:
    _ensure_dir(path)
    tmp = None
    dir_fd = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=str(path.parent), delete=False) as f:
            tmp = Path(f.name)
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        dir_fd = os.open(str(path.parent), os.O_DIRECTORY)
        try:
            os.replace(str(tmp), str(path))
            os.fchmod(os.open(str(path), os.O_RDONLY), mode)
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except Exception:
        if tmp and tmp.exists():
            try:
                tmp.unlink()
            except Exception:
                pass
        raise


def _ensure_items(items_or_doc: Any) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Accept either a doc with 'items' or a plain list of items."""
    if isinstance(items_or_doc, dict) and isinstance(items_or_doc.get("items"), list):
        return list(items_or_doc["items"]), items_or_doc
    if isinstance(items_or_doc, list):
        return list(items_or_doc), {}
    raise TypeError("build_choices/write_choices expect items list or {'items': [...]} document")


def _by_type(items: Iterable[Dict[str, Any]]):
    tmap = defaultdict(list)
    for it in items:
        tmap[(it.get("type") or "").lower()].append(it)
    return tmap


def _index_by_slug(items: Iterable[Dict[str, Any]]):
    return {it.get("slug"): it for it in items if it.get("slug")}


# ---------- core API ----------

def build_choices(items_or_doc: Any, *, include_all_in: bool = False) -> Dict[str, Any]:
    """Build a compact choices mapping from normalized items.

    Output shape:
    {
      "generated_at": "2025-01-01T00:00:00Z",
      "version": "1.0",
      "categories": [
        {"name": str, "slug": str, "url": str, "subs": [
            {"name": str, "slug": str, "url": str, "all_in": [ ... ]?},
            ...
        ]},
        ...
      ]
    }
    """
    items, doc = _ensure_items(items_or_doc)

    # Attempt the explicit-category path first (preserves encounter order from index)
    idx = build_by_category(items)
    categories_out: List[Dict[str, Any]] = []

    for cat_slug, bucket in idx.items():
        cat = bucket.get("category")
        if not cat:
            # orphan bucket without an explicit category record; will be handled by synthesis below
            continue
        subs_out: List[Dict[str, Any]] = []
        for child in bucket.get("children", []):
            t = (child.get("type") or "").lower()
            if t == "subcategory" or (include_all_in and t == "all_in"):
                entry = {
                    "name": child.get("name", ""),
                    "slug": child.get("slug", ""),
                    "url": child.get("url", ""),
                }
                if include_all_in and t == "subcategory":
                    # attach any "all_in" children recorded under this sub (if present in items)
                    pass  # optional enhancement later
                subs_out.append(entry)
        categories_out.append({
            "name": cat.get("name", ""),
            "slug": cat.get("slug", cat_slug),
            "url": cat.get("url", ""),
            "subs": subs_out,
        })

    # If that produced no categories (or very few), synthesize from subcategories
    if not categories_out:
        tmap = _by_type(items)
        subs = tmap.get("subcategory", [])
        allins = tmap.get("all_in", [])
        all_in_by_parent = defaultdict(list)
        for a in allins:
            pslug = a.get("parent_slug")
            if pslug:
                all_in_by_parent[pslug].append(a)

        # group subs by parent_slug (so we can create synthetic categories)
        subs_by_parent = defaultdict(list)
        for s in subs:
            subs_by_parent[s.get("parent_slug")].append(s)

        for parent_slug, grouped_subs in subs_by_parent.items():
            if not grouped_subs:
                continue
            parent_name = grouped_subs[0].get("parent") or "Uncategorized"
            cat_entry = {
                "name": parent_name,
                "slug": parent_slug or "uncategorized",
                "url": "",  # unknown
                "subs": [],
            }
            for s in grouped_subs:
                sub_entry = {
                    "name": s.get("name", ""),
                    "slug": s.get("slug", ""),
                    "url": s.get("url", ""),
                }
                if include_all_in:
                    sub_entry["all_in"] = [
                        {"name": a.get("name", ""), "slug": a.get("slug", ""), "url": a.get("url", "")}
                        for a in all_in_by_parent.get(s.get("slug"), [])
                    ]
                cat_entry["subs"].append(sub_entry)

            categories_out.append(cat_entry)

    # Build payload
    payload = {
        "generated_at": _utc_now_iso(),
        "version": doc.get("version", "1.0") if isinstance(doc, dict) else "1.0",
        "categories": categories_out,
    }
    return payload


def write_choices(items_or_doc: Any, out_path: str = "./data/choices.json", *, include_all_in: bool = False, pretty: bool = True) -> Path:
    """Write `choices.json` atomically.

    `items_or_doc` can be a normalized items list or a full taxonomy document.
    """
    payload = build_choices(items_or_doc, include_all_in=include_all_in)

    path = Path(out_path).expanduser().resolve()
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n" if pretty else json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    _atomic_write_text(path, text)
    return path


__all__ = ["build_choices", "write_choices"]
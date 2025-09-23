"""Directory page parser

Turns the Clutch directory-like HTML into a flat list of raw items:
    {"type": "category"|"subcategory"|"all_in",
     "name": str,
     "href": str | None,
     "parent": str | None}

This is intentionally schema-light (raw) so later phases can normalize and
validate into your final taxonomy schema.
"""
from __future__ import annotations

from typing import List, Dict, Optional
from bs4 import BeautifulSoup, Tag
import re

from .selectors import get_selectors, SelectorSet


def _clean_text(s: Optional[str]) -> str:
    if not s:
        return ""
    return " ".join(s.split()).strip()


def _first_match_text(node: Tag, css_list: list[str]) -> str:
    for css in css_list:
        hit = node.select_one(css)
        if hit and (txt := _clean_text(hit.get_text(" ", strip=True))):
            return txt
    return ""


def _find_blocks(soup: BeautifulSoup, sels: SelectorSet) -> list[Tag]:
    for css in sels.CATEGORY_BLOCKS:
        blocks = soup.select(css)
        if blocks:
            return blocks
    return []


def _iter_subcategory_items(block: Tag, sels: SelectorSet) -> list[Tag]:
    for css in sels.SUBCATEGORY_ITEMS:
        items = block.select(css)
        if items:
            return items
    return []


def _find_link(node: Tag, css_list: list[str]) -> Optional[Tag]:
    for css in css_list:
        a = node.select_one(css)
        if a and a.has_attr("href"):
            return a
    return None


def _iter_all_in_candidates(block: Tag, sels: SelectorSet) -> list[Tag]:
    """Yield anchors in a block that are likely All in … links, using attribute selectors first.
    Text filtering and URL hints are applied by the caller.
    """
    anchors: list[Tag] = []
    for css in getattr(sels, "ALL_IN_SELECTORS", []) or []:
        hits = block.select(css)
        if hits:
            anchors.extend([a for a in hits if isinstance(a, Tag) and a.has_attr("href")])
    # de-dupe by id(href) within the block
    seen = set()
    uniq: list[Tag] = []
    for a in anchors:
        key = a.get("href", "").strip()
        if key and key not in seen:
            seen.add(key)
            uniq.append(a)
    return uniq


def _is_all_in_anchor(a: Tag, sels: SelectorSet, category_name: str) -> bool:
    """Heuristics to decide if an anchor represents an All in … link.
    Rules:
      1) Text starts with/contains 'All in' (case-insensitive)
      2) aria-label/title contain 'All in'
      3) href looks like a directory root according to ROOT_HREF_HINTS
    """
    hint = (sels.ALL_IN_TEXT_HINT or "All in").lower()
    txt = _clean_text(a.get_text(" ", strip=True)).lower()
    if hint in txt:
        return True

    # attribute-based
    aria = (a.get("aria-label") or "").lower()
    title = (a.get("title") or "").lower()
    if hint in aria or hint in title:
        return True

    # URL based
    href = (a.get("href") or "").strip()
    for frag in (getattr(sels, "ROOT_HREF_HINTS", []) or []):
        if frag and frag in href:
            return True
    return False


def parse_directory(html: str) -> List[Dict]:
    """Parse a directory page into raw items.

    Returns a flat list in encounter order. Categories are emitted first,
    followed by their subcategories and an optional all_in link.
    """
    items: List[Dict] = []
    if not html or "<" not in html:
        return items

    soup = BeautifulSoup(html, "html.parser")
    sels_map = get_selectors()

    # Try selector sets in order until we find blocks
    blocks: list[Tag] = []
    chosen: Optional[SelectorSet] = None
    for _, sels in sels_map.items():
        blocks = _find_blocks(soup, sels)
        if blocks:
            chosen = sels
            break
    if not blocks or not chosen:
        return items

    for block in blocks:
        cat_name = _first_match_text(block, chosen.CATEGORY_TITLE)
        if not cat_name:
            # Skip blocks without a meaningful title
            continue

        items.append({
            "type": "category",
            "name": cat_name,
            "href": None,
            "parent": None,
        })

        # Subcategories
        sub_items = _iter_subcategory_items(block, chosen)
        for node in sub_items:
            a = _find_link(node, chosen.SUBCATEGORY_LINK)
            if not a:
                continue
            name = _clean_text(a.get_text(" ", strip=True))
            href = a.get("href", None)
            if not name:
                continue
            items.append({
                "type": "subcategory",
                "name": name,
                "href": href,
                "parent": cat_name,
            })

        # All-in link(s) (optional per category)
        emitted = set()
        candidates = _iter_all_in_candidates(block, chosen)
        picked: list[Tag] = [a for a in candidates if _is_all_in_anchor(a, chosen, cat_name)]

        # Fallback: URL-pattern detection (root-like hrefs inside this block)
        if not picked:
            for a in block.select("a[href]"):
                if not isinstance(a, Tag) or not a.has_attr("href"):
                    continue
                href = (a.get("href") or "").strip()
                for frag in (getattr(chosen, "ROOT_HREF_HINTS", []) or []):
                    if frag and frag in href:
                        picked.append(a)
                        break
                if picked:
                    break

        for a in picked:
            href = a.get("href", None)
            name_txt = _clean_text(a.get_text(" ", strip=True)) or f"All in {cat_name}"
            key = (href or "") + "|" + name_txt
            if key in emitted:
                continue
            emitted.add(key)
            items.append({
                "type": "all_in",
                "name": name_txt,
                "href": href,
                "parent": cat_name,
            })

    return items


__all__ = ["parse_directory"]
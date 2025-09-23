

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


def _find_all_in(block: Tag, sels: SelectorSet) -> Optional[Tag]:
    hint = sels.ALL_IN_TEXT_HINT.lower()
    for css in sels.ALL_IN_ANCHOR_SCAN:
        for a in block.select(css):
            if not a or not a.has_attr("href"):
                continue
            txt = _clean_text(a.get_text(" ", strip=True)).lower()
            if hint in txt:
                return a
    return None


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

        # All-in link (optional per category)
        all_in = _find_all_in(block, chosen)
        if all_in is not None:
            items.append({
                "type": "all_in",
                "name": _clean_text(all_in.get_text(" ", strip=True)),
                "href": all_in.get("href", None),
                "parent": cat_name,
            })

    return items


__all__ = ["parse_directory"]
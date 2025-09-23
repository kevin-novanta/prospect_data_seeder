"""Selectors for directory parsing (primary + fallbacks).

We keep this module *data-only* so the parser can iterate over ordered
candidates and stop on first match. Avoid importing BeautifulSoup here.

The parser should:
  1) iterate CATEGORY_BLOCKS until it finds blocks (>0)
  2) within each block, get CATEGORY_TITLE (first non-empty text)
  3) iterate SUBCATEGORY_ITEMS list; for each item, find SUBCATEGORY_LINK
  4) detect an "All in …" anchor by text (no :contains in CSS)
  5) detect "All in" anchors by attribute selectors (ALL_IN_SELECTORS)
  6) detect directory root links by href substrings (ROOT_HREF_HINTS)

Note: CSS :contains() is not supported by bs4, so we expose ALL_IN_TEXT_HINT
for the parser to filter anchors by text. Attribute and URL heuristics are
also provided via ALL_IN_SELECTORS and ROOT_HREF_HINTS.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict


@dataclass(frozen=True)
class SelectorSet:
    # Top-level blocks that group a category and its subcategories
    CATEGORY_BLOCKS: List[str]
    # Title/heading inside a category block
    CATEGORY_TITLE: List[str]
    # A node representing a single subcategory row/item inside a block
    SUBCATEGORY_ITEMS: List[str]
    # Anchor element for the subcategory link within a subcategory item
    SUBCATEGORY_LINK: List[str]
    # Anchors to scan for an "All in …" link (filter by text in parser)
    ALL_IN_ANCHOR_SCAN: List[str]
    # Lowercase text hint to identify the All in link (parser uses contains)
    ALL_IN_TEXT_HINT: str = "all in"
    # Anchors likely representing All in; attribute-targeted
    ALL_IN_SELECTORS: List[str] = ()
    # Href substrings that indicate directory roots
    ROOT_HREF_HINTS: List[str] = ()


# ---- Primary + fallbacks ----
PRIMARY = SelectorSet(
    CATEGORY_BLOCKS=[
        # Common content grid / sections
        'section.category',
        'section.directory-category',
        'div.directory-categories > section',
        '[data-test="category-block"]',
        # generic fallbacks
        'div.category',
        'li.category',
    ],
    CATEGORY_TITLE=[
        '.category--title',
        '.category-title',
        'header h2',
        'h2',
        'h3',
    ],
    SUBCATEGORY_ITEMS=[
        'ul.subcategories > li',
        'div.subcategories > div',
        'ul > li',
        '.subcategory',
        '.field--item',
        '.list-item',
    ],
    SUBCATEGORY_LINK=[
        'a.subcategory-link[href]',
        'a[href].subcategory',
        'a[href]',
    ],
    ALL_IN_ANCHOR_SCAN=[
        'a[href].all-in',
        'a[href][data-test="all-in"]',
        'a[href]',
    ],
    ALL_IN_SELECTORS=[
        'a[href][class*="all-in"]',
        'a[href][data-test="all-in"]',
        'a[href][aria-label*="All in"]',
        'a[href][title*="All in"]',
        'a[href]'  # last-resort scan; parser will filter by text/URL
    ],
    ROOT_HREF_HINTS=['/directory/', '/categories', '/category/'],
)

# Optional alternative that is more list-based (e.g., older markup)
ALT_LISTY = SelectorSet(
    CATEGORY_BLOCKS=[
        'ul.categories > li',
        'div.categories > div',
        'section.categories > div',
    ],
    CATEGORY_TITLE=[
        'h2', 'h3', '.title', 'header .title'
    ],
    SUBCATEGORY_ITEMS=[
        'ul > li', '.items > .item', '.links > li'
    ],
    SUBCATEGORY_LINK=[
        'a[href]', 'a.link'
    ],
    ALL_IN_ANCHOR_SCAN=[
        'a[href]'
    ],
    ALL_IN_SELECTORS=[
        'a[href][class*="all-in"]',
        'a[href][data-test="all-in"]',
        'a[href]'
    ],
    ROOT_HREF_HINTS=['/directory/', '/categories', '/category/'],
)

# Fallback extremely generic selectors (last resort)
GENERIC = SelectorSet(
    CATEGORY_BLOCKS=['section', 'div', 'li'],
    CATEGORY_TITLE=['h2', 'h3', 'strong', '.title'],
    SUBCATEGORY_ITEMS=['li', 'div', '.item'],
    SUBCATEGORY_LINK=['a[href]'],
    ALL_IN_ANCHOR_SCAN=['a[href]'],
    ALL_IN_SELECTORS=['a[href]'],
    ROOT_HREF_HINTS=['/directory/', '/categories', '/category/'],
)


def get_selectors() -> Dict[str, SelectorSet]:
    """Return selector presets in the order the parser should try them."""
    return {
        'primary': PRIMARY,
        'alt_listy': ALT_LISTY,
        'generic': GENERIC,
    }


__all__ = [
    'SelectorSet',
    'PRIMARY',
    'ALT_LISTY',
    'GENERIC',
    'get_selectors',
]

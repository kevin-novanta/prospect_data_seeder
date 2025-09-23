import json
from pathlib import Path
from collections import Counter

import pytest

from tools.taxonomy_builder.pipeline_core.parse.directory_parser import parse_directory


FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_HTML = FIXTURES_DIR / "clutch_directory_sample.html"
BLOCK_HTML = FIXTURES_DIR / "clutch_category_block.html"


@pytest.mark.parametrize("fixture_path", [SAMPLE_HTML, BLOCK_HTML])
def test_counts_basic(fixture_path: Path):
    """Parser should emit at least one category and one subcategory from fixtures."""
    html = fixture_path.read_text(encoding="utf-8")
    items = parse_directory(html)

    assert isinstance(items, list) and items, "parse_directory must return non-empty list"

    counts = Counter((it.get("type") or "").lower() for it in items)
    # Allow either or both fixtures; require basic signal
    assert counts.get("category", 0) >= 1, f"expected >=1 category in {fixture_path.name}, got {counts}"
    assert counts.get("subcategory", 0) >= 1, f"expected >=1 subcategory in {fixture_path.name}, got {counts}"

    # If any all_in are present, their label should contain 'All in'
    for it in items:
        if (it.get("type") or "").lower() == "all_in":
            assert "all in" in (it.get("name") or "").lower()


def test_presence_of_key_labels():
    """Spot-check a few expected labels commonly present on the directory page."""
    html = SAMPLE_HTML.read_text(encoding="utf-8")
    items = parse_directory(html)

    names = { (it.get("type"), (it.get("name") or "").strip()) for it in items }

    # Category we expect to see at least once in sample
    assert ("category", "Advertising & Marketing") in names or ("category", "Advertising and Marketing") in names

    # A few subcategories we often rely on in downstream logic
    expected_subs = {"SEO", "Social Media Marketing", "Email Marketing"}
    present_subs = { n for (t, n) in names if t == "subcategory" }

    missing = expected_subs - present_subs
    assert not missing, f"missing expected subcategories: {missing}"

import json
from pathlib import Path

import pytest

from tools.taxonomy_builder.pipeline_core.parse.directory_parser import parse_directory
from tools.taxonomy_builder.pipeline_core.normalize.lineage import attach_lineage
from tools.taxonomy_builder.pipeline_core.output.writer import write_json


FIXTURE_HTML = Path("tools/taxonomy_builder/data/clutch_directory.html")


@pytest.mark.smoke
@pytest.mark.skipif(not FIXTURE_HTML.exists(), reason="fixture HTML not present")
def test_smoke_fixture_writes_non_empty_taxonomy(tmp_path: Path):
    html = FIXTURE_HTML.read_text(encoding="utf-8")

    # parse -> normalize/attach lineage
    raw = parse_directory(html)
    items = attach_lineage(raw, base_url="https://clutch.co")

    # write minimal doc to a temp location
    out_taxonomy = tmp_path / "taxonomy.json"
    doc = {
        "version": "0.1.0",
        "source_page": "fixture:/clutch_directory.html",
        "collected_at": "2025-01-01T00:00:00Z",
        "items": items,
    }
    write_json(doc, str(out_taxonomy))

    # assert file exists and contains non-empty items
    assert out_taxonomy.exists() and out_taxonomy.stat().st_size > 0
    parsed = json.loads(out_taxonomy.read_text(encoding="utf-8"))
    assert isinstance(parsed.get("items"), list) and len(parsed["items"]) > 0

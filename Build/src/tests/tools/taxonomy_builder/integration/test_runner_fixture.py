import json
from pathlib import Path
from collections import Counter

import pytest

from tools.taxonomy_builder.runtime_delivery.runner import run_build
from tools.taxonomy_builder.pipeline_core.assemble_validate.validate import validate_taxonomy


FIXTURE_HTML = Path("tools/taxonomy_builder/data/clutch_directory.html")


@pytest.mark.integration
@pytest.mark.skipif(not FIXTURE_HTML.exists(), reason="fixture HTML not present")
def test_runner_end_to_end_with_fixture(tmp_path: Path):
    """Run the full pipeline on the local fixture and assert outputs are sane."""
    out_taxonomy = tmp_path / "taxonomy.json"

    # Run the pipeline (dev profile; fixture mode inside runner)
    code = run_build(
        html_path=str(FIXTURE_HTML),
        out_path=str(out_taxonomy),
        profile="dev",
        include_all_in=False,
    )
    assert code == 0, "runner should exit with code 0"

    # Taxonomy file exists and is non-empty
    assert out_taxonomy.exists() and out_taxonomy.stat().st_size > 0

    # Validate against schema
    doc = json.loads(out_taxonomy.read_text(encoding="utf-8"))
    validate_taxonomy(doc)

    # Basic shape & counts
    assert isinstance(doc.get("items"), list) and len(doc["items"]) >= 1
    counts = Counter((it.get("type") or "").lower() for it in doc["items"])
    assert counts.get("subcategory", 0) >= 1

    # Choices written alongside taxonomy
    out_choices = out_taxonomy.with_name("choices.json")
    assert out_choices.exists() and out_choices.stat().st_size > 0
    choices = json.loads(out_choices.read_text(encoding="utf-8"))
    cats = choices.get("categories", [])
    assert isinstance(cats, list) and len(cats) >= 1


@pytest.mark.integration
@pytest.mark.skipif(not FIXTURE_HTML.exists(), reason="fixture HTML not present")
def test_runner_writes_provenance(tmp_path: Path):
    out_taxonomy = tmp_path / "taxonomy.json"
    code = run_build(
        html_path=str(FIXTURE_HTML),
        out_path=str(out_taxonomy),
        profile="dev",
        include_all_in=False,
    )
    assert code == 0

    doc = json.loads(out_taxonomy.read_text(encoding="utf-8"))
    prov = doc.get("provenance") or {}
    # Minimal provenance presence (keys may vary by your implementation)
    assert prov.get("run_id")
    assert prov.get("parser_version")
    assert prov.get("profile") == "dev"

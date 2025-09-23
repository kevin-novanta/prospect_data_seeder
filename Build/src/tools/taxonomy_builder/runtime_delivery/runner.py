from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from collections import Counter

from ..config import load as load_config
from ..logging_setup import get_logger

# Platform & Ops
from ..platform_ops import governance, observability

# Fetch & Parse & Normalize
from ..pipeline_core.fetch.client import get_text
from ..pipeline_core.parse.directory_parser import parse_directory
from ..pipeline_core.normalize.lineage import attach_lineage

# Assemble & Validate
from ..pipeline_core.assemble_validate.dedupe import dedupe_items
from ..pipeline_core.assemble_validate.validate import validate_taxonomy

# Output
from ..pipeline_core.output.writer import write_taxonomy
from ..pipeline_core.output.choices import write_choices
from ..pipeline_core.output.provenance import build_provenance, attach_provenance
from ..pipeline_core.output.deadletter import append_deadletter


LOGGER = get_logger(__name__)
PARSER_VERSION = "0.1.0"
DEFAULT_SOURCE_PAGE = "https://clutch.co/categories"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_build(*, html_path: str, out_path: str = "./data/taxonomy.json", profile: str = "dev", include_all_in: Optional[bool] = None) -> int:
    """Run the taxonomy build pipeline and return an exit code (0 success, 2 failure)."""
    cfg = load_config(profile=profile)
    include_all = cfg.INCLUDE_ALL_IN_IN_CHOICES if include_all_in is None else bool(include_all_in)
    LOGGER.info({
        "event": "runner.start",
        "profile": profile,
        "out_path": str(out_path),
        "html_path": str(html_path),
    })

    with observability.time_block("total_run"):
        try:
            # 1) Governance / policy (stubbed for fixture mode)
            robots_on = governance.robots_policy(profile)
            observability.inc("robots_policy_checked", enabled=int(robots_on))

            # 2) Fetch HTML (fixture-only for Phase 8)
            status, html = get_text("file://fixture", use_fixture=True, fixture_path=html_path)
            if status != 200 or not html:
                LOGGER.error({"event": "fetch.error", "status": status, "fixture_path": html_path})
                append_deadletter({
                    "stage": "fetch",
                    "status": status,
                    "fixture_path": html_path,
                })
                return 2
            observability.inc("fetch_ok")

            # 3) Parse → Normalize → Dedupe
            raw = parse_directory(html)
            counts = Counter(x.get("type") for x in raw if isinstance(x, dict))
            observability.inc("found_categories", count=counts.get("category", 0))
            observability.inc("found_subcategories", count=counts.get("subcategory", 0))
            observability.inc("found_all_in", count=counts.get("all_in", 0))
            observability.inc("parsed_items", count=len(raw))

            items = attach_lineage(raw, base_url=DEFAULT_SOURCE_PAGE.replace("/categories", ""))
            items = dedupe_items(items)
            observability.inc("normalized_items", count=len(items))
            observability.inc("deduped_items", count=len(items))

            # 4) Assemble document
            doc = {
                "version": PARSER_VERSION,
                "source_page": DEFAULT_SOURCE_PAGE,
                "collected_at": _utc_now_iso(),
                "items": items,
            }

            # 5) Validate against schema
            try:
                validate_taxonomy(doc)
            except Exception as e:  # ValueError/FileNotFoundError/etc.
                LOGGER.error({"event": "validate.error", "error": str(e)})
                append_deadletter({
                    "stage": "validate",
                    "error": str(e),
                })
                return 2

            # 6) Stamp provenance
            prov = build_provenance(
                source_page=doc["source_page"],
                parser_version=PARSER_VERSION,
                profile=profile,
                extra={"schema": "taxonomy.schema.json"},
            )
            attach_provenance(doc, prov)

            # 7) Write outputs
            final_path = write_taxonomy(doc, out_path)
            # choices.json lives alongside taxonomy.json
            choices_path = str(Path(out_path).with_name("choices.json"))
            write_choices(items, choices_path, include_all_in=include_all)

            LOGGER.info({
                "event": "runner.success",
                "taxonomy_path": str(final_path),
                "choices_path": choices_path,
                "count": len(items),
                "type_counts": {
                    "category": counts.get("category", 0),
                    "subcategory": counts.get("subcategory", 0),
                    "all_in": counts.get("all_in", 0),
                },
            })
            return 0

        finally:
            # Always flush metrics at end
            metrics = observability.flush_metrics()
            LOGGER.info({"event": "metrics.flush", **metrics})


__all__ = ["run_build"]

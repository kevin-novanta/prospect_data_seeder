"""Provenance helpers for taxonomy output.

This module provides a tiny, dependency-free way to stamp run metadata onto
an output document. Keep it lightweight so it can run in CI and in containers
without git installed or network access.

Public API
----------
- build_provenance(source_page: str, *, parser_version: str,
                   profile: str | None = None,
                   extra: dict | None = None) -> dict

- attach_provenance(doc: dict, prov: dict) -> dict
  (adds the provenance under key "provenance" and returns `doc` for chaining)

Notes
-----
- We record a monotonic `run_id` (uuid4), UTC timestamp, python/runtime info,
  and best-effort git SHA if available.
- Callers typically set `doc["version"]`, `doc["source_page"]`, `doc["collected_at"]`
  separately; provenance complements those top-level fields.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import os
import platform
import subprocess
import sys
import uuid
from typing import Optional, Dict, Any


@dataclass(frozen=True)
class RuntimeInfo:
    python: str
    impl: str
    platform: str
    profile: Optional[str]
    git_sha: Optional[str]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _git_sha() -> Optional[str]:
    """Return short git SHA if available, else None.

    Best-effort: we do not error if git is missing or repo not present.
    """
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL
        ).decode().strip()
        return sha or None
    except Exception:
        return None


def _runtime(profile: Optional[str]) -> RuntimeInfo:
    return RuntimeInfo(
        python=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        impl=platform.python_implementation(),
        platform=platform.platform(aliased=True, terse=False),
        profile=profile,
        git_sha=_git_sha(),
    )


def build_provenance(
    source_page: str,
    *,
    parser_version: str,
    profile: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a provenance record for this run.

    Parameters
    ----------
    source_page: str
        Canonical page the taxonomy was sourced from (should match doc["source_page"]).
    parser_version: str
        Semantic version of the parser/normalizer pipeline (e.g., "0.1.0").
    profile: Optional[str]
        Runtime profile ("dev", "ci", "prod") if known.
    extra: Optional[dict]
        Caller-specified key/values to merge under `extra`.
    """
    run_id = str(uuid.uuid4())
    info = _runtime(profile)
    prov: Dict[str, Any] = {
        "run_id": run_id,
        "ts": _utc_now_iso(),
        "source_page": source_page,
        "parser_version": parser_version,
        "runtime": asdict(info),
    }
    if extra:
        prov["extra"] = dict(extra)
    return prov


def attach_provenance(doc: Dict[str, Any], prov: Dict[str, Any]) -> Dict[str, Any]:
    """Attach provenance under `provenance` key and return the doc for chaining."""
    if not isinstance(doc, dict):
        raise TypeError("doc must be a dict")
    doc["provenance"] = prov
    return doc


__all__ = ["build_provenance", "attach_provenance"]

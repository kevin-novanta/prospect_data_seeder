

"""platform_ops.health

Simple readiness / liveness probes for CLI and container healthchecks.

Public API:
    readiness() -> dict
    liveness()  -> dict
"""
from __future__ import annotations

from datetime import datetime, timezone

_COMPONENT = "taxonomy_builder"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def readiness() -> dict:
    """Return a minimal readiness signal.

    In later phases you can add dependency checks (e.g., schema file exists,
    output dir writable, env sanity) and include details here.
    """
    return {
        "component": _COMPONENT,
        "status": "ok",
        "ts": _now_iso(),
        "checks": [],
    }


def liveness() -> dict:
    """Return a minimal liveness signal (process is running)."""
    return {
        "component": _COMPONENT,
        "status": "ok",
        "ts": _now_iso(),
    }


__all__ = ["readiness", "liveness"]
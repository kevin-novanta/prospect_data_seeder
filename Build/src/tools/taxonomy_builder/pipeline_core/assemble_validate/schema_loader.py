"""Schema loader for taxonomy output (Draft-07 JSON Schema).

Public API
----------
- resolve_schema_path(explicit: str | None = None) -> pathlib.Path | None
    If `explicit` is provided and exists, return it.
    Else, attempt to resolve the packaged schema at
    `tools/taxonomy_builder/schema/taxonomy.schema.json`.

- load_schema(explicit: str | None = None) -> dict
    Load and parse the schema JSON, raising FileNotFoundError or
    json.JSONDecodeError on failure.

- schema_info(explicit: str | None = None) -> dict
    Return a small info dict: {"path": str|None, "exists": bool, "$schema": str|None}.

Notes
-----
- This module does not perform validation; it only loads the schema. Use
  `assemble_validate.validate` for the actual jsonschema validation step.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Dict, Any

try:
    # Python 3.9+
    from importlib.resources import files as _res_files
except Exception:  # pragma: no cover
    _res_files = None  # type: ignore


_PACKAGED_SCHEMA_REL = (
    "tools",
    "taxonomy_builder",
    "schema",
    "taxonomy.schema.json",
)


def _packaged_schema_path() -> Optional[Path]:
    """Best-effort resolution of the packaged schema file.

    Returns `Path` if the file can be resolved on the current PYTHONPATH,
    otherwise `None`.
    """
    # Try importlib.resources first (when installed as a package/module)
    if _res_files is not None:
        try:
            pkg_root = _res_files("tools.taxonomy_builder").joinpath("schema")
            candidate = pkg_root.joinpath("taxonomy.schema.json")
            if candidate.is_file():
                return Path(str(candidate))
        except Exception:
            pass
    # Fallback to manual relative construction from CWD / sys.path
    candidate = Path.cwd().joinpath(*_PACKAGED_SCHEMA_REL)
    if candidate.is_file():
        return candidate
    # Try one directory up (common when running from Build/src)
    candidate = Path(__file__).resolve().parents[3].joinpath(*_PACKAGED_SCHEMA_REL)
    if candidate.is_file():
        return candidate
    return None


def resolve_schema_path(explicit: Optional[str] = None) -> Optional[Path]:
    """Resolve the schema path from explicit path or packaged location."""
    if explicit:
        p = Path(explicit).expanduser().resolve()
        return p if p.is_file() else None
    return _packaged_schema_path()


def load_schema(explicit: Optional[str] = None) -> Dict[str, Any]:
    """Load Draft-07 schema JSON into a dict.

    Raises FileNotFoundError if the schema cannot be located.
    Raises json.JSONDecodeError if the JSON is invalid.
    """
    path = resolve_schema_path(explicit)
    if not path or not path.is_file():
        raise FileNotFoundError("taxonomy schema not found; ensure schema/taxonomy.schema.json exists")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def schema_info(explicit: Optional[str] = None) -> Dict[str, Any]:
    """Return a small info record for diagnostics and banners."""
    info: Dict[str, Any] = {"path": None, "exists": False, "$schema": None}
    path = resolve_schema_path(explicit)
    if path is None:
        return info
    info["path"] = str(path)
    info["exists"] = path.is_file()
    if info["exists"]:
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            info["$schema"] = data.get("$schema")
        except Exception:
            pass
    return info


__all__ = ["resolve_schema_path", "load_schema", "schema_info"]

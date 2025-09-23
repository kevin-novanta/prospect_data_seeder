"""Validate taxonomy output against Draft-07 schema.

Public API
----------
validate_taxonomy(doc: dict, schema_path: str | None = None) -> None
    Validates the provided document against the taxonomy JSON Schema. Raises
    a ValueError with a concise message on failure, preserving the first
    validation error details. If `schema_path` is None, attempts to load the
    packaged schema via `schema_loader`.

Notes
-----
- Uses jsonschema Draft-07. The repository should include
  tools/taxonomy_builder/schema/taxonomy.schema.json.
- This module keeps a small surface area so callers can import it from
  runners or tests without extra dependencies.
"""
from __future__ import annotations

from typing import Any, Optional

from jsonschema import Draft7Validator, RefResolver, exceptions as js_ex

from .schema_loader import load_schema, resolve_schema_path


def _format_error(err: js_ex.ValidationError) -> str:
    # Build a concise, one-line error with the path where it failed
    path = "$" + "".join(f"/{p}" for p in err.absolute_path)
    ctx = "; ".join(sorted({c.message for c in err.context}) or [])
    base = f"{path}: {err.message}"
    if ctx:
        base += f" (context: {ctx})"
    return base


def validate_taxonomy(doc: dict, schema_path: Optional[str] = None) -> None:
    """Validate taxonomy `doc` against the Draft-07 schema.

    Raises
    ------
    ValueError
        If validation fails. The message includes the first error and how many
        total errors were found.
    FileNotFoundError
        If the schema file cannot be located.
    json.JSONDecodeError
        If the schema JSON is invalid.
    """
    if not isinstance(doc, dict):
        raise ValueError("taxonomy document must be a dict")

    schema = load_schema(schema_path)

    # Prepare a resolver with the base directory of the schema so $ref works
    schema_path_resolved = resolve_schema_path(schema_path)
    base_uri = (schema_path_resolved.parent.as_uri() + "/") if schema_path_resolved else ""
    resolver = RefResolver(base_uri=base_uri, referrer=schema)  # deprecated in jsonschema>=4, but works

    validator = Draft7Validator(schema, resolver=resolver)
    errors = sorted(validator.iter_errors(doc), key=lambda e: e.path)
    if errors:
        first = errors[0]
        msg = _format_error(first)
        raise ValueError(f"taxonomy validation failed: {msg}; total_errors={len(errors)}")

    # no return (success)


__all__ = ["validate_taxonomy"]

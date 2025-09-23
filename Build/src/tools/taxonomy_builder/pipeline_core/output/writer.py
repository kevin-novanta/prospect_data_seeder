"""Atomic writer for taxonomy output files.

Usage
-----
from tools.taxonomy_builder.pipeline_core.output.writer import write_taxonomy

write_taxonomy(doc, out_path="./data/taxonomy.json")

This function guarantees an atomic replace within the same filesystem by
writing to a temporary file in the target directory, fsync'ing, and then
renaming with os.replace().
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any


def _ensure_dir(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


def _atomic_write_text(path: Path, text: str, *, mode: int = 0o644) -> None:
    """Atomically write `text` to `path`.

    - Creates the parent directory if needed
    - Writes to a temp file in the same directory
    - fsyncs file contents and directory entry
    - Replaces the final file with os.replace (atomic on POSIX)
    """
    _ensure_dir(path)

    tmp = None
    dir_fd = None
    try:
        # Use the same directory to keep the rename atomic
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=str(path.parent), delete=False) as f:
            tmp = Path(f.name)
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        # Ensure directory entry is durable as well
        dir_fd = os.open(str(path.parent), os.O_DIRECTORY)
        try:
            os.replace(str(tmp), str(path))
            os.fchmod(os.open(str(path), os.O_RDONLY), mode)
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except Exception:
        # Best-effort cleanup of temp file on failure
        if tmp and tmp.exists():
            try:
                tmp.unlink()
            except Exception:
                pass
        raise


def write_taxonomy(doc: Dict[str, Any], out_path: str = "./data/taxonomy.json", *, pretty: bool = True) -> Path:
    """Write taxonomy document to JSON at `out_path` using an atomic replace.

    Parameters
    ----------
    doc : dict
        The fully assembled and validated taxonomy document.
    out_path : str
        Target path (default ./data/taxonomy.json).
    pretty : bool
        If True, writes indented JSON with a trailing newline.

    Returns
    -------
    Path
        The final file path written.
    """
    path = Path(out_path).expanduser().resolve()
    if pretty:
        text = json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    else:
        text = json.dumps(doc, ensure_ascii=False, separators=(",", ":"))
    _atomic_write_text(path, text)
    return path


def write_json(doc: Dict[str, Any], out_path: str = "./data/taxonomy.json", *, pretty: bool = True) -> Path:
    """Backward-compatible alias for write_taxonomy()."""
    return write_taxonomy(doc, out_path, pretty=pretty)


__all__ = ["write_taxonomy", "write_json"]

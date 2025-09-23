"""Central configuration for taxonomy_builder.

Exposes both object- and dict-style accessors:
  - load() -> Config
  - load_settings() -> dict
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

# ---------- Defaults from env ----------
_DEF_PROFILE = (os.getenv("TB_PROFILE") or "dev").strip()
_DEF_OUTPUT_DIR = Path(os.getenv("TB_OUTPUT_DIR") or "./data")
_DEF_SCHEMA_PATH = Path(os.getenv("TB_SCHEMA_PATH") or "./schema/taxonomy.schema.json")
_DEF_LOG_LEVEL = (os.getenv("TB_LOG_LEVEL") or "INFO").upper()
_DEF_HTTP_TIMEOUT = float(os.getenv("TB_HTTP_TIMEOUT") or 15)
_DEF_HTTP_UA = os.getenv(
    "TB_HTTP_USER_AGENT",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
)


@dataclass
class Config:
    profile: str = _DEF_PROFILE
    output_dir: Path = _DEF_OUTPUT_DIR
    schema_path: Path = _DEF_SCHEMA_PATH
    log_level: str = _DEF_LOG_LEVEL

    http_timeout_seconds: float = _DEF_HTTP_TIMEOUT
    user_agent: str = _DEF_HTTP_UA

    def ensure_dirs(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            profile=(os.getenv("TB_PROFILE") or _DEF_PROFILE).strip() or "dev",
            output_dir=Path(os.getenv("TB_OUTPUT_DIR") or _DEF_OUTPUT_DIR),
            schema_path=Path(os.getenv("TB_SCHEMA_PATH") or _DEF_SCHEMA_PATH),
            log_level=(os.getenv("TB_LOG_LEVEL") or _DEF_LOG_LEVEL).upper(),
            http_timeout_seconds=float(os.getenv("TB_HTTP_TIMEOUT") or _DEF_HTTP_TIMEOUT),
            user_agent=os.getenv("TB_HTTP_USER_AGENT") or _DEF_HTTP_UA,
        )


def load() -> Config:
    """Return a Config object resolved from environment with defaults."""
    return Config.from_env()


def load_settings() -> Dict[str, Any]:
    """Return a flat dict of settings (legacy convenience)."""
    cfg = load()
    return {
        "PROFILE": cfg.profile,
        "OUTPUT_DIR": str(cfg.output_dir),
        "SCHEMA_PATH": str(cfg.schema_path),
        "LOG_LEVEL": cfg.log_level,
        "HTTP_TIMEOUT_SECONDS": cfg.http_timeout_seconds,
        "USER_AGENT": cfg.user_agent,
    }


__all__ = ["Config", "load", "load_settings"]
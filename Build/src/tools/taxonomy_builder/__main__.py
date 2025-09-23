"""runtime_delivery.entrypoint

Exposes `print_config_banner()` used by `python -m tools.taxonomy_builder --self-check`.
This module intentionally has no side-effects and only depends on stdlib and
`tools.taxonomy_builder.config`.
"""
from __future__ import annotations

import json
import os
import sys
import platform
from datetime import datetime

# Import the Config loader from our package
from . import config as _config


def _pkg_version_or(name: str, default: str = "not-installed") -> str:
    try:
        import importlib.metadata as im  # Python >= 3.8
    except Exception:  # pragma: no cover
        try:
            import importlib_metadata as im  # type: ignore
        except Exception:
            return default
    try:
        return im.version(name)
    except Exception:
        return default


def print_config_banner() -> None:
    """Print a JSON summary of runtime + config, followed by a human line."""
    cfg = _config.load()

    summary = {
        "ts": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "python": sys.version.split()[0],
        "impl": platform.python_implementation(),
        "platform": platform.platform(),
        "profile": cfg.profile,
        "log_level": cfg.log_level,
        "env": {
            "TB_PROFILE": os.getenv("TB_PROFILE"),
            "TB_OUTPUT_DIR": os.getenv("TB_OUTPUT_DIR"),
            "TB_SCHEMA_PATH": os.getenv("TB_SCHEMA_PATH"),
            "TB_HTTP_TIMEOUT": os.getenv("TB_HTTP_TIMEOUT"),
            "TB_HTTP_USER_AGENT": os.getenv("TB_HTTP_USER_AGENT"),
        },
        "packages": {
            "requests": _pkg_version_or("requests"),
            "beautifulsoup4": _pkg_version_or("beautifulsoup4"),
            "lxml": _pkg_version_or("lxml"),
            "jsonschema": _pkg_version_or("jsonschema"),
            "playwright": _pkg_version_or("playwright"),
        },
        "paths": {
            "OUTPUT_DIR": str(cfg.output_dir.resolve()),
            "SCHEMA_PATH": str(cfg.schema_path.resolve()),
            "DATA_DIR_EXISTS": cfg.output_dir.exists(),
            "SCHEMA_EXISTS": cfg.schema_path.exists(),
        },
    }

    print(json.dumps({"entrypoint": summary}, indent=2))
    print(
        f"OK — profile={cfg.profile} python={summary['python']} "
        f"output_dir={summary['paths']['OUTPUT_DIR']} schema_exists={summary['paths']['SCHEMA_EXISTS']}"
    )


# Allow manual execution for quick check
if __name__ == "__main__":
    print_config_banner()
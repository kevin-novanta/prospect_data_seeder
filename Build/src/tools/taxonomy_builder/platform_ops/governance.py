"""platform_ops.governance

Minimal governance toggles for early phases.

Responsibilities (Phase 2 minimal):
- robots_policy(profile) -> bool : whether to respect robots.txt
- allow_domain(url) -> bool      : coarse domain allowlist (fixture always true)

Later phases may add:
- per-domain crawl-delay, disallow rules
- policy profiles tied to runtime_delivery.profiles
- audit logging of policy decisions
"""
from __future__ import annotations

from urllib.parse import urlparse

# Profiles that should respect robots by default (you can adjust later)
_ROBOTS_ON_PROFILES = {"prod"}


def robots_policy(profile: str | None) -> bool:
    """Return True if the given profile should respect robots.txt.

    Phase 2 defaults:
      - dev:  False
      - ci:   False (deterministic fixture runs)
      - prod: True
    """
    if not profile:
        return False
    return profile.lower() in _ROBOTS_ON_PROFILES


def allow_domain(url: str | None) -> bool:
    """Coarse domain allowlist.

    For Phase 2 we keep this permissive: any http(s) domain is allowed.
    We special-case fixture/local paths to always return True.
    """
    if not url:
        return False

    # Fixture / local runs
    if url.startswith("file://"):
        return True

    p = urlparse(url)
    if p.scheme in {"http", "https"} and p.netloc:
        return True
    return False


__all__ = ["robots_policy", "allow_domain"]
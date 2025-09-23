"""URL normalization helpers.

`canonicalize(base, href) -> str`
- Resolves relative `href` against `base` (when provided)
- Forces scheme+netloc for http(s) URLs
- Lowercases scheme/host, removes default ports (:80 for http, :443 for https)
- Collapses duplicate slashes in path, resolves dot-segments
- Drops URL fragment (#...)
- Strips common tracking query params (utm_*, gclid, fbclid, mc_cid, mc_eid, ref, ref_src, ref_url, _hsenc, _hsmi, hsa_*)
- Returns the normalized absolute URL (or empty string if not normalizable)

Notes
-----
- mailto:, tel:, javascript: are returned untouched (after strip()) since they are not navigable http(s) URLs.
- If `href` is empty/None, returns "".
- If `base` is missing and `href` is relative, returns "" (cannot resolve).
"""
from __future__ import annotations

import posixpath
from urllib.parse import urlparse, urlunparse, urljoin, parse_qsl, urlencode
from typing import Iterable, Tuple, List

# Tracking param rules
_DROP_PREFIXES = ("utm_", "hsa_")
_DROP_KEYS = {
    "gclid", "fbclid",
    "mc_cid", "mc_eid",
    "_hsenc", "_hsmi",
    "ref", "ref_src", "ref_url",
}


def _is_http_scheme(scheme: str) -> bool:
    return scheme in ("http", "https")


def _clean_query(pairs: Iterable[Tuple[str, str]]) -> List[Tuple[str, str]]:
    cleaned: List[Tuple[str, str]] = []
    for k, v in pairs:
        lk = (k or "").lower()
        if lk in _DROP_KEYS:
            continue
        if any(lk.startswith(pfx) for pfx in _DROP_PREFIXES):
            continue
        # keep empty-value keys if present
        cleaned.append((k, v))
    return cleaned


def _normalize_netloc(scheme: str, netloc: str) -> str:
    if not netloc:
        return netloc
    # Split userinfo@host:port
    userinfo, hostport = ("", netloc)
    if "@" in netloc:
        userinfo, hostport = netloc.rsplit("@", 1)
    host, port = (hostport, "")
    if ":" in hostport:
        host, port = hostport.split(":", 1)
    host = host.lower()
    # Drop default ports
    if (scheme == "http" and port == "80") or (scheme == "https" and port == "443"):
        port = ""
    rebuilt = host
    if port:
        rebuilt = f"{rebuilt}:{port}"
    if userinfo:
        rebuilt = f"{userinfo}@{rebuilt}"
    return rebuilt


def _normalize_path(path: str) -> str:
    if not path:
        return "/"
    # Collapse duplicate slashes and resolve dot-segments
    # posixpath.normpath keeps a leading slash if present
    collapsed = posixpath.normpath(path)
    # normpath removes trailing slash except for root; preserve root slash
    if not collapsed.startswith('/'):
        collapsed = '/' + collapsed
    return collapsed


def canonicalize(base: str | None, href: str | None) -> str:
    href = (href or "").strip()
    if not href:
        return ""

    # Non-http schemes: return as-is (mailto, tel, javascript, data, etc.)
    p_href = urlparse(href)
    if p_href.scheme and not _is_http_scheme(p_href.scheme.lower()):
        return href

    # Resolve relative using base when needed
    if not p_href.scheme and not href.startswith("//"):
        if not base:
            return ""  # cannot resolve relative without base
        href = urljoin(base, href)
        p_href = urlparse(href)

    # Protocol-relative URLs (//example.com/path)
    if href.startswith("//"):
        # assume https by default
        href = "https:" + href
        p_href = urlparse(href)

    scheme = (p_href.scheme or "https").lower()
    if not _is_http_scheme(scheme):
        # if scheme ended up non-http after resolution, return best-effort
        return href

    netloc = _normalize_netloc(scheme, p_href.netloc)
    path = _normalize_path(p_href.path)

    # Clean query string
    pairs = parse_qsl(p_href.query, keep_blank_values=True)
    pairs = _clean_query(pairs)
    query = urlencode(pairs, doseq=True)

    # Drop fragment
    fragment = ""

    normalized = urlunparse((scheme, netloc, path, "", query, fragment))
    return normalized


__all__ = ["canonicalize"]

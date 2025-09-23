

from __future__ import annotations

import sys
import os
import argparse
from pathlib import Path

# Runner orchestrates the end-to-end flow
from .runtime_delivery import runner as _runner

DEFAULT_OUT = "./data/taxonomy.json"
PROFILE_CHOICES = ("dev", "ci", "prod")


def _ensure_parent(path: str) -> None:
    p = Path(path).expanduser().resolve()
    p.parent.mkdir(parents=True, exist_ok=True)


def _coerce_profile(val: str | None) -> str:
    if not val:
        return "dev"
    v = val.lower().strip()
    if v not in PROFILE_CHOICES:
        raise SystemExit(f"invalid --profile: {val} (choices: {', '.join(PROFILE_CHOICES)})")
    return v


def build_cmd(args: argparse.Namespace) -> int:
    profile = _coerce_profile(args.profile)

    # Surface profile to the environment so config/profiles can read it
    os.environ.setdefault("TB_PROFILE", profile)

    out_path = args.out or DEFAULT_OUT
    _ensure_parent(out_path)

    # Preferred API: runner.run_build(...), if present
    if hasattr(_runner, "run_build"):
        return int(_runner.run_build(out_path=out_path, html_path=args.html, profile=profile) or 0)

    # Fallback: pick path based on provided flags
    if args.html:
        _runner.build_from_html(args.html, out_path)
        return 0

    # Else dispatch to auto (uses config/env to decide URL vs fixture)
    _runner.build_auto(out_path)
    return 0


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="taxonomy_builder", description="Taxonomy Builder CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build", help="Build taxonomy JSON from directory HTML or live source")
    p_build.add_argument("--html", metavar="FILE", help="Fixture HTML file (offline parse)")
    p_build.add_argument("--out", metavar="FILE", default=DEFAULT_OUT, help=f"Output JSON (default {DEFAULT_OUT})")
    p_build.add_argument(
        "--profile", choices=list(PROFILE_CHOICES), default="dev", help="Profile to use (dev|ci|prod)"
    )
    p_build.set_defaults(func=build_cmd)

    return parser


def main(argv: list[str] | None = None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    parser = make_parser()
    args = parser.parse_args(argv)
    rc = args.func(args)  # type: ignore[attr-defined]
    raise SystemExit(int(rc or 0))


if __name__ == "__main__":
    main()
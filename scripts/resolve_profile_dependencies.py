#!/usr/bin/env python3
"""Resolve a profile's transitive `depends_on` chain from the matrix registry.

Read-only. Given a profile name (or several), walk
``profiles/profile-index.yaml`` and emit the ordered set of profiles that
need to be installed together — including the requested profile and all of
its transitive dependencies in dependency-first order.

Detects:
- Unknown profile names
- Missing depends_on targets
- Circular dependencies

Does NOT install anything. The install plan validator and applier remain the
gates for any real runtime write.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PROFILE_INDEX = REPO_ROOT / "profiles" / "profile-index.yaml"


def _strip_block_scalar(value: str) -> str:
    return " ".join(line.strip() for line in value.splitlines() if line.strip())


def parse_profile_dependencies(text: str) -> dict[str, dict[str, Any]]:
    """Line-based parser for profile metadata we care about.

    Only extracts the metadata chain installers and diagnostics need:
    ``depends_on``, ``entrypoints``, ``routers``, ``status``, ``future_repo``,
    and ``github_url`` per profile. Avoids a PyYAML dependency — the
    profile-index file uses stable two-space indentation with profile keys at
    column 2.
    """
    profiles: dict[str, dict[str, Any]] = {}
    in_profiles_block = False
    current: str | None = None
    active_list_field: str | None = None
    lines = text.splitlines()
    for line in lines:
        stripped = line.strip()
        if not in_profiles_block:
            if line.rstrip() == "profiles:":
                in_profiles_block = True
            continue
        # Blank or comment-only lines belong to whatever profile is active.
        if not stripped or stripped.startswith("#"):
            continue
        if not line.startswith(" "):
            # left the profiles block (top-level key)
            break
        if line.startswith("  ") and not line.startswith("    "):
            match = re.match(r"^\s\s([a-z0-9][a-z0-9-]*):\s*$", line)
            if match:
                current = match.group(1)
                profiles[current] = {
                    "depends_on": [],
                    "entrypoints": [],
                    "routers": [],
                    "status": None,
                    "future_repo": None,
                    "github_url": None,
                }
                active_list_field = None
            else:
                # column-2 line that isn't a profile key — leaves profiles block
                if stripped and not stripped.startswith("#"):
                    break
            continue
        if current is None:
            continue
        if line.startswith("    ") and not line.startswith("      "):
            active_list_field = None
            for field in ("depends_on", "entrypoints", "routers"):
                if stripped.startswith(f"{field}:"):
                    active_list_field = field
                    break
            if active_list_field is not None:
                continue
            for field in ("status", "future_repo", "github_url"):
                marker = f"{field}:"
                if stripped.startswith(marker):
                    profiles[current][field] = stripped[len(marker):].strip()
                    break
            continue
        if active_list_field is not None and stripped.startswith("- "):
            profiles[current][active_list_field].append(stripped[2:].strip())
    return profiles


def resolve(
    requested: list[str],
    profiles: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    issues: list[str] = []
    order: list[str] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    for name in requested:
        if name not in profiles:
            issues.append(f"unknown profile: `{name}`")

    def walk(name: str, stack: list[str]) -> None:
        if name in visited:
            return
        if name in visiting:
            cycle = " → ".join(stack + [name])
            issues.append(f"circular depends_on chain: {cycle}")
            return
        if name not in profiles:
            return
        visiting.add(name)
        for dep in profiles[name].get("depends_on", []):
            if dep not in profiles:
                issues.append(
                    f"`{name}` depends_on `{dep}` but `{dep}` is not in the registry"
                )
                continue
            walk(dep, stack + [name])
        visiting.discard(name)
        visited.add(name)
        order.append(name)

    for name in requested:
        if name in profiles:
            walk(name, [])

    return {
        "requested": requested,
        "resolution_order": order,
        "issues": issues,
        "passed": not issues,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Resolve a profile's transitive depends_on chain from the matrix "
            "registry. Read-only — does not install anything."
        )
    )
    parser.add_argument(
        "profiles",
        nargs="+",
        help="One or more profile names to resolve (e.g. quick-experiment)",
    )
    parser.add_argument(
        "--profile-index",
        type=Path,
        default=PROFILE_INDEX,
        help="Path to profiles/profile-index.yaml (default: %(default)s)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    text = args.profile_index.read_text(encoding="utf-8")
    profiles = parse_profile_dependencies(text)
    report = resolve(args.profiles, profiles)
    # Annotate each resolved profile with status / repo / url so the caller
    # can decide install order and where to clone from.
    annotated_order = []
    for name in report["resolution_order"]:
        info = profiles.get(name, {})
        annotated_order.append(
            {
                "profile": name,
                "status": info.get("status"),
                "future_repo": info.get("future_repo"),
                "github_url": info.get("github_url"),
                "depends_on": info.get("depends_on", []),
                "entrypoints": info.get("entrypoints", []),
                "routers": info.get("routers", []),
            }
        )
    report["resolution_order"] = annotated_order
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Verify sibling pack repos match the pinned commits in profile-index.yaml.

Read-only. Walks ``profiles/profile-index.yaml`` `repo_matrix` entries with a
`pinned_commit`, then for each one runs ``git -C <pack-path> rev-parse HEAD``
to check whether the pack on disk is at the pinned revision. Prints a report
and exits non-zero if any pack diverges from its pin.

Does NOT mutate anything. Checking out the pinned ref is the operator's call.

Usage:
    python3 scripts/verify_pack_pins.py --pack-search-path <parent-of-cloned-packs>
    python3 scripts/verify_pack_pins.py --pack-search-path . --json
    python3 scripts/verify_pack_pins.py --pack <name>=<path> [--pack ...]

Example:
    # All sibling packs cloned under ~/Projects/<repo-name>/
    python3 scripts/verify_pack_pins.py --pack-search-path ~/Projects
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PROFILE_INDEX = REPO_ROOT / "profiles" / "profile-index.yaml"
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


def parse_pinned_packs(text: str) -> dict[str, dict[str, str]]:
    """Line-based parser. Pulls each top-level repo_matrix entry's name,
    github_url, pinned_commit, pinned_at.
    """
    in_repo_matrix = False
    repo_matrix_indent = None
    current_name: str | None = None
    current_indent = -1
    out: dict[str, dict[str, str]] = {}

    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip())
        stripped = raw_line.strip()

        if stripped.rstrip(":") == "repo_matrix" and stripped.endswith(":"):
            in_repo_matrix = True
            repo_matrix_indent = indent
            current_name = None
            continue

        if not in_repo_matrix:
            continue

        if indent <= (repo_matrix_indent or -1) and stripped.endswith(":"):
            # We left repo_matrix into a new top-level key
            in_repo_matrix = False
            current_name = None
            continue

        if indent == (repo_matrix_indent or 0) + 2 and stripped.endswith(":"):
            current_name = stripped[:-1].strip()
            current_indent = indent
            out.setdefault(current_name, {})
            continue

        if current_name is None:
            continue

        if indent <= current_indent:
            current_name = None
            continue

        for key in ("github_url", "pinned_commit", "pinned_at"):
            prefix = f"{key}:"
            if stripped.startswith(prefix):
                value = stripped[len(prefix) :].strip().strip('"')
                out[current_name][key] = value
                break

    return {
        name: meta
        for name, meta in out.items()
        if "pinned_commit" in meta and COMMIT_RE.match(meta["pinned_commit"])
    }


def git_head(repo_path: Path) -> tuple[str | None, str | None]:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_path), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return None, "git executable not found"
    if proc.returncode != 0:
        return None, (proc.stderr or proc.stdout).strip()
    sha = proc.stdout.strip()
    if not COMMIT_RE.match(sha):
        return None, f"unexpected rev-parse output: {sha!r}"
    return sha, None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pack-search-path",
        type=Path,
        default=None,
        help="Parent directory under which each pack is cloned as <pack-name>/.",
    )
    parser.add_argument(
        "--pack",
        action="append",
        default=[],
        metavar="NAME=PATH",
        help="Override a single pack location (repeatable).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit results as JSON instead of human-readable text.",
    )
    args = parser.parse_args()

    pinned = parse_pinned_packs(PROFILE_INDEX.read_text())
    if not pinned:
        print(
            f"no pinned packs found in {PROFILE_INDEX.relative_to(REPO_ROOT)}",
            file=sys.stderr,
        )
        return 2

    overrides: dict[str, Path] = {}
    for spec in args.pack:
        if "=" not in spec:
            print(f"--pack expects NAME=PATH, got {spec!r}", file=sys.stderr)
            return 2
        name, _, path = spec.partition("=")
        overrides[name.strip()] = Path(path).expanduser().resolve()

    results: list[dict[str, str]] = []
    any_failure = False

    for name, meta in sorted(pinned.items()):
        pinned_commit = meta["pinned_commit"]
        path: Path | None
        if name in overrides:
            path = overrides[name]
        elif args.pack_search_path is not None:
            path = (args.pack_search_path / name).expanduser().resolve()
        else:
            path = None

        entry: dict[str, str] = {
            "pack": name,
            "pinned_commit": pinned_commit,
            "pinned_at": meta.get("pinned_at", ""),
        }
        if path is None:
            entry["status"] = "skipped"
            entry["reason"] = "no --pack-search-path and no --pack override"
            results.append(entry)
            continue
        entry["path"] = str(path)
        if not path.exists():
            entry["status"] = "missing"
            entry["reason"] = "pack directory does not exist"
            any_failure = True
            results.append(entry)
            continue

        head, err = git_head(path)
        if head is None:
            entry["status"] = "error"
            entry["reason"] = err or "unknown git error"
            any_failure = True
            results.append(entry)
            continue
        entry["actual_commit"] = head
        if head == pinned_commit:
            entry["status"] = "match"
        else:
            entry["status"] = "mismatch"
            any_failure = True
        results.append(entry)

    if args.json:
        print(json.dumps({"results": results}, indent=2))
    else:
        for entry in results:
            status = entry["status"].upper()
            line = f"[{status}] {entry['pack']}"
            if "path" in entry:
                line += f"  ({entry['path']})"
            print(line)
            print(f"    pinned:  {entry['pinned_commit']}  ({entry.get('pinned_at','')})")
            if "actual_commit" in entry:
                print(f"    actual:  {entry['actual_commit']}")
            if "reason" in entry:
                print(f"    reason:  {entry['reason']}")
        print()
        summary = {
            "match": sum(1 for r in results if r["status"] == "match"),
            "mismatch": sum(1 for r in results if r["status"] == "mismatch"),
            "missing": sum(1 for r in results if r["status"] == "missing"),
            "skipped": sum(1 for r in results if r["status"] == "skipped"),
            "error": sum(1 for r in results if r["status"] == "error"),
        }
        print(
            "summary: "
            + ", ".join(f"{k}={v}" for k, v in summary.items() if v)
        )

    return 1 if any_failure else 0


if __name__ == "__main__":
    sys.exit(main())

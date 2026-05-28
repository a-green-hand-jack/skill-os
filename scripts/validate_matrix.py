#!/usr/bin/env python3
"""Run Skill OS hub + sibling-pack validation as one matrix check.

This is the maintainer-facing wrapper for cross-repo consistency. It does not
mutate any repo. It runs the local hub checks and, when pack paths are supplied,
threads the same pack discovery through taxonomy validation and pinned-commit
verification.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from resolve_profile_dependencies import parse_profile_dependencies  # noqa: E402
from verify_pack_pins import parse_pinned_packs  # noqa: E402

PROFILE_INDEX = REPO_ROOT / "profiles" / "profile-index.yaml"


@dataclass(frozen=True)
class PackOverride:
    requested_name: str
    repo_name: str
    path: Path


def normalize_pack_name(
    name: str,
    profiles: dict[str, dict[str, Any]],
    pinned_repo_names: set[str],
) -> str:
    """Accept either repo names (`ml-research-skills`) or profile names (`ml-research`)."""
    if name in pinned_repo_names:
        return name
    profile = profiles.get(name)
    if isinstance(profile, dict):
        future_repo = profile.get("future_repo")
        if isinstance(future_repo, str) and future_repo in pinned_repo_names:
            return future_repo
    return name


def parse_pack_overrides(
    specs: list[str],
    profiles: dict[str, dict[str, Any]],
    pinned_repo_names: set[str],
) -> list[PackOverride]:
    overrides: list[PackOverride] = []
    for spec in specs:
        if "=" not in spec:
            raise ValueError(f"--pack expects NAME=PATH, got {spec!r}")
        name, _, raw_path = spec.partition("=")
        requested = name.strip()
        if not requested:
            raise ValueError(f"--pack expects a non-empty NAME in {spec!r}")
        repo_name = normalize_pack_name(requested, profiles, pinned_repo_names)
        overrides.append(
            PackOverride(
                requested_name=requested,
                repo_name=repo_name,
                path=Path(raw_path).expanduser().resolve(),
            )
        )
    return overrides


def build_pack_args(
    search_paths: list[Path],
    overrides: list[PackOverride],
) -> list[str]:
    args: list[str] = []
    for path in search_paths:
        args.extend(["--pack-search-path", str(path)])
    for override in overrides:
        args.extend(["--pack", f"{override.repo_name}={override.path}"])
    return args


def discover_pack_paths(
    pinned: dict[str, dict[str, str]],
    search_paths: list[Path],
    overrides: list[PackOverride],
) -> list[dict[str, str]]:
    override_by_repo = {override.repo_name: override for override in overrides}
    rows: list[dict[str, str]] = []
    for repo_name in sorted(pinned):
        row: dict[str, str] = {"pack": repo_name}
        override = override_by_repo.get(repo_name)
        if override is not None:
            row["source"] = "override"
            row["requested_name"] = override.requested_name
            row["path"] = str(override.path)
            row["status"] = "present" if override.path.is_dir() else "missing"
            rows.append(row)
            continue
        found: Path | None = None
        for parent in search_paths:
            candidate = parent / repo_name
            if candidate.is_dir():
                found = candidate.resolve()
                break
        if found is not None:
            row["source"] = "search-path"
            row["path"] = str(found)
            row["status"] = "present"
        else:
            row["source"] = "search-path" if search_paths else "not-specified"
            row["status"] = "missing" if search_paths else "skipped"
        rows.append(row)
    return rows


def run_command(name: str, cmd: list[str]) -> dict[str, Any]:
    proc = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "name": name,
        "status": "passed" if proc.returncode == 0 else "failed",
        "exit_code": proc.returncode,
        "command": cmd,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def skipped_step(name: str, reason: str) -> dict[str, Any]:
    return {
        "name": name,
        "status": "skipped",
        "exit_code": 0,
        "reason": reason,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the skill-os hub checks plus sibling-pack taxonomy and pin "
            "checks. This script is read-only."
        )
    )
    parser.add_argument(
        "--pack-search-path",
        type=Path,
        action="append",
        default=[],
        help="Parent directory containing sibling pack repos by canonical repo name.",
    )
    parser.add_argument(
        "--pack",
        action="append",
        default=[],
        metavar="NAME=PATH",
        help=(
            "Override one pack path. NAME may be a repo name "
            "(ml-research-skills) or profile name (ml-research). Repeatable."
        ),
    )
    parser.add_argument("--skip-tests", action="store_true", help="Skip unittest discovery.")
    parser.add_argument("--skip-adapters", action="store_true", help="Skip adapter export check.")
    parser.add_argument("--skip-taxonomy", action="store_true", help="Skip matrix-aware taxonomy validation.")
    parser.add_argument("--skip-pins", action="store_true", help="Skip sibling-pack pinned commit verification.")
    parser.add_argument("--json", action="store_true", help="Emit a JSON report.")
    return parser.parse_args(argv)


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    profile_text = PROFILE_INDEX.read_text(encoding="utf-8")
    profiles = parse_profile_dependencies(profile_text)
    pinned = parse_pinned_packs(profile_text)
    overrides = parse_pack_overrides(args.pack, profiles, set(pinned))
    search_paths = [path.expanduser().resolve() for path in args.pack_search_path]
    pack_args = build_pack_args(search_paths, overrides)

    steps: list[dict[str, Any]] = []
    if args.skip_tests:
        steps.append(skipped_step("unit-tests", "--skip-tests"))
    else:
        steps.append(run_command("unit-tests", ["python3", "-m", "unittest", "discover", "tests"]))

    if args.skip_adapters:
        steps.append(skipped_step("adapter-export", "--skip-adapters"))
    else:
        steps.append(
            run_command(
                "adapter-export",
                ["python3", "scripts/export_skill_kernel_adapters.py", "--runtime", "all", "--check"],
            )
        )

    if args.skip_taxonomy:
        steps.append(skipped_step("taxonomy", "--skip-taxonomy"))
    else:
        steps.append(
            run_command(
                "taxonomy",
                ["uv", "run", "scripts/validate_skill_taxonomy.py", *pack_args],
            )
        )

    if args.skip_pins:
        steps.append(skipped_step("pack-pins", "--skip-pins"))
    else:
        steps.append(
            run_command(
                "pack-pins",
                ["python3", "scripts/verify_pack_pins.py", *pack_args, "--json"],
            )
        )

    summary = {
        "passed": sum(1 for step in steps if step["status"] == "passed"),
        "failed": sum(1 for step in steps if step["status"] == "failed"),
        "skipped": sum(1 for step in steps if step["status"] == "skipped"),
    }
    return {
        "schema_version": "0.1",
        "passed": summary["failed"] == 0,
        "summary": summary,
        "pack_paths": discover_pack_paths(pinned, search_paths, overrides),
        "steps": steps,
    }


def emit_text(report: dict[str, Any]) -> None:
    status = "PASS" if report["passed"] else "FAIL"
    summary = report["summary"]
    print(
        f"{status}: matrix validation "
        f"({summary['passed']} passed, {summary['failed']} failed, {summary['skipped']} skipped)"
    )
    print()
    print("Pack paths:")
    for row in report["pack_paths"]:
        suffix = f"  {row.get('path', '')}" if row.get("path") else ""
        requested = row.get("requested_name")
        alias = f" via {requested}" if requested and requested != row["pack"] else ""
        print(f"  [{row['status']}] {row['pack']}{alias}{suffix}")
    print()
    print("Checks:")
    for step in report["steps"]:
        print(f"  [{step['status']}] {step['name']}")
        if step["status"] == "failed":
            if step.get("stdout"):
                print(step["stdout"].rstrip())
            if step.get("stderr"):
                print(step["stderr"].rstrip())


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(sys.argv[1:] if argv is None else argv)
        report = build_report(args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        emit_text(report)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

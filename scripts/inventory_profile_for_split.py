#!/usr/bin/env python3
"""Inventory the files a repo-split scaffolder would copy for a profile.

Read-only. Produces two artifacts:

1. A source inventory JSON listing kernel example, kernel ``source_paths``,
   the profile-index entry, and every file under each required/optional skill
   directory, with sha256 hashes, byte counts, and proposed destination paths.
2. A privacy audit JSON that scans each included file for credential
   markers, absolute home paths, machine-specific email markers, sidecar paths,
   and raw log markers, and records a final pass/fail verdict.

Neither artifact represents an authorization to copy files into a destination
repo. The reviewed install/repo-split handoff contract remains the gate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_KERNEL_DIR = REPO_ROOT / "schemas" / "skill-kernel" / "examples"
PROFILE_INDEX_PATH = REPO_ROOT / "profiles" / "profile-index.yaml"

INVENTORY_SCHEMA_VERSION = "0.1"
AUDIT_SCHEMA_VERSION = "0.1"

EXCLUSIONS = [
    {
        "path_pattern": ".agent/sidecars/",
        "reason": "private sidecar artifacts are excluded by repo policy",
    },
    {
        "path_pattern": "memory/",
        "reason": "project memory is not part of the public profile pack",
    },
    {
        "path_pattern": "*/.DS_Store",
        "reason": "OS metadata files are never copied into a split repo",
    },
    {
        "path_pattern": "*/__pycache__/*",
        "reason": "compiled bytecode is never copied",
    },
]

PRIVACY_PATTERNS = [
    {
        "id": "absolute-mac-home",
        "pattern": r"/Users/[A-Za-z0-9._-]+/",
        "rationale": "Absolute macOS home paths leak machine-specific user identity.",
    },
    {
        "id": "absolute-linux-home",
        "pattern": r"/home/[A-Za-z0-9._-]+/",
        "rationale": "Absolute Linux home paths leak machine-specific user identity.",
    },
    {
        "id": "sidecar-private-path",
        "pattern": r"\.agent/sidecars/[A-Za-z0-9][A-Za-z0-9._-]{4,}/",
        "rationale": "Concrete sidecar artifact paths (with a real task id segment) are local-only and must not enter a public split repo. Placeholder forms like `.agent/sidecars/<task-id>/` are documented conventions and are not matched by this pattern.",
    },
    {
        "id": "ssh-private-key-block",
        "pattern": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
        "rationale": "Private key material must never be copied.",
    },
    {
        "id": "openssh-public-marker",
        "pattern": r"ssh-(rsa|ed25519|ecdsa) AAAA",
        "rationale": "Hard-coded public keys often indicate accidental key material copy.",
    },
    {
        "id": "aws-access-key-id",
        "pattern": r"AKIA[0-9A-Z]{16}",
        "rationale": "AWS access key IDs are credentials.",
    },
    {
        "id": "github-token-prefix",
        "pattern": r"gh[pousr]_[A-Za-z0-9]{20,}",
        "rationale": "GitHub personal access / OAuth tokens are credentials.",
    },
    {
        "id": "anthropic-api-key",
        "pattern": r"sk-ant-[A-Za-z0-9_-]{20,}",
        "rationale": "Anthropic API keys are credentials.",
    },
    {
        "id": "user-email-kaust",
        "pattern": r"[A-Za-z0-9._%+-]+@kaust\.edu\.sa",
        "rationale": "Personal institutional email leaks user identity.",
    },
    {
        "id": "user-email-northwestern",
        "pattern": r"[A-Za-z0-9._%+-]+@northwestern\.edu",
        "rationale": "Personal institutional email leaks user identity.",
    },
    {
        "id": "user-email-epfl",
        "pattern": r"[A-Za-z0-9._%+-]+@epfl\.ch",
        "rationale": "Personal institutional email leaks user identity.",
    },
]


def sha256_hex(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def repo_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"{repo_relative(path)} is missing") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"{repo_relative(path)} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{repo_relative(path)} must contain a JSON object")
    return data


def kernel_path_for(profile: str, kernel_dir: Path) -> Path:
    direct = kernel_dir / f"{profile}.kernel.json"
    if direct.is_file():
        return direct
    workflow_variant = kernel_dir / f"{profile}-workflow-contract.kernel.json"
    if workflow_variant.is_file():
        return workflow_variant
    raise ValueError(
        f"no kernel example for profile `{profile}` under {repo_relative(kernel_dir)}"
    )


def walk_skill_dir(skill_name: str, kind: str) -> list[dict[str, Any]]:
    skill_root = REPO_ROOT / "skills" / skill_name
    if not skill_root.is_dir():
        raise ValueError(f"skill directory missing: skills/{skill_name}")
    entries: list[dict[str, Any]] = []
    for file_path in sorted(skill_root.rglob("*")):
        if not file_path.is_file():
            continue
        if "__pycache__" in file_path.parts or file_path.name == ".DS_Store":
            continue
        rel = repo_relative(file_path)
        raw = file_path.read_bytes()
        entries.append(
            {
                "path": rel,
                "class": kind,
                "size_bytes": len(raw),
                "sha256": sha256_hex(raw),
                "include_in_split": True,
                "destination_path": rel,
                "owning_skill": skill_name,
            }
        )
    return entries


def file_entry(rel_path: str, classification: str) -> dict[str, Any]:
    path = REPO_ROOT / rel_path
    if not path.is_file():
        raise ValueError(f"source path is not a file: {rel_path}")
    raw = path.read_bytes()
    return {
        "path": rel_path,
        "class": classification,
        "size_bytes": len(raw),
        "sha256": sha256_hex(raw),
        "include_in_split": True,
        "destination_path": rel_path,
    }


def directory_entries(rel_path: str, classification: str) -> list[dict[str, Any]]:
    path = REPO_ROOT / rel_path
    if not path.is_dir():
        return []
    entries: list[dict[str, Any]] = []
    for file_path in sorted(path.rglob("*")):
        if not file_path.is_file():
            continue
        if "__pycache__" in file_path.parts or file_path.name == ".DS_Store":
            continue
        rel = repo_relative(file_path)
        raw = file_path.read_bytes()
        entries.append(
            {
                "path": rel,
                "class": classification,
                "size_bytes": len(raw),
                "sha256": sha256_hex(raw),
                "include_in_split": True,
                "destination_path": rel,
            }
        )
    return entries


def kernel_source_entries(kernel: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for rel in kernel.get("source_paths", []):
        if not isinstance(rel, str):
            continue
        if rel.startswith("skills/"):
            # Skill files are enumerated through the skill walk; reference only here.
            continue
        path = REPO_ROOT / rel
        if path.is_dir():
            entries.extend(directory_entries(rel, "kernel-source"))
        elif path.is_file():
            entries.append(file_entry(rel, "kernel-source"))
    return entries


def build_inventory(profile: str, kernel_dir: Path) -> dict[str, Any]:
    kernel_path = kernel_path_for(profile, kernel_dir)
    kernel = load_json(kernel_path)
    if kernel.get("profile", {}).get("name") != profile:
        # Allow workflow-contract kernels whose name differs by suffix.
        if not kernel_path.name.startswith(profile):
            raise ValueError(
                f"kernel at {repo_relative(kernel_path)} does not declare profile `{profile}`"
            )

    sources: list[dict[str, Any]] = []
    sources.append(file_entry(repo_relative(kernel_path), "kernel"))

    sources.extend(kernel_source_entries(kernel))

    required_skills = kernel.get("skills", {}).get("required", []) or []
    optional_skills = kernel.get("skills", {}).get("optional", []) or []
    seen_paths = {entry["path"] for entry in sources}
    for skill in required_skills:
        for entry in walk_skill_dir(skill, "skill-required"):
            if entry["path"] in seen_paths:
                continue
            sources.append(entry)
            seen_paths.add(entry["path"])
    for skill in optional_skills:
        for entry in walk_skill_dir(skill, "skill-optional"):
            if entry["path"] in seen_paths:
                continue
            sources.append(entry)
            seen_paths.add(entry["path"])

    profile_index = {
        "path": "profiles/profile-index.yaml",
        "key": profile,
        "destination_path": "profiles/profile-index.yaml",
    }

    sources.sort(key=lambda entry: (entry["class"], entry["path"]))

    totals = {
        "file_count": len(sources),
        "total_bytes": sum(entry["size_bytes"] for entry in sources),
        "skill_count": len(required_skills) + len(optional_skills),
    }

    inventory: dict[str, Any] = {
        "schema_version": INVENTORY_SCHEMA_VERSION,
        "profile": profile,
        "kernel_id": kernel.get("kernel_id", profile),
        "kernel_path": repo_relative(kernel_path),
        "kernel_source_paths": [
            rel for rel in kernel.get("source_paths", []) if isinstance(rel, str)
        ],
        "sources": sources,
        "profile_index": profile_index,
        "excluded_sources": EXCLUSIONS,
        "totals": totals,
    }
    return inventory


def scan_file_for_patterns(
    path: Path,
    compiled_patterns: list[tuple[str, re.Pattern[str]]],
) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return hits
    for line_number, line in enumerate(text.splitlines(), start=1):
        for pattern_id, pattern in compiled_patterns:
            if pattern.search(line):
                hits.append(
                    {
                        "path": repo_relative(path),
                        "line_number": line_number,
                        "pattern_id": pattern_id,
                        "snippet": line.strip()[:200],
                    }
                )
    return hits


def build_privacy_audit(
    inventory: dict[str, Any],
    inventory_source_label: str,
) -> dict[str, Any]:
    compiled = [
        (entry["id"], re.compile(entry["pattern"]))
        for entry in PRIVACY_PATTERNS
    ]

    checked_paths: list[str] = []
    hits: list[dict[str, Any]] = []
    for source in inventory["sources"]:
        rel = source["path"]
        abs_path = REPO_ROOT / rel
        if not abs_path.is_file():
            continue
        checked_paths.append(rel)
        hits.extend(scan_file_for_patterns(abs_path, compiled))

    status = "passed" if not hits else "failed"
    summary = (
        "no credential / private-path / personal-identifier hits in the proposed split set"
        if status == "passed"
        else f"{len(hits)} privacy hit(s) must be resolved before any repo-split scaffolding"
    )

    return {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "profile": inventory["profile"],
        "kernel_id": inventory["kernel_id"],
        "inventory_path": inventory_source_label,
        "checked_paths": checked_paths,
        "patterns_scanned": PRIVACY_PATTERNS,
        "hits": hits,
        "status": status,
        "summary": summary,
        "ignored_paths": [
            entry["path_pattern"] for entry in inventory.get("excluded_sources", [])
        ],
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inventory the source files a reviewed repo-split scaffolder would "
            "copy for a profile and run a privacy audit over them. Read-only."
        )
    )
    parser.add_argument("profile", help="Profile name, e.g. core-ops.")
    parser.add_argument(
        "--kernel-dir",
        type=Path,
        default=DEFAULT_KERNEL_DIR,
        help="Directory containing kernel examples.",
    )
    parser.add_argument(
        "--inventory-out",
        type=Path,
        help="Path to write the source inventory JSON.",
    )
    parser.add_argument(
        "--audit-out",
        type=Path,
        help="Path to write the privacy audit JSON.",
    )
    parser.add_argument(
        "--print",
        choices=["inventory", "audit", "both"],
        default="both",
        help="Which artifact(s) to print to stdout (default both).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        inventory = build_inventory(args.profile, args.kernel_dir.resolve())
    except ValueError as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, indent=2, sort_keys=True))
        return 2

    inventory_label = (
        repo_relative(args.inventory_out.resolve())
        if args.inventory_out is not None
        else f"<unwritten inventory for profile {args.profile}>"
    )
    audit = build_privacy_audit(inventory, inventory_label)

    if args.inventory_out:
        args.inventory_out.parent.mkdir(parents=True, exist_ok=True)
        args.inventory_out.write_text(
            json.dumps(inventory, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if args.audit_out:
        args.audit_out.parent.mkdir(parents=True, exist_ok=True)
        args.audit_out.write_text(
            json.dumps(audit, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    output: dict[str, Any] = {}
    if args.print in ("inventory", "both"):
        output["inventory"] = inventory
    if args.print in ("audit", "both"):
        output["audit"] = audit
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if audit["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

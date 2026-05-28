#!/usr/bin/env python3
"""Apply a reviewed repo-split plan — refuses to write until the contract authorizes.

Real scaffolder for ``repo-split-handoff`` mode. Reads a reviewed plan plus
the generated manifest index, re-runs the validator, re-uses
``preview_repo_split_writer.py`` to enumerate copy/scaffold actions, then —
only if the active handoff contract explicitly authorizes real runtime writes
AND the caller passes ``--execute`` — copies the source files into
``target_root``, slices the profile-index entry, and emits a rollback record
artifact.

While the active contract carries ``automation_policy.real_installer_authorized
= false`` this script will always refuse to write and exit non-zero, regardless
of ``--execute``. The script never edits global skill roots, never touches the
source repo's files, and the destination ``target_root`` must not point at a
known global skill root.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from preview_repo_split_writer import (  # noqa: E402
    SUPPORTED_MODE as REPO_SPLIT_SUPPORTED_MODE,
    build_preview as build_repo_split_preview,
    find_inventory_path,
    find_privacy_audit_path,
)
from validate_install_handoff_plan import (  # noqa: E402
    DEFAULT_CONTRACT_PATH,
    GLOBAL_SKILL_ROOTS,
    load_json,
    path_is_relative_to,
    resolve_input_path,
    validate_plan,
)

ROLLBACK_SCHEMA_VERSION = "0.1"


def sha256_hex(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def target_is_known_global(path: Path) -> bool:
    return any(path_is_relative_to(path, root) for root in GLOBAL_SKILL_ROOTS)


def gather_blockers(
    plan: dict[str, Any],
    plan_report: dict[str, Any],
    contract: dict[str, Any],
    preview: dict[str, Any],
    execute: bool,
    target_root: Path,
) -> list[str]:
    blockers: list[str] = []
    if not plan_report.get("passed"):
        blockers.append("repo-split plan failed the validator; refusing to scaffold")
    if plan.get("mode") != REPO_SPLIT_SUPPORTED_MODE:
        blockers.append(
            f"mode `{plan.get('mode')}` is not supported by this scaffolder; "
            f"only `{REPO_SPLIT_SUPPORTED_MODE}` is supported"
        )
    if not plan_report.get("mode_allowed_now"):
        blockers.append(
            f"mode `{plan.get('mode')}` is not currently executable by the active contract"
        )
    automation_policy = contract.get("automation_policy", {})
    if not isinstance(automation_policy, dict) or not automation_policy.get(
        "real_installer_authorized"
    ):
        blockers.append(
            "active handoff contract does not authorize real runtime writes "
            "(automation_policy.real_installer_authorized must be true)"
        )
    if target_is_known_global(target_root):
        blockers.append(
            "target_root falls under a known global skill root; this scaffolder never writes there"
        )
    if not execute:
        blockers.append("--execute was not passed; dry-run only")
    if preview.get("issues"):
        blockers.append("preview reported issues: " + "; ".join(preview["issues"]))
    return blockers


def execute_repo_split_actions(
    preview: dict[str, Any],
    inventory: dict[str, Any],
) -> tuple[list[str], list[str]]:
    written: list[str] = []
    created_directories: list[str] = []
    if not preview["manifests"]:
        return written, created_directories
    actions = preview["manifests"][0]["actions"]

    for action in actions:
        kind = action["kind"]
        target_path = Path(action["target_path"])
        if kind == "create-directory":
            target_path.mkdir(parents=True, exist_ok=True)
            created_directories.append(str(target_path))
        elif kind == "copy-file":
            source_path = REPO_ROOT / action["source_path"]
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target_path)
            written.append(str(target_path))
        elif kind == "write-profile-index-slice":
            target_path.parent.mkdir(parents=True, exist_ok=True)
            slice_yaml = render_profile_index_slice(inventory)
            target_path.write_text(slice_yaml, encoding="utf-8")
            written.append(str(target_path))
        elif kind == "post-write-check":
            # post-write-check actions are advisory only; the caller is responsible
            # for running them in the destination repo after the scaffold finishes.
            continue
    return written, created_directories


def slice_profile_index_yaml(source_path: Path, profile_key: str) -> str | None:
    """Extract a single profile's entry from profiles/profile-index.yaml.

    Returns the slice with the same indentation as the source, or ``None`` if
    the profile key is not found. The source is a stable, hand-written YAML
    file with two-space indentation: ``profiles:`` at column 0, each profile
    key at column 2, and per-profile fields at column 4 or deeper. Line-based
    slicing avoids a PyYAML dependency.
    """
    if not source_path.is_file():
        return None
    text = source_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    in_profiles_block = False
    in_target = False
    captured: list[str] = []

    for line in lines:
        if not in_profiles_block:
            if line.rstrip() == "profiles:":
                in_profiles_block = True
            continue
        stripped = line.strip()
        # Blank or whitespace-only line: belongs to whichever profile is active.
        if not stripped:
            if in_target:
                captured.append(line)
            continue
        if line.startswith("  ") and not line.startswith("    "):
            # Column-2 entry: either start of target profile or sibling profile.
            if stripped.startswith(f"{profile_key}:"):
                in_target = True
                captured.append(line)
                continue
            if in_target:
                # Reached the next profile; stop.
                break
            continue
        if not line.startswith("  "):
            # Left the profiles block (top-level key after the profiles map).
            break
        if in_target:
            captured.append(line)

    if not captured:
        return None

    body = "\n".join(captured)
    return (
        "# Generated profile-index slice; replace with destination-repo "
        "profile-index when scaffolding completes.\n"
        "schema_version: 0\n"
        "profiles:\n"
        f"{body}\n"
    )


def render_profile_index_slice(inventory: dict[str, Any]) -> str:
    profile_index = inventory.get("profile_index", {})
    profile = inventory.get("profile", "")
    kernel_id = inventory.get("kernel_id", profile)
    source_path = REPO_ROOT / profile_index.get("path", "profiles/profile-index.yaml")
    sliced = slice_profile_index_yaml(source_path, profile_index.get("key", profile))
    if sliced is not None:
        return sliced
    return (
        "# Profile-index slice fallback (source file or key missing).\n"
        f"# profile_index_source: {profile_index.get('path', '')}\n"
        "schema_version: 0\n"
        f"sliced_for: {profile}\n"
        f"kernel_id: {kernel_id}\n"
    )


def build_rollback_record(
    plan: dict[str, Any],
    contract_path: Path,
    written_paths: list[str],
    created_directories: list[str],
) -> dict[str, Any]:
    return {
        "schema_version": ROLLBACK_SCHEMA_VERSION,
        "plan_id": plan.get("plan_id"),
        "mode": plan.get("mode"),
        "profile": plan.get("profile"),
        "runtime": plan.get("runtime"),
        "target_root": plan.get("target_root"),
        "contract_path": str(contract_path),
        "written_paths": written_paths,
        "created_directories": created_directories,
        "restore_strategy": (
            "Delete written_paths and remove created_directories (deepest first) "
            "to roll the destination repo back to its pre-scaffold state. The "
            "source repo was not modified."
        ),
        "applied_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Apply a reviewed repo-split plan. Refuses to write until the "
            "active handoff contract authorizes real runtime writes AND "
            "--execute is passed."
        )
    )
    parser.add_argument("plan", type=Path, help="Install plan JSON path.")
    parser.add_argument(
        "--manifest-index",
        type=Path,
        required=True,
        help="Generated installable-manifest-index.json path.",
    )
    parser.add_argument(
        "--contract",
        type=Path,
        default=DEFAULT_CONTRACT_PATH,
        help="Handoff contract JSON. Defaults to the active contract.",
    )
    parser.add_argument(
        "--inventory",
        type=Path,
        help="Source inventory JSON. Auto-located when omitted.",
    )
    parser.add_argument(
        "--privacy-audit",
        type=Path,
        help="Privacy audit JSON. Auto-located when omitted.",
    )
    parser.add_argument(
        "--rollback-record",
        type=Path,
        help="Where to write the rollback record JSON after a successful scaffold.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually copy files into target_root. Without this flag the script is dry-run only.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        plan = load_json(resolve_input_path(args.plan))
        contract = load_json(resolve_input_path(args.contract))
        plan_report = validate_plan(plan, contract, args.manifest_index)
        profile = plan.get("profile", "")
        inventory_path = args.inventory or find_inventory_path(profile)
        audit_path = args.privacy_audit or find_privacy_audit_path(profile)
        inventory = (
            load_json(resolve_input_path(inventory_path))
            if inventory_path is not None
            else None
        )
        audit = (
            load_json(resolve_input_path(audit_path)) if audit_path is not None else None
        )
        preview = build_repo_split_preview(
            plan, plan_report, inventory, audit, inventory_path, audit_path
        )
        target_root = Path(plan.get("target_root", "")).expanduser()
        blockers = gather_blockers(
            plan, plan_report, contract, preview, args.execute, target_root
        )
    except ValueError as exc:
        print(
            json.dumps(
                {"applied": False, "issues": [str(exc)]},
                indent=2,
                sort_keys=True,
            )
        )
        return 2

    if blockers:
        print(
            json.dumps(
                {
                    "applied": False,
                    "plan_id": plan.get("plan_id"),
                    "mode": plan.get("mode"),
                    "validator_passed": plan_report.get("passed"),
                    "mode_allowed_now": plan_report.get("mode_allowed_now"),
                    "real_runtime_write_authorized": plan_report.get(
                        "real_runtime_write_authorized"
                    ),
                    "blockers": blockers,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1

    if inventory is None:
        print(
            json.dumps(
                {"applied": False, "issues": ["inventory not found at apply time"]},
                indent=2,
                sort_keys=True,
            )
        )
        return 1

    written_paths, created_directories = execute_repo_split_actions(preview, inventory)
    record = build_rollback_record(plan, args.contract, written_paths, created_directories)
    if args.rollback_record:
        args.rollback_record.parent.mkdir(parents=True, exist_ok=True)
        args.rollback_record.write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(
        json.dumps(
            {
                "applied": True,
                "plan_id": plan.get("plan_id"),
                "mode": plan.get("mode"),
                "target_root": str(target_root),
                "written_paths": written_paths,
                "created_directories": created_directories,
                "rollback_record": str(args.rollback_record) if args.rollback_record else None,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

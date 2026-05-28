#!/usr/bin/env python3
"""Preview the copy/scaffold actions a reviewed repo-split scaffolder would perform.

Read-only. Consumes a passing ``repo-split-handoff`` install plan plus the
generated installable-manifest index and the profile's source inventory. If the
plan passes ``validate_install_handoff_plan.py`` and the privacy audit reports
``status: passed``, the script enumerates the exact list of copy-file,
write-profile-index-slice, and post-write-check actions the future scaffolder
would emit, plus a rollback record template.

The script never writes under ``target_root`` and never edits the source repo.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from validate_install_handoff_plan import (  # noqa: E402
    DEFAULT_CONTRACT_PATH,
    _resolve_source_root,
    load_json,
    resolve_input_path,
    validate_plan,
)

PREVIEW_SCHEMA_VERSION = "0.1"
SUPPORTED_MODE = "repo-split-handoff"
INVENTORY_DIR = REPO_ROOT / "schemas" / "skill-kernel" / "repo-split"


def find_inventory_path(profile: str) -> Path | None:
    if not INVENTORY_DIR.is_dir():
        return None
    candidates = sorted(INVENTORY_DIR.glob(f"{profile}-source-inventory-*.json"))
    if not candidates:
        return None
    return candidates[-1]


def find_privacy_audit_path(profile: str) -> Path | None:
    if not INVENTORY_DIR.is_dir():
        return None
    candidates = sorted(INVENTORY_DIR.glob(f"{profile}-privacy-audit-*.json"))
    if not candidates:
        return None
    return candidates[-1]


def repo_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def actions_for_inventory(
    plan: dict[str, Any],
    inventory: dict[str, Any],
) -> tuple[list[dict[str, Any]], int, int, list[str]]:
    target_root_path = Path(plan.get("target_root", ""))
    actions: list[dict[str, Any]] = [
        {
            "kind": "create-directory",
            "target_path": str(target_root_path),
        }
    ]
    total_files = 0
    total_bytes = 0
    expected_existing: list[str] = []
    seen_dirs: set[str] = {str(target_root_path)}

    for source in inventory["sources"]:
        if not source.get("include_in_split", False):
            continue
        destination_rel = source.get("destination_path") or source["path"]
        destination = target_root_path / destination_rel
        parent = str(destination.parent)
        if parent not in seen_dirs:
            actions.append({"kind": "create-directory", "target_path": parent})
            seen_dirs.add(parent)
        actions.append(
            {
                "kind": "copy-file",
                "target_path": str(destination),
                "source_path": source["path"],
                "source_sha256": source["sha256"],
                "content_bytes": source["size_bytes"],
                "owning_skill": source.get("owning_skill", ""),
            }
        )
        total_files += 1
        total_bytes += int(source["size_bytes"])
        expected_existing.append(str(destination))

    profile_index = inventory.get("profile_index")
    if isinstance(profile_index, dict):
        destination_profile_index = target_root_path / profile_index["destination_path"]
        actions.append(
            {
                "kind": "create-directory",
                "target_path": str(destination_profile_index.parent),
            }
        )
        actions.append(
            {
                "kind": "write-profile-index-slice",
                "target_path": str(destination_profile_index),
                "source_path": profile_index["path"],
                "source": (
                    f"slice profile-index entry `{profile_index['key']}` from "
                    f"{profile_index['path']} into a minimal profile-index for the destination repo"
                ),
            }
        )
        expected_existing.append(str(destination_profile_index))

    post_write_commands = [
        "python3 scripts/validate_skills.py",
        "uv run scripts/validate_skill_taxonomy.py",
        "python3 scripts/export_skill_kernel_adapters.py --runtime all --check",
        "python3 -m unittest -v tests.test_install_plan_fixtures tests.test_install_writer_preview tests.test_repo_split_inventory",
    ]
    for command in post_write_commands:
        actions.append(
            {
                "kind": "post-write-check",
                "target_path": "<destination-repo>",
                "post_write_command": command,
            }
        )

    return actions, total_files, total_bytes, expected_existing


def build_preview(
    plan: dict[str, Any],
    plan_report: dict[str, Any],
    inventory: dict[str, Any] | None,
    audit: dict[str, Any] | None,
    inventory_path: Path | None,
    audit_path: Path | None,
) -> dict[str, Any]:
    issues: list[str] = list(plan_report.get("issues", []))
    warnings: list[str] = list(plan_report.get("warnings", []))
    mode = plan.get("mode")

    if mode != SUPPORTED_MODE:
        issues.append(
            f"mode `{mode}` is not supported by the repo-split preview; "
            f"only `{SUPPORTED_MODE}` is supported here"
        )

    if inventory is None:
        issues.append(
            f"no source inventory found for profile `{plan.get('profile')}` under "
            f"{repo_relative(INVENTORY_DIR)}/"
        )
    if audit is None:
        issues.append(
            f"no privacy audit found for profile `{plan.get('profile')}` under "
            f"{repo_relative(INVENTORY_DIR)}/"
        )
    elif audit.get("status") != "passed":
        issues.append(
            f"privacy audit status `{audit.get('status')}` blocks repo-split preview"
        )

    actions: list[dict[str, Any]] = []
    total_files = 0
    total_bytes = 0
    expected_existing: list[str] = []

    if (
        plan_report.get("passed")
        and mode == SUPPORTED_MODE
        and inventory is not None
        and audit is not None
        and audit.get("status") == "passed"
    ):
        actions, total_files, total_bytes, expected_existing = actions_for_inventory(
            plan, inventory
        )

    manifests_block: list[dict[str, Any]] = []
    if actions:
        manifests_block.append(
            {
                "kernel_id": inventory["kernel_id"] if inventory else plan.get("profile", ""),
                "runtime": plan.get("runtime", ""),
                "manifest_path": (
                    repo_relative(inventory_path)
                    if inventory_path is not None
                    else "<unspecified inventory>"
                ),
                "skill_directory": plan.get("profile", ""),
                "actions": actions,
            }
        )

    rollback = {
        "snapshot_required": True,
        "expected_existing_paths_to_check": expected_existing,
        "rollback_record_template": {
            "schema_version": "0.1",
            "plan_id": plan.get("plan_id"),
            "mode": mode,
            "target_root": plan.get("target_root"),
            "wrote_paths": [],
            "pre_existing_paths": [],
            "pre_existing_hashes": {},
            "destination_repo": plan.get("target_root"),
            "destination_commit_before_scaffold": None,
        },
    }

    return {
        "schema_version": PREVIEW_SCHEMA_VERSION,
        "plan_id": plan.get("plan_id"),
        "mode": mode,
        "profile": plan.get("profile"),
        "runtime": plan.get("runtime"),
        "target_root": plan.get("target_root"),
        "validator_passed": bool(plan_report.get("passed")),
        "real_runtime_write_authorized": bool(
            plan_report.get("real_runtime_write_authorized")
        ),
        "dry_run": True,
        "writes_during_preview": False,
        "manifests": manifests_block,
        "total_files": total_files,
        "total_bytes": total_bytes,
        "rollback": rollback,
        "supported_modes": [SUPPORTED_MODE],
        "warnings": warnings,
        "issues": issues,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Preview the copy/scaffold actions a reviewed repo-split "
            "scaffolder would emit for a passing repo-split plan. Read-only."
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
        help="Source inventory JSON. Auto-located under schemas/skill-kernel/repo-split/ when omitted.",
    )
    parser.add_argument(
        "--privacy-audit",
        type=Path,
        help="Privacy audit JSON. Auto-located alongside the inventory when omitted.",
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        default=None,
        help=(
            "Optional second root for cross-repo plan validation. Forwarded "
            "to validate_install_handoff_plan; see that script for details. "
            "Also accepts SKILL_OS_SOURCE_ROOT env var."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    source_root = _resolve_source_root(args.source_root)
    try:
        plan = load_json(resolve_input_path(args.plan))
        contract = load_json(resolve_input_path(args.contract))
        plan_report = validate_plan(plan, contract, args.manifest_index, source_root)
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
        preview = build_preview(plan, plan_report, inventory, audit, inventory_path, audit_path)
    except ValueError as exc:
        print(
            json.dumps(
                {"validator_passed": False, "issues": [str(exc)]},
                indent=2,
                sort_keys=True,
            )
        )
        return 2

    print(json.dumps(preview, indent=2, sort_keys=True))
    if preview["issues"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

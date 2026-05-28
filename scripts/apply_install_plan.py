#!/usr/bin/env python3
"""Apply a reviewed install plan — refuses to write until the contract authorizes.

Real installer for ``project-local-profile-install`` mode. Reads a reviewed
plan plus the generated manifest index, re-runs the validator, re-uses
``preview_install_writer.py`` to enumerate write actions, then — only if the
active handoff contract explicitly authorizes real runtime writes and the
caller passes ``--execute`` — performs the writes, records a snapshot of any
pre-existing target files, and emits a rollback record artifact.

While the active contract carries ``automation_policy.real_installer_authorized
= false`` this script will always refuse to write and exit non-zero, regardless
of ``--execute``. The script never edits global skill roots (``~/.codex/skills``,
``~/.agents/skills``, ``~/.claude/skills``) under any contract state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from preview_install_writer import build_preview as build_install_preview  # noqa: E402
from preview_install_writer import (  # noqa: E402
    SUPPORTED_MODES as INSTALL_SUPPORTED_MODES,
)
from validate_install_handoff_plan import (  # noqa: E402
    DEFAULT_CONTRACT_PATH,
    GLOBAL_SKILL_ROOTS,
    _resolve_source_root,
    load_json,
    path_is_relative_to,
    resolve_input_path,
    validate_plan,
)
from preview_install_writer import (  # noqa: E402
    load_manifest_index as load_install_manifest_index,
)

ROLLBACK_SCHEMA_VERSION = "0.1"


def sha256_hex(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def target_is_known_global(path: Path) -> bool:
    return any(path_is_relative_to(path, root) for root in GLOBAL_SKILL_ROOTS)


def gather_authorization_blockers(
    plan: dict[str, Any],
    plan_report: dict[str, Any],
    contract: dict[str, Any],
    preview: dict[str, Any],
    execute: bool,
    target_root: Path,
) -> list[str]:
    blockers: list[str] = []
    if not plan_report.get("passed"):
        blockers.append("install plan failed the validator; refusing to write")
    if plan.get("mode") not in INSTALL_SUPPORTED_MODES:
        blockers.append(
            f"mode `{plan.get('mode')}` is not supported by this installer; "
            f"supported modes: {', '.join(INSTALL_SUPPORTED_MODES)}"
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
            "target_root falls under a known global skill root; this installer never writes there"
        )
    if not execute:
        blockers.append("--execute was not passed; dry-run only")
    if preview.get("issues"):
        blockers.append(
            "preview reported issues: " + "; ".join(preview["issues"])
        )
    return blockers


def take_snapshot(paths: list[Path]) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    for path in paths:
        if path.is_file():
            snapshot[str(path)] = sha256_hex(path.read_bytes())
    return snapshot


def render_skill_markdown(manifest_path: Path) -> str:
    from export_skill_kernel_adapters import render_installed_skill_markdown  # local import

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return render_installed_skill_markdown(manifest)


def render_interface_yaml_from_manifest(manifest_path: Path) -> str | None:
    from export_skill_kernel_adapters import render_interface_yaml  # local import

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    interface = manifest.get("interface_metadata")
    if not isinstance(interface, dict):
        return None
    return render_interface_yaml(interface)


def execute_actions(
    preview: dict[str, Any],
    manifest_root: Path,
) -> tuple[list[str], list[Path]]:
    written: list[str] = []
    directories: list[Path] = []
    for entry in preview["manifests"]:
        manifest_path_rel = entry["manifest_path"]
        # preview emits manifest_path as the kernel's `generated_from` slug
        manifest_runtime = entry["runtime"]
        manifest_kernel_id = entry["kernel_id"]
        manifest_file = (
            manifest_root
            / manifest_runtime
            / manifest_kernel_id
            / "adapter-manifest.json"
        )
        skill_md_content: str | None = None
        interface_yaml: str | None = None
        if manifest_file.is_file():
            skill_md_content = render_skill_markdown(manifest_file)
            interface_yaml = render_interface_yaml_from_manifest(manifest_file)

        for action in entry["actions"]:
            target_path = Path(action["target_path"])
            kind = action["kind"]
            if kind == "create-directory":
                target_path.mkdir(parents=True, exist_ok=True)
                directories.append(target_path)
            elif kind == "write-skill-markdown":
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_text(skill_md_content or "", encoding="utf-8")
                written.append(str(target_path))
            elif kind == "write-interface-metadata":
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_text(interface_yaml or "", encoding="utf-8")
                written.append(str(target_path))
    return written, directories


def expected_existing_paths(preview: dict[str, Any]) -> list[Path]:
    paths: list[Path] = []
    for path_str in preview["rollback"]["expected_existing_paths_to_check"]:
        paths.append(Path(path_str))
    return paths


def build_rollback_record(
    plan: dict[str, Any],
    contract_path: Path,
    snapshot: dict[str, str],
    written_paths: list[str],
    created_directories: list[Path],
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
        "created_directories": [str(p) for p in created_directories],
        "pre_existing_files_at_target": snapshot,
        "restore_strategy": (
            "Delete written_paths; for each path in pre_existing_files_at_target, "
            "restore the file from the recorded sha256 via the rollback snapshot."
        ),
        "applied_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Apply a reviewed project-local install plan. Refuses to write "
            "until the active handoff contract authorizes real runtime writes "
            "AND --execute is passed."
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
        "--rollback-record",
        type=Path,
        help="Where to write the rollback record JSON after a successful write.",
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        default=None,
        help=(
            "Optional second root for cross-repo plan validation. Forwarded "
            "to the plan validator; see validate_install_handoff_plan for "
            "details. Also accepts SKILL_OS_SOURCE_ROOT env var."
        ),
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually write target files. Without this flag the script is dry-run only.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    source_root = _resolve_source_root(args.source_root)
    try:
        plan = load_json(resolve_input_path(args.plan))
        contract = load_json(resolve_input_path(args.contract))
        plan_report = validate_plan(plan, contract, args.manifest_index, source_root)
        manifest_index, manifest_root = load_install_manifest_index(args.manifest_index)
        preview = build_install_preview(plan, plan_report, manifest_index, manifest_root)
        target_root = Path(plan.get("target_root", "")).expanduser()
        blockers = gather_authorization_blockers(
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

    snapshot = take_snapshot(expected_existing_paths(preview))
    written_paths, created_directories = execute_actions(preview, manifest_root)
    record = build_rollback_record(
        plan, args.contract, snapshot, written_paths, created_directories
    )
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
                "rollback_record": str(args.rollback_record) if args.rollback_record else None,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

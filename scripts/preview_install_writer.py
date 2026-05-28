#!/usr/bin/env python3
"""Preview the write actions a reviewed-plan installer would perform.

This script is strictly read-only: it consumes a reviewed install plan plus a
generated installable-manifest index, re-validates the plan through
``validate_install_handoff_plan.py``, and (only if the plan passes) enumerates
the exact list of file writes a future installer would emit. It never writes
under ``target_root`` or any other runtime location.

Currently supports the ``project-local-profile-install`` mode. Other modes
(repo split, session-only exercise, global bootstrap, maintainer/debug global
install) are out of scope here: session-only writes already have their own
generator under ``export_skill_kernel_adapters.py --exercise-skill-root`` and
repo-split scaffolding is structurally different.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from export_skill_kernel_adapters import (  # noqa: E402
    render_exercised_skill_markdown,
    render_interface_yaml,
)
from validate_install_handoff_plan import (  # noqa: E402
    DEFAULT_CONTRACT_PATH,
    load_json,
    resolve_input_path,
    validate_plan,
)

PREVIEW_SCHEMA_VERSION = "0.1"
SUPPORTED_MODES = ("project-local-profile-install",)


def sha256_hex(content: str) -> str:
    return "sha256:" + hashlib.sha256(content.encode("utf-8")).hexdigest()


def load_manifest_index(index_path: Path) -> tuple[dict[str, Any], Path]:
    resolved = resolve_input_path(index_path)
    return load_json(resolved), resolved.parent


def find_manifest_entry(
    index: dict[str, Any],
    runtime: str,
    kernel_id: str,
) -> dict[str, Any] | None:
    for entry in index.get("manifests", []):
        if (
            isinstance(entry, dict)
            and entry.get("runtime") == runtime
            and entry.get("kernel_id") == kernel_id
        ):
            return entry
    return None


def load_manifest_for_request(
    index: dict[str, Any],
    manifest_root: Path,
    runtime: str,
    kernel_id: str,
) -> dict[str, Any]:
    entry = find_manifest_entry(index, runtime, kernel_id)
    if entry is None:
        raise ValueError(f"manifest index has no entry for {runtime}/{kernel_id}")
    manifest_rel = entry.get("manifest")
    if not isinstance(manifest_rel, str):
        raise ValueError(f"manifest index entry missing manifest path: {runtime}/{kernel_id}")
    manifest_path = manifest_root / manifest_rel
    return load_json(manifest_path)


def actions_for_manifest(manifest: dict[str, Any], target_root: str) -> list[dict[str, Any]]:
    install_target = manifest.get("install_target", {})
    skill_directory = install_target.get("skill_directory") or manifest.get(
        "skill_markdown", {}
    ).get("frontmatter", {}).get("name", "")
    target_root_path = Path(target_root)

    actions: list[dict[str, Any]] = [
        {
            "kind": "create-directory",
            "target_path": str(target_root_path),
        }
    ]

    skill_md = render_exercised_skill_markdown(manifest)
    skill_md_path = target_root_path / manifest["skill_markdown"]["path"]
    actions.append(
        {
            "kind": "write-skill-markdown",
            "target_path": str(skill_md_path),
            "source": f"rendered from {manifest['generated_from']} via manifest skill_markdown",
            "content_sha256": sha256_hex(skill_md),
            "content_bytes": len(skill_md.encode("utf-8")),
        }
    )

    interface_projection = manifest.get("interface_metadata")
    if isinstance(interface_projection, dict) and interface_projection.get("path"):
        interface_yaml = render_interface_yaml(interface_projection)
        interface_path = target_root_path / interface_projection["path"]
        actions.append(
            {
                "kind": "create-directory",
                "target_path": str(interface_path.parent),
            }
        )
        actions.append(
            {
                "kind": "write-interface-metadata",
                "target_path": str(interface_path),
                "source": f"rendered from {manifest['generated_from']} via manifest interface_metadata",
                "content_sha256": sha256_hex(interface_yaml),
                "content_bytes": len(interface_yaml.encode("utf-8")),
            }
        )

    return [
        {
            "kernel_id": manifest["kernel"]["kernel_id"],
            "runtime": manifest["runtime"],
            "manifest_path": manifest["generated_from"],
            "skill_directory": skill_directory,
            "actions": actions,
        }
    ]


def build_preview(
    plan: dict[str, Any],
    plan_report: dict[str, Any],
    manifest_index: dict[str, Any],
    manifest_root: Path,
) -> dict[str, Any]:
    issues: list[str] = []
    warnings: list[str] = list(plan_report.get("warnings", []))
    mode = plan.get("mode")
    if mode not in SUPPORTED_MODES:
        issues.append(
            f"mode `{mode}` is not yet supported by the writer preview; supported modes: "
            + ", ".join(SUPPORTED_MODES)
        )

    manifests_block: list[dict[str, Any]] = []
    total_files = 0
    total_bytes = 0
    expected_existing_paths: list[str] = []

    if plan_report.get("passed") and mode in SUPPORTED_MODES:
        for requested in plan.get("requested_manifests", []):
            if not isinstance(requested, dict):
                continue
            runtime = requested.get("runtime")
            kernel_id = requested.get("kernel_id")
            if not isinstance(runtime, str) or not isinstance(kernel_id, str):
                continue
            manifest = load_manifest_for_request(
                manifest_index, manifest_root, runtime, kernel_id
            )
            for entry in actions_for_manifest(manifest, plan.get("target_root", "")):
                manifests_block.append(entry)
                for action in entry["actions"]:
                    if action["kind"].startswith("write-"):
                        total_files += 1
                        total_bytes += int(action.get("content_bytes", 0))
                        expected_existing_paths.append(action["target_path"])

    rollback = {
        "snapshot_required": mode != "session-only-exercise",
        "expected_existing_paths_to_check": expected_existing_paths,
        "rollback_record_template": {
            "schema_version": "0.1",
            "plan_id": plan.get("plan_id"),
            "mode": mode,
            "target_root": plan.get("target_root"),
            "wrote_paths": [],
            "pre_existing_paths": [],
            "pre_existing_hashes": {},
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
        "supported_modes": list(SUPPORTED_MODES),
        "warnings": warnings,
        "issues": issues + list(plan_report.get("issues", [])),
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Preview the file writes a future reviewed-plan installer would "
            "emit for a single passing install plan. This script never writes "
            "runtime files."
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
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        plan = load_json(resolve_input_path(args.plan))
        contract = load_json(resolve_input_path(args.contract))
        plan_report = validate_plan(plan, contract, args.manifest_index)
        manifest_index, manifest_root = load_manifest_index(args.manifest_index)
        preview = build_preview(plan, plan_report, manifest_index, manifest_root)
    except ValueError as exc:
        print(json.dumps({"validator_passed": False, "issues": [str(exc)]}, indent=2, sort_keys=True))
        return 2

    print(json.dumps(preview, indent=2, sort_keys=True))
    if preview["issues"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

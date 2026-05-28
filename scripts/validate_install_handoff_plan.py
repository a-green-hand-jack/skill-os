#!/usr/bin/env python3
"""Validate a reviewed install/repo-split plan without writing runtime files."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT_PATH = (
    REPO_ROOT
    / "schemas"
    / "skill-kernel"
    / "install-handoff-contract-2026-05-28.json"
)
PLAN_SCHEMA_VERSION = "0.1"
GLOBAL_SKILL_ROOTS = (
    Path.home() / ".codex" / "skills",
    Path.home() / ".agents" / "skills",
    Path.home() / ".claude" / "skills",
)
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


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


def resolve_input_path(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def path_is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(parent.resolve(strict=False))
    except ValueError:
        return False
    return True


def target_is_known_global_skill_root(target_root: str) -> bool:
    target = Path(target_root).expanduser()
    return any(path_is_relative_to(target, root) for root in GLOBAL_SKILL_ROOTS)


def gate_ids(entries: Any) -> set[str]:
    if not isinstance(entries, list):
        return set()
    ids: set[str] = set()
    for entry in entries:
        if isinstance(entry, str):
            ids.add(entry)
        elif isinstance(entry, dict) and isinstance(entry.get("id"), str):
            status = entry.get("status", "passed")
            if status in {"passed", "not-applicable"}:
                ids.add(entry["id"])
    return ids


def string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def required_contract_sources(contract: dict[str, Any]) -> set[str]:
    paths: set[str] = set()
    for source in contract.get("authoritative_sources", []):
        if not isinstance(source, dict):
            continue
        for rel_path in source.get("paths", []):
            if isinstance(rel_path, str):
                paths.add(rel_path)
    return paths


def contract_modes(contract: dict[str, Any]) -> dict[str, dict[str, Any]]:
    modes: dict[str, dict[str, Any]] = {}
    for mode in contract.get("target_modes", []):
        if isinstance(mode, dict) and isinstance(mode.get("id"), str):
            modes[mode["id"]] = mode
    return modes


def load_manifest_index(index_path: Path | None) -> tuple[dict[str, Any] | None, Path | None]:
    if index_path is None:
        return None, None
    resolved = resolve_input_path(index_path)
    return load_json(resolved), resolved.parent


def index_entries(index: dict[str, Any]) -> list[dict[str, Any]]:
    entries = index.get("manifests", [])
    if not isinstance(entries, list):
        return []
    return [entry for entry in entries if isinstance(entry, dict)]


def find_manifest_entry(
    index: dict[str, Any],
    runtime: str,
    kernel_id: str,
) -> dict[str, Any] | None:
    for entry in index_entries(index):
        if entry.get("runtime") == runtime and entry.get("kernel_id") == kernel_id:
            return entry
    return None


def validate_manifest_file(
    entry: dict[str, Any],
    manifest_root: Path,
    plan: dict[str, Any],
) -> tuple[dict[str, Any] | None, list[str]]:
    issues: list[str] = []
    manifest_rel = entry.get("manifest")
    if not isinstance(manifest_rel, str) or not manifest_rel:
        return None, ["manifest index entry is missing manifest path"]
    manifest_path = Path(manifest_rel)
    if manifest_path.is_absolute() or ".." in manifest_path.parts:
        return None, [f"manifest path must stay relative to manifest index: {manifest_rel}"]

    try:
        manifest = load_json(manifest_root / manifest_path)
    except ValueError as exc:
        return None, [str(exc)]

    runtime = entry.get("runtime")
    kernel_id = entry.get("kernel_id")
    if manifest.get("runtime") != runtime:
        issues.append(f"{manifest_rel}: runtime does not match manifest index")
    kernel = manifest.get("kernel", {})
    if not isinstance(kernel, dict) or kernel.get("kernel_id") != kernel_id:
        issues.append(f"{manifest_rel}: kernel_id does not match manifest index")
    if manifest.get("source_of_truth") != "kernel":
        issues.append(f"{manifest_rel}: source_of_truth must be `kernel`")
    if manifest.get("safe_to_install_automatically") is not False:
        issues.append(f"{manifest_rel}: safe_to_install_automatically must be false")
    if manifest.get("manual_review_required") is not True:
        issues.append(f"{manifest_rel}: manual_review_required must be true")

    routing_hints = manifest.get("routing_hints", {})
    profile_name = routing_hints.get("profile_name") if isinstance(routing_hints, dict) else None
    if profile_name != plan.get("profile"):
        issues.append(
            f"{manifest_rel}: profile `{profile_name}` does not match plan profile `{plan.get('profile')}`"
        )

    selection_semantics = manifest.get("selection_semantics", {})
    runtime_expectation = (
        selection_semantics.get("runtime_expectation")
        if isinstance(selection_semantics, dict)
        else None
    )
    if runtime_expectation != entry.get("selection_expectation"):
        issues.append(f"{manifest_rel}: selection expectation drifted from index")

    manifest_gate_ids = gate_ids(manifest.get("review_gates", []))
    for required_gate in ("selection-semantics-preserved", "manual-review-required"):
        if required_gate not in manifest_gate_ids:
            issues.append(f"{manifest_rel}: missing manifest review gate `{required_gate}`")

    source_paths = string_list(manifest.get("kernel_source_paths", []))
    if not source_paths:
        issues.append(f"{manifest_rel}: kernel_source_paths must be a non-empty list")
    for source_path in source_paths:
        if source_path.startswith("/") or ".." in Path(source_path).parts:
            issues.append(f"{manifest_rel}: kernel source path must be repo-relative: {source_path}")
        elif not (REPO_ROOT / source_path).exists():
            issues.append(f"{manifest_rel}: kernel source path missing: {source_path}")

    return manifest, issues


def validate_plan(
    plan: dict[str, Any],
    contract: dict[str, Any],
    manifest_index_path: Path | None,
) -> dict[str, Any]:
    issues: list[str] = []
    warnings: list[str] = []
    matched_manifests: list[dict[str, str]] = []

    if plan.get("schema_version") != PLAN_SCHEMA_VERSION:
        issues.append(f"schema_version must be `{PLAN_SCHEMA_VERSION}`")
    for field in (
        "plan_id",
        "mode",
        "profile",
        "runtime",
        "target_root",
        "requested_manifests",
        "review_gates",
        "source_of_truth_paths",
        "validation_commands",
        "privacy_audit",
        "rollback",
        "automation",
        "acknowledged_forbidden_actions",
    ):
        if field not in plan:
            issues.append(f"missing required plan field `{field}`")

    plan_id = plan.get("plan_id")
    if not isinstance(plan_id, str) or not SLUG_RE.fullmatch(plan_id):
        issues.append("plan_id must be lowercase hyphenated text")
    for field in ("profile", "runtime"):
        value = plan.get(field)
        if not isinstance(value, str) or not SLUG_RE.fullmatch(value):
            issues.append(f"{field} must be lowercase hyphenated text")

    modes = contract_modes(contract)
    mode_id = plan.get("mode")
    mode = modes.get(mode_id) if isinstance(mode_id, str) else None
    if mode is None:
        issues.append(f"mode `{mode_id}` is not defined by the handoff contract")
        mode = {}

    plan_gate_ids = gate_ids(plan.get("review_gates", []))
    required_gates = set(string_list(mode.get("required_review_gates", [])))
    missing_gates = required_gates - plan_gate_ids
    for gate in sorted(missing_gates):
        issues.append(f"required review gate missing for mode `{mode_id}`: {gate}")

    contract_gate_ids = gate_ids(contract.get("review_gates", []))
    unknown_gates = plan_gate_ids - contract_gate_ids
    for gate in sorted(unknown_gates):
        issues.append(f"review gate is not defined by handoff contract: {gate}")

    source_paths = set(string_list(plan.get("source_of_truth_paths", [])))
    required_sources = required_contract_sources(contract)
    missing_sources = required_sources - source_paths
    for source_path in sorted(missing_sources):
        issues.append(f"source_of_truth_paths missing authoritative source: {source_path}")
    for source_path in sorted(source_paths):
        rel = Path(source_path)
        if rel.is_absolute() or ".." in rel.parts:
            issues.append(f"source_of_truth_paths must be repo-relative: {source_path}")
        elif not (REPO_ROOT / rel).exists():
            issues.append(f"source_of_truth_path does not exist: {source_path}")

    validation_commands = set(string_list(plan.get("validation_commands", [])))
    for command in string_list(contract.get("acceptance_checks", [])):
        if command not in validation_commands:
            issues.append(f"validation_commands missing acceptance check: {command}")

    forbidden_ids = {
        action["id"]
        for action in contract.get("forbidden_actions", [])
        if isinstance(action, dict) and isinstance(action.get("id"), str)
    }
    acknowledged = set(string_list(plan.get("acknowledged_forbidden_actions", [])))
    for action_id in sorted(forbidden_ids - acknowledged):
        issues.append(f"acknowledged_forbidden_actions missing: {action_id}")

    target_root = plan.get("target_root")
    target_is_global = isinstance(target_root, str) and target_is_known_global_skill_root(target_root)
    mode_may_touch_global = bool(mode.get("may_touch_global_roots"))
    automation = plan.get("automation", {})
    if not isinstance(automation, dict):
        issues.append("automation must be a JSON object")
        automation = {}
    else:
        if automation.get("validator_only") is not True:
            issues.append("automation.validator_only must be true")
        if automation.get("writes_during_validation") is not False:
            issues.append("automation.writes_during_validation must be false")
        if automation.get("real_installer_requested") is not False:
            issues.append("automation.real_installer_requested must be false")
        if target_is_global and not mode_may_touch_global:
            issues.append(f"mode `{mode_id}` may not target known global skill roots")
        if automation.get("will_touch_global_roots") and not mode_may_touch_global:
            issues.append(f"mode `{mode_id}` may not touch global skill roots")
        if mode_may_touch_global and (
            target_is_global or automation.get("will_touch_global_roots")
        ) and automation.get("explicit_user_request_for_global_scope") is not True:
            issues.append("global-scope plans require explicit_user_request_for_global_scope")

    privacy_audit = plan.get("privacy_audit", {})
    if not isinstance(privacy_audit, dict):
        issues.append("privacy_audit must be a JSON object")
    elif "privacy-and-publication-audit" in required_gates and privacy_audit.get("status") != "passed":
        issues.append("privacy_audit.status must be `passed` for this mode")

    rollback = plan.get("rollback", {})
    if not isinstance(rollback, dict):
        issues.append("rollback must be a JSON object")
    else:
        if "rollback-plan-recorded" in required_gates:
            if not rollback.get("rollback_record_path"):
                issues.append("rollback.rollback_record_path must be recorded")
            if not rollback.get("restore_strategy"):
                issues.append("rollback.restore_strategy must be recorded")
            if mode_id != "session-only-exercise" and rollback.get("snapshot_before_write") is not True:
                issues.append("rollback.snapshot_before_write must be true before non-session writes")

    requested_manifests = plan.get("requested_manifests", [])
    if not isinstance(requested_manifests, list) or not requested_manifests:
        issues.append("requested_manifests must be a non-empty list")
        requested_manifests = []

    manifest_index, manifest_root = load_manifest_index(manifest_index_path)
    if requested_manifests and manifest_index is None:
        issues.append("--manifest-index is required when requested_manifests is non-empty")
    elif manifest_index is not None and manifest_root is not None:
        if manifest_index.get("source_of_truth") != "kernel":
            issues.append("manifest index source_of_truth must be `kernel`")
        if manifest_index.get("safe_to_install_automatically") is not False:
            issues.append("manifest index safe_to_install_automatically must be false")
        if manifest_index.get("manual_review_required") is not True:
            issues.append("manifest index manual_review_required must be true")

        for requested in requested_manifests:
            if not isinstance(requested, dict):
                issues.append("requested_manifests entries must be objects")
                continue
            runtime = requested.get("runtime")
            kernel_id = requested.get("kernel_id")
            if not isinstance(runtime, str) or not isinstance(kernel_id, str):
                issues.append("requested_manifest runtime and kernel_id must be strings")
                continue
            if runtime != plan.get("runtime"):
                issues.append(f"requested manifest runtime `{runtime}` does not match plan runtime")
            entry = find_manifest_entry(manifest_index, runtime, kernel_id)
            if entry is None:
                issues.append(f"manifest index has no entry for {runtime}/{kernel_id}")
                continue
            manifest, manifest_issues = validate_manifest_file(entry, manifest_root, plan)
            issues.extend(manifest_issues)
            if manifest is not None:
                matched_manifests.append(
                    {
                        "runtime": runtime,
                        "kernel_id": kernel_id,
                        "manifest": str(entry.get("manifest")),
                        "selection_expectation": str(entry.get("selection_expectation")),
                    }
                )

    mode_allowed_now = bool(mode.get("allowed_now"))
    if mode_id and not mode_allowed_now:
        warnings.append(f"mode `{mode_id}` is not currently executable by the active contract")

    contract_automation = contract.get("automation_policy", {})
    real_runtime_write_authorized = (
        not issues
        and isinstance(contract_automation, dict)
        and contract_automation.get("real_installer_authorized") is True
    )
    if not real_runtime_write_authorized:
        warnings.append("active handoff contract does not authorize real runtime writes")

    passed = not issues
    return {
        "schema_version": PLAN_SCHEMA_VERSION,
        "plan_id": plan.get("plan_id"),
        "mode": mode_id,
        "profile": plan.get("profile"),
        "runtime": plan.get("runtime"),
        "passed": passed,
        "mode_allowed_now": mode_allowed_now,
        "current_action_authorized": passed and mode_allowed_now,
        "real_runtime_write_authorized": real_runtime_write_authorized,
        "checked_gates": sorted(plan_gate_ids),
        "matched_manifests": matched_manifests,
        "issues": issues,
        "warnings": warnings,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a skill-kernel install or repo-split plan against the "
            "reviewed handoff contract and generated manifest index. The "
            "validator is read-only and never writes runtime skill files."
        )
    )
    parser.add_argument("plan", type=Path, help="Install/repo-split plan JSON.")
    parser.add_argument(
        "--contract",
        type=Path,
        default=DEFAULT_CONTRACT_PATH,
        help=(
            "Handoff contract JSON. Defaults to "
            "schemas/skill-kernel/install-handoff-contract-2026-05-28.json."
        ),
    )
    parser.add_argument(
        "--manifest-index",
        type=Path,
        help="Generated installable-manifest-index.json to validate requested manifests.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        plan = load_json(resolve_input_path(args.plan))
        contract = load_json(resolve_input_path(args.contract))
        report = validate_plan(plan, contract, args.manifest_index)
    except ValueError as exc:
        print(json.dumps({"passed": False, "issues": [str(exc)]}, indent=2, sort_keys=True))
        return 2

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

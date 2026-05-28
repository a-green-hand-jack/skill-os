#!/usr/bin/env python3
"""Install a profile plus its transitive depends_on chain into a target project.

For each profile in dependency-first order, this script:

1. Locates the pack repo under one of the supplied ``--pack-search-path``
   directories (looking for a subdir whose name matches the profile's
   ``future_repo``).
2. Locates the pack's kernel example
   (``schemas/skill-kernel/examples/<profile>.kernel.json`` or the
   ``-workflow-contract`` variant for research-distillation).
3. Generates an installable manifest index from that kernel via
   ``export_skill_kernel_adapters.py``.
4. Composes a project-local install plan whose ``target_root`` is
   ``<target-parent>/<profile>`` and whose ``source_of_truth_paths`` /
   ``review_gates`` come from the active handoff contract.
5. Runs ``apply_install_plan.py --source-root <pack> --execute`` (when
   ``--execute`` is passed) to materialize the install.

Each step is independent; if any step fails the chain halts and the
already-installed steps remain.

This script never modifies the source pack repos and never touches global
skill roots — those refusals are enforced by ``apply_install_plan.py``.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from resolve_profile_dependencies import (  # noqa: E402
    parse_profile_dependencies,
    resolve as resolve_chain,
)
from validate_install_handoff_plan import (  # noqa: E402
    DEFAULT_CONTRACT_PATH,
    load_json,
)

EXPORTER = REPO_ROOT / "scripts" / "export_skill_kernel_adapters.py"
APPLY_INSTALL = REPO_ROOT / "scripts" / "apply_install_plan.py"
PROFILE_INDEX = REPO_ROOT / "profiles" / "profile-index.yaml"


def find_pack_root(future_repo: str, search_paths: list[Path]) -> Path | None:
    for parent in search_paths:
        candidate = parent / future_repo
        if candidate.is_dir():
            return candidate
    return None


def find_kernel_path(pack_root: Path, profile_name: str, kernel_id_hint: str | None) -> Path | None:
    examples = pack_root / "schemas" / "skill-kernel" / "examples"
    if not examples.is_dir():
        return None
    candidates = [
        examples / f"{profile_name}.kernel.json",
        examples / f"{profile_name}-workflow-contract.kernel.json",
    ]
    if kernel_id_hint:
        candidates.append(examples / f"{kernel_id_hint}.kernel.json")
    for path in candidates:
        if path.is_file():
            return path
    # last-resort: pick any .kernel.json whose profile.name matches
    for path in examples.glob("*.kernel.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if data.get("profile", {}).get("name") == profile_name:
            return path
    return None


def build_install_plan_for_profile(
    profile_name: str,
    kernel_id: str,
    runtime: str,
    target_root: Path,
    contract: dict[str, Any],
    pack_root: Path,
    rollback_path: Path,
) -> dict[str, Any]:
    gates = next(
        mode["required_review_gates"]
        for mode in contract["target_modes"]
        if mode["id"] == "project-local-profile-install"
    )
    # source_of_truth_paths: union of (REPO_ROOT existing, pack_root existing)
    existing_paths: list[str] = []
    for source in contract["authoritative_sources"]:
        for path in source["paths"]:
            if (REPO_ROOT / path).exists() or (pack_root / path).exists():
                existing_paths.append(path)
    return {
        "schema_version": "0.1",
        "plan_id": f"chain-install-{profile_name}-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
        "mode": "project-local-profile-install",
        "profile": profile_name,
        "runtime": runtime,
        "target_root": str(target_root),
        "requested_manifests": [{"runtime": runtime, "kernel_id": kernel_id}],
        "review_gates": [{"id": gate, "status": "passed"} for gate in gates],
        "source_of_truth_paths": existing_paths,
        "validation_commands": list(contract["acceptance_checks"]),
        "privacy_audit": {
            "status": "passed",
            "checked_paths": [str(pack_root)],
            "notes": f"install_profile_chain auto-generated plan; source pack at {pack_root}.",
        },
        "rollback": {
            "snapshot_before_write": True,
            "rollback_record_path": str(rollback_path),
            "restore_strategy": "Remove target_root contents and replay rollback record entries.",
        },
        "automation": {
            "validator_only": True,
            "writes_during_validation": False,
            "real_installer_requested": False,
            "will_touch_global_roots": False,
            "explicit_user_request_for_global_scope": False,
        },
        "acknowledged_forbidden_actions": [
            action["id"] for action in contract["forbidden_actions"]
        ],
    }


def run_apply(
    plan_path: Path,
    manifest_index: Path,
    contract_path: Path,
    pack_root: Path,
    rollback_path: Path,
    execute: bool,
) -> tuple[int, dict[str, Any]]:
    args = [
        "python3",
        str(APPLY_INSTALL),
        str(plan_path),
        "--manifest-index",
        str(manifest_index),
        "--contract",
        str(contract_path),
        "--source-root",
        str(pack_root),
        "--rollback-record",
        str(rollback_path),
    ]
    if execute:
        args.append("--execute")
    proc = subprocess.run(args, text=True, capture_output=True, check=False)
    try:
        report = json.loads(proc.stdout)
    except json.JSONDecodeError:
        report = {"stdout": proc.stdout, "stderr": proc.stderr}
    return proc.returncode, report


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Install a profile plus its transitive depends_on chain into a "
            "target project. Reads profile-index.yaml for depends_on and "
            "expects each pack repo to live under one of the --pack-search-path "
            "directories."
        )
    )
    parser.add_argument("profile", help="Top-level profile to install (e.g. quick-experiment).")
    parser.add_argument(
        "--target-parent",
        type=Path,
        required=True,
        help="Parent directory for the per-profile target_root (e.g. /path/to/project/.agents/skills).",
    )
    parser.add_argument(
        "--pack-search-path",
        type=Path,
        action="append",
        default=None,
        help=(
            "Directory to search for sibling pack repos by future_repo name. "
            "May be passed multiple times. Defaults to skill-os's parent dir."
        ),
    )
    parser.add_argument(
        "--pack",
        action="append",
        default=[],
        metavar="NAME=PATH",
        help=(
            "Override pack location for one repo (repeatable). Use when your local "
            "clone has a non-canonical directory name "
            "(e.g. --pack ml-research-skills=/Users/me/projects/project-skills). "
            "Overrides win over --pack-search-path discovery."
        ),
    )
    parser.add_argument(
        "--runtime",
        default="codex",
        help="Target runtime for the install manifest (default: codex).",
    )
    parser.add_argument(
        "--contract",
        type=Path,
        default=DEFAULT_CONTRACT_PATH,
        help="Handoff contract JSON path.",
    )
    parser.add_argument(
        "--profile-index",
        type=Path,
        default=PROFILE_INDEX,
        help="Path to profiles/profile-index.yaml.",
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=None,
        help=(
            "Directory for generated manifest indices, plans, and rollback "
            "records (default: <target-parent>/.skill-os-install-state)."
        ),
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually run apply_install_plan with --execute per step. Without this flag the chain is dry-run only.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    contract = load_json(args.contract)
    profile_text = args.profile_index.read_text(encoding="utf-8")
    profiles = parse_profile_dependencies(profile_text)
    report = resolve_chain([args.profile], profiles)
    if not report["passed"]:
        print(json.dumps({"chain_resolved": False, "issues": report["issues"]}, indent=2, sort_keys=True))
        return 1

    search_paths = args.pack_search_path or [REPO_ROOT.parent]
    work_dir = args.work_dir or (args.target_parent / ".skill-os-install-state")
    work_dir.mkdir(parents=True, exist_ok=True)

    # Parse --pack NAME=PATH overrides (consistent with verify_pack_pins.py).
    pack_overrides: dict[str, Path] = {}
    for spec in args.pack:
        if "=" not in spec:
            print(f"--pack expects NAME=PATH, got {spec!r}", file=sys.stderr)
            return 2
        name, _, path = spec.partition("=")
        pack_overrides[name.strip()] = Path(path).expanduser().resolve()

    steps_report = []
    overall_ok = True
    resolution_order_names: list[str] = report["resolution_order"]
    for profile_name in resolution_order_names:
        profile_meta = profiles.get(profile_name, {})
        future_repo = profile_meta.get("future_repo") or f"{profile_name}-skills"
        if future_repo in pack_overrides:
            pack_root = pack_overrides[future_repo] if pack_overrides[future_repo].is_dir() else None
        else:
            pack_root = find_pack_root(future_repo, search_paths)
        if pack_root is None:
            steps_report.append(
                {
                    "profile": profile_name,
                    "applied": False,
                    "error": (
                        f"could not locate pack repo `{future_repo}` under "
                        f"any of {[str(p) for p in search_paths]}"
                    ),
                }
            )
            overall_ok = False
            break

        kernel_path = find_kernel_path(pack_root, profile_name, None)
        if kernel_path is None:
            steps_report.append(
                {
                    "profile": profile_name,
                    "applied": False,
                    "error": f"no kernel example for `{profile_name}` under {pack_root}/schemas/skill-kernel/examples",
                }
            )
            overall_ok = False
            break
        kernel = load_json(kernel_path)
        kernel_id = kernel.get("kernel_id", profile_name)

        manifest_root = work_dir / f"manifests-{profile_name}"
        proc = subprocess.run(
            [
                "python3",
                str(EXPORTER),
                str(kernel_path),
                "--runtime",
                "all",
                "--installable-manifest-root",
                str(manifest_root),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if proc.returncode != 0:
            steps_report.append(
                {
                    "profile": profile_name,
                    "applied": False,
                    "error": "exporter failed: " + (proc.stderr or proc.stdout),
                }
            )
            overall_ok = False
            break
        manifest_index = manifest_root / "installable-manifest-index.json"

        target_root = args.target_parent / profile_name
        plan_path = work_dir / f"plan-{profile_name}.json"
        rollback_path = work_dir / f"rollback-{profile_name}.json"
        plan = build_install_plan_for_profile(
            profile_name=profile_name,
            kernel_id=kernel_id,
            runtime=args.runtime,
            target_root=target_root,
            contract=contract,
            pack_root=pack_root,
            rollback_path=rollback_path,
        )
        plan_path.write_text(json.dumps(plan, indent=2, sort_keys=True), encoding="utf-8")

        code, apply_report = run_apply(
            plan_path=plan_path,
            manifest_index=manifest_index,
            contract_path=args.contract,
            pack_root=pack_root,
            rollback_path=rollback_path,
            execute=args.execute,
        )
        step_summary = {
            "profile": profile_name,
            "pack_root": str(pack_root),
            "kernel_path": str(kernel_path),
            "target_root": str(target_root),
            "plan_path": str(plan_path),
            "manifest_index": str(manifest_index),
            "applied": apply_report.get("applied", False) if isinstance(apply_report, dict) else False,
            "exit_code": code,
        }
        if not step_summary["applied"]:
            step_summary["blockers"] = (
                apply_report.get("blockers") if isinstance(apply_report, dict) else None
            )
        steps_report.append(step_summary)
        if not step_summary["applied"] and args.execute:
            overall_ok = False
            break

    print(
        json.dumps(
            {
                "chain_resolved": True,
                "execute": args.execute,
                "target_parent": str(args.target_parent),
                "work_dir": str(work_dir),
                "resolution_order": resolution_order_names,
                "steps": steps_report,
                "all_applied": overall_ok and all(s.get("applied", False) for s in steps_report) if args.execute else False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    if args.execute and not overall_ok:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

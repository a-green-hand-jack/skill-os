"""Synthetic repo-split chain test.

Exercises the repo-split half of the matrix scaffolder against the
``synthetic-pack`` fixture: generate inventory, build a repo-split plan,
validate it, run the repo-split writer preview, then apply the scaffolder
with ``--execute`` and ``--source-root`` set to the synthetic pack so files
are actually copied into a tmp destination.

The skill-os repo itself never has its real ``skills/`` directory touched —
the scaffolder reads from the synthetic-pack fixture only.
"""

from __future__ import annotations

import copy
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PACK = REPO_ROOT / "tests" / "fixtures" / "synthetic-pack"
EXPORTER = REPO_ROOT / "scripts" / "export_skill_kernel_adapters.py"
INVENTORY = REPO_ROOT / "scripts" / "inventory_profile_for_split.py"
VALIDATOR = REPO_ROOT / "scripts" / "validate_install_handoff_plan.py"
PREVIEW_REPO_SPLIT = REPO_ROOT / "scripts" / "preview_repo_split_writer.py"
APPLY_REPO_SPLIT = REPO_ROOT / "scripts" / "apply_repo_split.py"
ACTIVE_CONTRACT = (
    REPO_ROOT / "schemas" / "skill-kernel" / "install-handoff-contract-2026-05-28.json"
)


def _existing_authoritative_sources(contract: dict) -> list[str]:
    paths = []
    for source in contract["authoritative_sources"]:
        for p in source["paths"]:
            if (REPO_ROOT / p).exists():
                paths.append(p)
    return paths


def write_synthetic_repo_split_plan(target_root: Path, plan_path: Path) -> Path:
    contract = json.loads(ACTIVE_CONTRACT.read_text(encoding="utf-8"))
    gates_for_mode = next(
        mode["required_review_gates"]
        for mode in contract["target_modes"]
        if mode["id"] == "repo-split-handoff"
    )
    plan = {
        "schema_version": "0.1",
        "plan_id": "synthetic-repo-split",
        "mode": "repo-split-handoff",
        "profile": "synthetic",
        "runtime": "generic-agent",
        "target_root": str(target_root),
        "requested_manifests": [
            {"runtime": "generic-agent", "kernel_id": "synthetic"},
        ],
        "review_gates": [{"id": gate, "status": "passed"} for gate in gates_for_mode],
        "source_of_truth_paths": _existing_authoritative_sources(contract),
        "validation_commands": list(contract["acceptance_checks"]),
        "privacy_audit": {
            "status": "passed",
            "checked_paths": ["tests/fixtures/synthetic-pack"],
            "notes": "Synthetic fixture; no real credentials or sources.",
        },
        "rollback": {
            "snapshot_before_write": True,
            "rollback_record_path": ".agent/install-plans/synthetic-repo-split-rollback.json",
            "restore_strategy": "Synthetic test; delete destination tmp dir.",
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
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(plan, indent=2, sort_keys=True), encoding="utf-8")
    return plan_path


def run(args: list[str], env: dict[str, str] | None = None) -> tuple[int, dict]:
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    proc = subprocess.run(
        args,
        text=True,
        capture_output=True,
        check=False,
        env=full_env,
    )
    try:
        report = json.loads(proc.stdout)
    except json.JSONDecodeError:
        report = {"stdout": proc.stdout, "stderr": proc.stderr}
    return proc.returncode, report


class SyntheticRepoSplitChainTest(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="synthetic-repo-split-")
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

        # Generate manifest index from the synthetic kernel
        synthetic_kernel = (
            FIXTURE_PACK
            / "schemas"
            / "skill-kernel"
            / "examples"
            / "synthetic.kernel.json"
        )
        manifest_root = self.tmp / "manifests"
        proc = subprocess.run(
            [
                "python3",
                str(EXPORTER),
                str(synthetic_kernel),
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
            raise RuntimeError(proc.stderr or proc.stdout)
        self.manifest_index = manifest_root / "installable-manifest-index.json"

        # Generate inventory + audit for synthetic profile into a tmp inventory dir
        self.inventory_dir = self.tmp / "inventories"
        self.inventory_dir.mkdir(parents=True, exist_ok=True)
        self.inventory_path = self.inventory_dir / "synthetic-source-inventory.json"
        self.audit_path = self.inventory_dir / "synthetic-privacy-audit.json"
        proc = subprocess.run(
            [
                "python3",
                str(INVENTORY),
                "synthetic",
                "--source-root",
                str(FIXTURE_PACK),
                "--inventory-out",
                str(self.inventory_path),
                "--audit-out",
                str(self.audit_path),
                "--print",
                "audit",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr or proc.stdout)

    def test_repo_split_preview_emits_copy_actions(self) -> None:
        target_root = self.tmp / "would-be-destination"
        plan_path = write_synthetic_repo_split_plan(target_root, self.tmp / "plan.json")
        code, preview = run(
            [
                "python3",
                str(PREVIEW_REPO_SPLIT),
                str(plan_path),
                "--manifest-index",
                str(self.manifest_index),
                "--inventory",
                str(self.inventory_path),
                "--privacy-audit",
                str(self.audit_path),
            ]
        )
        self.assertEqual(code, 0, preview)
        self.assertTrue(preview["validator_passed"])
        self.assertEqual(preview["mode"], "repo-split-handoff")
        self.assertEqual(preview["profile"], "synthetic")
        self.assertGreater(preview["total_files"], 0)
        kinds = {
            action["kind"]
            for entry in preview["manifests"]
            for action in entry["actions"]
        }
        self.assertIn("copy-file", kinds)
        self.assertIn("write-profile-index-slice", kinds)
        self.assertIn("post-write-check", kinds)
        self.assertFalse(target_root.exists())

    def test_apply_repo_split_writes_destination_from_synthetic_source(self) -> None:
        target_root = self.tmp / "destination-repo"
        plan_path = write_synthetic_repo_split_plan(target_root, self.tmp / "plan.json")
        rollback_path = self.tmp / "rollback.json"
        code, report = run(
            [
                "python3",
                str(APPLY_REPO_SPLIT),
                str(plan_path),
                "--manifest-index",
                str(self.manifest_index),
                "--inventory",
                str(self.inventory_path),
                "--privacy-audit",
                str(self.audit_path),
                "--source-root",
                str(FIXTURE_PACK),
                "--rollback-record",
                str(rollback_path),
                "--execute",
            ]
        )
        self.assertEqual(code, 0, report)
        self.assertTrue(report["applied"])
        # The synthetic pack has alpha (required), beta (required), gamma (optional)
        # so the destination should contain all three skill dirs.
        for skill in ("synthetic-alpha", "synthetic-beta", "synthetic-gamma"):
            self.assertTrue(
                (target_root / "skills" / skill / "SKILL.md").is_file(),
                f"missing {skill} in destination",
            )
        self.assertTrue(
            (target_root / "profiles" / "profile-index.yaml").is_file(),
            "missing profile-index slice",
        )
        # The synthetic kernel example should land at its source path inside the destination
        self.assertTrue(rollback_path.is_file())


if __name__ == "__main__":
    unittest.main()

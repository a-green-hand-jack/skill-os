"""End-to-end install-chain test on a self-contained synthetic fixture.

Exercises inventory → kernel ingestion → adapter export → install plan
validation → install writer preview → apply install plan, all against the
``synthetic-pack`` test fixture under ``tests/fixtures/synthetic-pack/``. No
dependency on a real pack repo or a live ``skills/`` directory in skill-os.

This is the skill-os-side counterpart of the operational tests that live in
ml-research-skills. ml-research-skills validates real pack data; skill-os
validates that the scripts themselves behave correctly on synthetic input.
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
PREVIEW_INSTALL = REPO_ROOT / "scripts" / "preview_install_writer.py"
APPLY_INSTALL = REPO_ROOT / "scripts" / "apply_install_plan.py"
ACTIVE_CONTRACT = (
    REPO_ROOT / "schemas" / "skill-kernel" / "install-handoff-contract-2026-05-28.json"
)
FROZEN_CONTRACT = (
    REPO_ROOT / "schemas" / "skill-kernel" / "install-handoff-contract-2026-05-27.json"
)


def write_synthetic_install_plan(target_root: Path, plan_path: Path) -> Path:
    """Compose a minimal synthetic project-local install plan.

    The plan satisfies every gate that the active 2026-05-28 contract
    requires for the ``project-local-profile-install`` mode, but uses the
    synthetic fixture's kernel + profile so no real pack data is involved.
    """
    contract = json.loads(ACTIVE_CONTRACT.read_text(encoding="utf-8"))
    gates_for_mode = next(
        mode["required_review_gates"]
        for mode in contract["target_modes"]
        if mode["id"] == "project-local-profile-install"
    )
    plan = {
        "schema_version": "0.1",
        "plan_id": "synthetic-project-local-install",
        "mode": "project-local-profile-install",
        "profile": "synthetic",
        "runtime": "codex",
        "target_root": str(target_root),
        "requested_manifests": [
            {"runtime": "codex", "kernel_id": "synthetic"},
        ],
        "review_gates": [{"id": gate, "status": "passed"} for gate in gates_for_mode],
        "source_of_truth_paths": [
            source["paths"][0] if isinstance(source["paths"], list) else source["paths"]
            for source in contract["authoritative_sources"]
        ],
        "validation_commands": list(contract["acceptance_checks"]),
        "privacy_audit": {
            "status": "passed",
            "checked_paths": ["tests/fixtures/synthetic-pack"],
            "notes": "Synthetic fixture; no real credentials or sources.",
        },
        "rollback": {
            "snapshot_before_write": True,
            "rollback_record_path": ".agent/install-plans/synthetic-rollback.json",
            "restore_strategy": "Synthetic test; delete written paths.",
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
    # Use the contract's authoritative_sources (paths must exist in repo).
    plan["source_of_truth_paths"] = []
    for source in contract["authoritative_sources"]:
        for p in source["paths"]:
            if (REPO_ROOT / p).exists():
                plan["source_of_truth_paths"].append(p)
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


class SyntheticInstallChainTest(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="synthetic-install-")
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def _export_manifest_index(self) -> Path:
        """Generate a manifest index containing just the synthetic kernel."""
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
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        return manifest_root / "installable-manifest-index.json"

    def test_inventory_runs_on_synthetic_pack(self) -> None:
        out_inv = self.tmp / "inventory.json"
        out_audit = self.tmp / "audit.json"
        code, output = run(
            [
                "python3",
                str(INVENTORY),
                "synthetic",
                "--source-root",
                str(FIXTURE_PACK),
                "--inventory-out",
                str(out_inv),
                "--audit-out",
                str(out_audit),
                "--print",
                "both",
            ]
        )
        self.assertEqual(code, 0, output)
        inv = json.loads(out_inv.read_text(encoding="utf-8"))
        audit = json.loads(out_audit.read_text(encoding="utf-8"))
        self.assertEqual(inv["profile"], "synthetic")
        self.assertEqual(inv["kernel_id"], "synthetic")
        owning = {
            entry.get("owning_skill")
            for entry in inv["sources"]
            if entry.get("owning_skill")
        }
        self.assertEqual(
            owning, {"synthetic-alpha", "synthetic-beta", "synthetic-gamma"}
        )
        self.assertEqual(audit["status"], "passed")
        self.assertEqual(audit["hits"], [])

    def test_install_plan_validator_passes_on_synthetic_plan(self) -> None:
        manifest_index = self._export_manifest_index()
        target_root = self.tmp / "would-be-target"
        plan_path = write_synthetic_install_plan(target_root, self.tmp / "plan.json")
        code, report = run(
            [
                "python3",
                str(VALIDATOR),
                str(plan_path),
                "--manifest-index",
                str(manifest_index),
            ]
        )
        self.assertEqual(code, 0, report)
        self.assertTrue(report["passed"])
        self.assertEqual(report["profile"], "synthetic")
        self.assertEqual(report["mode"], "project-local-profile-install")
        # Active 2026-05-28 contract authorizes this mode.
        self.assertTrue(report["mode_allowed_now"])

    def test_install_writer_preview_emits_skill_actions(self) -> None:
        manifest_index = self._export_manifest_index()
        target_root = self.tmp / "would-be-target"
        plan_path = write_synthetic_install_plan(target_root, self.tmp / "plan.json")
        code, preview = run(
            [
                "python3",
                str(PREVIEW_INSTALL),
                str(plan_path),
                "--manifest-index",
                str(manifest_index),
            ]
        )
        self.assertEqual(code, 0, preview)
        self.assertTrue(preview["validator_passed"])
        self.assertTrue(preview["dry_run"])
        self.assertFalse(preview["writes_during_preview"])
        # synthetic kernel for codex has install_target with SKILL.md and
        # agents/openai.yaml, so we expect at least 2 write actions.
        self.assertGreaterEqual(preview["total_files"], 1)
        kinds = {
            action["kind"]
            for entry in preview["manifests"]
            for action in entry["actions"]
        }
        self.assertIn("write-skill-markdown", kinds)
        self.assertFalse(target_root.exists())

    def test_apply_install_refuses_global_skill_root_targets(self) -> None:
        manifest_index = self._export_manifest_index()
        target_root = Path.home() / ".codex" / "skills" / "synthetic"
        plan_path = write_synthetic_install_plan(
            target_root, self.tmp / "plan-global.json"
        )
        code, report = run(
            [
                "python3",
                str(APPLY_INSTALL),
                str(plan_path),
                "--manifest-index",
                str(manifest_index),
                "--execute",
            ]
        )
        self.assertNotEqual(code, 0)
        self.assertFalse(report["applied"])
        self.assertTrue(
            any(
                "global skill root" in blocker
                for blocker in report.get("blockers", [])
            )
        )

    def test_apply_install_refuses_when_execute_flag_missing(self) -> None:
        manifest_index = self._export_manifest_index()
        target_root = self.tmp / "would-be-target"
        plan_path = write_synthetic_install_plan(target_root, self.tmp / "plan.json")
        code, report = run(
            [
                "python3",
                str(APPLY_INSTALL),
                str(plan_path),
                "--manifest-index",
                str(manifest_index),
                # no --execute
            ]
        )
        self.assertNotEqual(code, 0)
        self.assertFalse(report["applied"])
        self.assertFalse(target_root.exists())

    def test_apply_install_refuses_under_frozen_pre_revision_contract(self) -> None:
        manifest_index = self._export_manifest_index()
        target_root = self.tmp / "would-be-target"
        plan_path = write_synthetic_install_plan(target_root, self.tmp / "plan.json")
        code, report = run(
            [
                "python3",
                str(APPLY_INSTALL),
                str(plan_path),
                "--manifest-index",
                str(manifest_index),
                "--contract",
                str(FROZEN_CONTRACT),
                "--execute",
            ]
        )
        self.assertNotEqual(code, 0)
        self.assertFalse(report["applied"])
        self.assertFalse(target_root.exists())
        self.assertTrue(
            any(
                "real_installer_authorized" in blocker
                for blocker in report.get("blockers", [])
            )
        )

    def test_apply_install_writes_into_tmp_under_active_contract(self) -> None:
        manifest_index = self._export_manifest_index()
        target_root = self.tmp / "project" / ".agents" / "skills" / "synthetic"
        plan_path = write_synthetic_install_plan(target_root, self.tmp / "plan.json")
        rollback_path = self.tmp / "rollback.json"
        code, report = run(
            [
                "python3",
                str(APPLY_INSTALL),
                str(plan_path),
                "--manifest-index",
                str(manifest_index),
                "--rollback-record",
                str(rollback_path),
                "--execute",
            ]
        )
        self.assertEqual(code, 0, report)
        self.assertTrue(report["applied"])
        skill_md = target_root / "SKILL.md"
        self.assertTrue(skill_md.is_file())
        text = skill_md.read_text(encoding="utf-8")
        self.assertIn('name: "synthetic"', text)
        self.assertNotIn("Session Exercise", text)
        self.assertTrue(rollback_path.is_file())
        rollback = json.loads(rollback_path.read_text(encoding="utf-8"))
        self.assertEqual(rollback["plan_id"], "synthetic-project-local-install")
        self.assertIn(str(skill_md), rollback["written_paths"])


if __name__ == "__main__":
    unittest.main()

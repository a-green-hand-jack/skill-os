"""Cross-repo install test: skill-os scripts + a sibling pack laid out in tmp.

This test pretends skill-os and the source pack live in different repos
(which is the matrix-deployed state). The skill-os scripts run from the
skill-os REPO_ROOT but the source pack is in a sibling tmpdir. With
`--source-root <sibling>` the validator + applier should resolve all paths
across both roots.

Before ACT-082 this scenario was the documented gap; with --source-root
support added, the chain now closes end-to-end.
"""

from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PACK = REPO_ROOT / "tests" / "fixtures" / "synthetic-pack"
EXPORTER = REPO_ROOT / "scripts" / "export_skill_kernel_adapters.py"
VALIDATOR = REPO_ROOT / "scripts" / "validate_install_handoff_plan.py"
PREVIEW_INSTALL = REPO_ROOT / "scripts" / "preview_install_writer.py"
APPLY_INSTALL = REPO_ROOT / "scripts" / "apply_install_plan.py"
ACTIVE_CONTRACT = (
    REPO_ROOT / "schemas" / "skill-kernel" / "install-handoff-contract-2026-05-28.json"
)


def _existing_in(paths: list[str], roots: list[Path]) -> list[str]:
    """Return the subset of repo-relative paths that exist in at least one root."""
    return [p for p in paths if any((root / p).exists() for root in roots)]


def build_cross_repo_plan(
    target_root: Path,
    plan_path: Path,
    sibling_pack: Path,
) -> Path:
    """Build a plan whose source_of_truth_paths are the union of skill-os + sibling pack."""
    contract = json.loads(ACTIVE_CONTRACT.read_text(encoding="utf-8"))
    gates_for_mode = next(
        mode["required_review_gates"]
        for mode in contract["target_modes"]
        if mode["id"] == "project-local-profile-install"
    )
    # Authoritative source paths are split across skill-os and the sibling pack.
    all_paths = []
    for source in contract["authoritative_sources"]:
        all_paths.extend(source["paths"])
    existing = _existing_in(all_paths, [REPO_ROOT, sibling_pack])
    plan = {
        "schema_version": "0.1",
        "plan_id": "cross-repo-synthetic-install",
        "mode": "project-local-profile-install",
        "profile": "synthetic",
        "runtime": "codex",
        "target_root": str(target_root),
        "requested_manifests": [
            {"runtime": "codex", "kernel_id": "synthetic"},
        ],
        "review_gates": [{"id": g, "status": "passed"} for g in gates_for_mode],
        "source_of_truth_paths": existing,
        "validation_commands": contract["acceptance_checks"],
        "privacy_audit": {
            "status": "passed",
            "checked_paths": [str(sibling_pack)],
            "notes": "Cross-repo synthetic; sibling pack lives outside skill-os.",
        },
        "rollback": {
            "snapshot_before_write": True,
            "rollback_record_path": ".agent/install-plans/cross-repo-rollback.json",
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
            a["id"] for a in contract["forbidden_actions"]
        ],
    }
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(plan, indent=2, sort_keys=True), encoding="utf-8")
    return plan_path


def run(args: list[str], env: dict[str, str] | None = None) -> tuple[int, dict]:
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    proc = subprocess.run(args, text=True, capture_output=True, check=False, env=full_env)
    try:
        report = json.loads(proc.stdout)
    except json.JSONDecodeError:
        report = {"stdout": proc.stdout, "stderr": proc.stderr}
    return proc.returncode, report


class SyntheticCrossRepoInstallTest(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="cross-repo-install-")
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

        # Lay out a sibling pack repo by copying the synthetic-pack fixture
        # into the tmpdir. The sibling pack now lives at <tmp>/sibling-pack,
        # NOT inside skill-os.
        self.sibling_pack = self.tmp / "sibling-pack"
        shutil.copytree(FIXTURE_PACK, self.sibling_pack)
        # The synthetic kernel inside the fixture uses paths like
        # `tests/fixtures/synthetic-pack/skills/...` (skill-os-relative). For
        # cross-repo realism, rewrite them to be pack-relative.
        kernel_path = (
            self.sibling_pack / "schemas" / "skill-kernel" / "examples"
            / "synthetic.kernel.json"
        )
        kernel = json.loads(kernel_path.read_text(encoding="utf-8"))
        kernel["source_paths"] = [
            "profiles/profile-index.yaml",
            "skills/synthetic-alpha/SKILL.md",
            "skills/synthetic-beta/SKILL.md",
        ]
        kernel_path.write_text(json.dumps(kernel, indent=2, sort_keys=True), encoding="utf-8")

        # Generate the manifest index from the rewritten sibling-pack kernel.
        manifest_root = self.tmp / "manifests"
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
            raise RuntimeError(proc.stderr or proc.stdout)
        self.manifest_index = manifest_root / "installable-manifest-index.json"

    def test_validator_fails_cross_repo_without_source_root(self) -> None:
        """Sanity: without --source-root the validator still fails (pre-ACT-082 behavior)."""
        target_root = self.tmp / "would-be-target"
        plan_path = build_cross_repo_plan(
            target_root, self.tmp / "plan-no-source-root.json", self.sibling_pack
        )
        code, report = run(
            [
                "python3",
                str(VALIDATOR),
                str(plan_path),
                "--manifest-index",
                str(self.manifest_index),
            ]
        )
        # The plan lists source_of_truth_paths from BOTH roots, so without
        # --source-root the validator can only resolve the skill-os subset.
        # Paths exclusive to the sibling pack (skills/synthetic-alpha/SKILL.md
        # etc.) won't resolve → validator fails.
        self.assertNotEqual(code, 0)
        self.assertFalse(report["passed"])
        self.assertTrue(
            any(
                "kernel source path missing" in issue
                for issue in report["issues"]
            )
        )

    def test_validator_passes_cross_repo_with_source_root_flag(self) -> None:
        target_root = self.tmp / "would-be-target"
        plan_path = build_cross_repo_plan(
            target_root, self.tmp / "plan-with-source-root.json", self.sibling_pack
        )
        code, report = run(
            [
                "python3",
                str(VALIDATOR),
                str(plan_path),
                "--manifest-index",
                str(self.manifest_index),
                "--source-root",
                str(self.sibling_pack),
            ]
        )
        self.assertEqual(code, 0, report)
        self.assertTrue(report["passed"])
        self.assertTrue(report["mode_allowed_now"])

    def test_validator_passes_cross_repo_via_env_var(self) -> None:
        target_root = self.tmp / "would-be-target"
        plan_path = build_cross_repo_plan(
            target_root, self.tmp / "plan-env.json", self.sibling_pack
        )
        code, report = run(
            [
                "python3",
                str(VALIDATOR),
                str(plan_path),
                "--manifest-index",
                str(self.manifest_index),
            ],
            env={"SKILL_OS_SOURCE_ROOT": str(self.sibling_pack)},
        )
        self.assertEqual(code, 0, report)
        self.assertTrue(report["passed"])

    def test_install_preview_passes_cross_repo_with_source_root(self) -> None:
        target_root = self.tmp / "would-be-target"
        plan_path = build_cross_repo_plan(
            target_root, self.tmp / "plan-preview.json", self.sibling_pack
        )
        code, preview = run(
            [
                "python3",
                str(PREVIEW_INSTALL),
                str(plan_path),
                "--manifest-index",
                str(self.manifest_index),
                "--source-root",
                str(self.sibling_pack),
            ]
        )
        self.assertEqual(code, 0, preview)
        self.assertTrue(preview["validator_passed"])
        self.assertGreater(preview["total_files"], 0)
        self.assertFalse(target_root.exists())

    def test_apply_install_writes_cross_repo_with_source_root(self) -> None:
        target_root = self.tmp / "project" / ".agents" / "skills" / "synthetic"
        plan_path = build_cross_repo_plan(
            target_root, self.tmp / "plan-apply.json", self.sibling_pack
        )
        rollback_path = self.tmp / "rollback.json"
        code, report = run(
            [
                "python3",
                str(APPLY_INSTALL),
                str(plan_path),
                "--manifest-index",
                str(self.manifest_index),
                "--source-root",
                str(self.sibling_pack),
                "--rollback-record",
                str(rollback_path),
                "--execute",
            ]
        )
        self.assertEqual(code, 0, report)
        self.assertTrue(report["applied"])
        skill_md = target_root / "SKILL.md"
        self.assertTrue(skill_md.is_file())
        self.assertIn('name: "synthetic"', skill_md.read_text(encoding="utf-8"))
        self.assertTrue(rollback_path.is_file())


if __name__ == "__main__":
    unittest.main()

"""End-to-end test of install_profile_chain.py against synthetic fixtures.

Combines two fixture packs (`synthetic` from tests/fixtures/synthetic-pack/
and `synthetic-pdf` from tests/fixtures/synthetic-pack-pdf/) where
`synthetic-pdf` declares `depends_on: [synthetic]`. The chain installer
should resolve the chain in dependency-first order and install both packs
into the target.
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
SYNTHETIC_PACK = REPO_ROOT / "tests" / "fixtures" / "synthetic-pack"
SYNTHETIC_PACK_PDF = REPO_ROOT / "tests" / "fixtures" / "synthetic-pack-pdf"
INSTALL_CHAIN = REPO_ROOT / "scripts" / "install_profile_chain.py"


COMBINED_PROFILE_INDEX = """schema_version: 0
note: >
  Test-only combined profile-index. Lists both synthetic and synthetic-pdf
  so the chain installer can resolve synthetic-pdf → synthetic.

profiles:
  synthetic:
    status: draft
    scope: private
    future_repo: synthetic-pack
    intent: >
      Synthetic base profile.
    entrypoints:
      - synthetic-alpha
    routers:
      - synthetic-alpha
    skills:
      required:
        - synthetic-alpha
        - synthetic-beta
      optional:
        - synthetic-gamma
    install_policy:
      recommended: project-local
      full_bundle_allowed: false
  synthetic-pdf:
    status: draft
    scope: private
    future_repo: synthetic-pack-pdf
    depends_on:
      - synthetic
    intent: >
      Synthetic profile depending on synthetic.
    entrypoints:
      - synthetic-pdf-reader
    routers:
      - synthetic-pdf-reader
    skills:
      required:
        - synthetic-pdf-reader
      optional: []
    install_policy:
      recommended: project-local
      full_bundle_allowed: false
"""


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


class ChainInstallTest(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="chain-install-")
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

        # Lay out two sibling pack repos under a single parent dir.
        self.pack_parent = self.tmp / "packs"
        self.pack_parent.mkdir(parents=True, exist_ok=True)

        # Pack A: synthetic (the base, no dependencies)
        synthetic_dest = self.pack_parent / "synthetic-pack"
        shutil.copytree(SYNTHETIC_PACK, synthetic_dest)
        # Rewrite kernel source_paths to be pack-relative (the fixture's kernel
        # uses skill-os-relative paths because it originally lived inside skill-os).
        kernel_path = (
            synthetic_dest / "schemas" / "skill-kernel" / "examples"
            / "synthetic.kernel.json"
        )
        kernel = json.loads(kernel_path.read_text(encoding="utf-8"))
        kernel["source_paths"] = [
            "profiles/profile-index.yaml",
            "skills/synthetic-alpha/SKILL.md",
            "skills/synthetic-beta/SKILL.md",
        ]
        kernel_path.write_text(json.dumps(kernel, indent=2, sort_keys=True), encoding="utf-8")

        # Pack B: synthetic-pdf (depends on synthetic)
        synthetic_pdf_dest = self.pack_parent / "synthetic-pack-pdf"
        shutil.copytree(SYNTHETIC_PACK_PDF, synthetic_pdf_dest)

        # Write a combined profile-index in tmp that the chain installer reads.
        self.combined_profile_index = self.tmp / "combined-profile-index.yaml"
        self.combined_profile_index.write_text(COMBINED_PROFILE_INDEX, encoding="utf-8")

        # Target install dir
        self.target_parent = self.tmp / "test-project" / ".agents" / "skills"

    def test_chain_install_synthetic_pdf_installs_both_profiles(self) -> None:
        code, report = run(
            [
                "python3",
                str(INSTALL_CHAIN),
                "synthetic-pdf",
                "--target-parent",
                str(self.target_parent),
                "--pack-search-path",
                str(self.pack_parent),
                "--profile-index",
                str(self.combined_profile_index),
                "--execute",
            ]
        )
        self.assertEqual(code, 0, report)
        self.assertTrue(report["chain_resolved"])
        self.assertEqual(report["resolution_order"], ["synthetic", "synthetic-pdf"])
        self.assertEqual(len(report["steps"]), 2)
        for step in report["steps"]:
            self.assertTrue(step["applied"], step)

        # synthetic landed under target/synthetic/
        self.assertTrue((self.target_parent / "synthetic" / "SKILL.md").is_file())
        # synthetic-pdf landed under target/synthetic-pdf/
        self.assertTrue((self.target_parent / "synthetic-pdf" / "SKILL.md").is_file())

        # Each step should have its own rollback record
        work_dir = self.target_parent / ".skill-os-install-state"
        self.assertTrue(work_dir.is_dir())
        self.assertTrue((work_dir / "rollback-synthetic.json").is_file())
        self.assertTrue((work_dir / "rollback-synthetic-pdf.json").is_file())

        # Leaf-skill staging: every leaf SKILL.md from each pack should also land
        # flat under target_parent/<skill-name>/.
        self.assertTrue((self.target_parent / "synthetic-alpha" / "SKILL.md").is_file())
        self.assertTrue((self.target_parent / "synthetic-beta" / "SKILL.md").is_file())
        self.assertTrue((self.target_parent / "synthetic-gamma" / "SKILL.md").is_file())
        self.assertTrue((self.target_parent / "synthetic-pdf-reader" / "SKILL.md").is_file())

        # Aggregated reporting
        self.assertEqual(
            sorted(report["leaf_skills_staged_unique"]),
            ["synthetic-alpha", "synthetic-beta", "synthetic-gamma", "synthetic-pdf-reader"],
        )
        self.assertEqual(report["leaf_skills_unique_count"], 4)

        # Per-step staging counts
        synth_step = next(s for s in report["steps"] if s["profile"] == "synthetic")
        pdf_step = next(s for s in report["steps"] if s["profile"] == "synthetic-pdf")
        self.assertEqual(len(synth_step["leaf_skills"]["staged"]), 3)
        self.assertEqual(len(synth_step["leaf_skills"]["skipped_dedup"]), 0)
        self.assertEqual(len(pdf_step["leaf_skills"]["staged"]), 1)
        self.assertEqual(len(pdf_step["leaf_skills"]["skipped_dedup"]), 0)

    def test_chain_install_no_leaf_skills_skips_staging(self) -> None:
        code, report = run(
            [
                "python3",
                str(INSTALL_CHAIN),
                "synthetic-pdf",
                "--target-parent",
                str(self.target_parent),
                "--pack-search-path",
                str(self.pack_parent),
                "--profile-index",
                str(self.combined_profile_index),
                "--execute",
                "--no-leaf-skills",
            ]
        )
        self.assertEqual(code, 0, report)
        # Profile adapters land as usual
        self.assertTrue((self.target_parent / "synthetic" / "SKILL.md").is_file())
        # But no leaf-skill flat dirs
        self.assertFalse((self.target_parent / "synthetic-alpha").exists())
        self.assertFalse((self.target_parent / "synthetic-pdf-reader").exists())
        self.assertEqual(report["leaf_skills_unique_count"], 0)
        for step in report["steps"]:
            self.assertTrue(step["leaf_skills"].get("skipped_via_flag"))

    def test_leaf_staging_dedup_first_pack_wins(self) -> None:
        """When two packs ship a same-named skill, the first (foundational) wins."""
        # Add a synthetic-alpha to synthetic-pdf with distinctive content; on
        # install, foundational synthetic's version should remain (first wins).
        clash_dir = self.pack_parent / "synthetic-pack-pdf" / "skills" / "synthetic-alpha"
        clash_dir.mkdir(parents=True, exist_ok=True)
        (clash_dir / "SKILL.md").write_text(
            "---\nname: synthetic-alpha\n"
            "description: This is the WRONG version from synthetic-pdf — first-wins dedup should keep synthetic's copy.\n"
            "---\n",
            encoding="utf-8",
        )

        code, report = run(
            [
                "python3",
                str(INSTALL_CHAIN),
                "synthetic-pdf",
                "--target-parent",
                str(self.target_parent),
                "--pack-search-path",
                str(self.pack_parent),
                "--profile-index",
                str(self.combined_profile_index),
                "--execute",
            ]
        )
        self.assertEqual(code, 0, report)
        # The synthetic-alpha that ends up on disk must be synthetic's (foundational),
        # not synthetic-pdf's clashing copy.
        landed = (self.target_parent / "synthetic-alpha" / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("WRONG version", landed)
        self.assertIn("Synthetic test fixture skill alpha", landed)
        # The clash must be recorded in synthetic-pdf step's skipped_dedup
        pdf_step = next(s for s in report["steps"] if s["profile"] == "synthetic-pdf")
        skipped = pdf_step["leaf_skills"]["skipped_dedup"]
        self.assertTrue(
            any(s["name"] == "synthetic-alpha" for s in skipped),
            f"expected synthetic-alpha in skipped_dedup, got {skipped}",
        )

    def test_chain_install_dry_run_writes_no_files_under_target(self) -> None:
        code, report = run(
            [
                "python3",
                str(INSTALL_CHAIN),
                "synthetic-pdf",
                "--target-parent",
                str(self.target_parent),
                "--pack-search-path",
                str(self.pack_parent),
                "--profile-index",
                str(self.combined_profile_index),
                # NB: no --execute
            ]
        )
        self.assertEqual(code, 0, report)
        self.assertTrue(report["chain_resolved"])
        # apply_install_plan refuses without --execute → steps say applied: False,
        # but the chain script keeps going through both steps in dry-run mode.
        self.assertEqual(len(report["steps"]), 2)
        for step in report["steps"]:
            self.assertFalse(step["applied"])
        # No target files written
        self.assertFalse((self.target_parent / "synthetic" / "SKILL.md").exists())
        self.assertFalse((self.target_parent / "synthetic-pdf" / "SKILL.md").exists())
        # And no leaf-skill flat dirs either
        self.assertFalse((self.target_parent / "synthetic-alpha").exists())
        self.assertFalse((self.target_parent / "synthetic-pdf-reader").exists())

    def test_chain_install_fails_when_pack_root_missing(self) -> None:
        # Point search path at an empty dir → pack discovery fails
        empty_search = self.tmp / "empty-search-dir"
        empty_search.mkdir()
        code, report = run(
            [
                "python3",
                str(INSTALL_CHAIN),
                "synthetic-pdf",
                "--target-parent",
                str(self.target_parent),
                "--pack-search-path",
                str(empty_search),
                "--profile-index",
                str(self.combined_profile_index),
                "--execute",
            ]
        )
        self.assertNotEqual(code, 0)
        self.assertTrue(report["chain_resolved"])
        # First step (synthetic) fails to locate the pack
        first_step = report["steps"][0]
        self.assertFalse(first_step["applied"])
        self.assertIn("could not locate pack repo", first_step["error"])

    def test_chain_install_fails_for_unknown_top_profile(self) -> None:
        code, report = run(
            [
                "python3",
                str(INSTALL_CHAIN),
                "definitely-not-a-profile",
                "--target-parent",
                str(self.target_parent),
                "--pack-search-path",
                str(self.pack_parent),
                "--profile-index",
                str(self.combined_profile_index),
                "--execute",
            ]
        )
        self.assertNotEqual(code, 0)
        self.assertFalse(report.get("chain_resolved", True))


if __name__ == "__main__":
    unittest.main()

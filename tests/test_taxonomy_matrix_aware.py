from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "validate_skill_taxonomy.py"
SYNTHETIC = REPO_ROOT / "tests" / "fixtures" / "synthetic-pack"


class TaxonomyMatrixAwareTest(unittest.TestCase):
    """Smoke tests for matrix-aware validate_skill_taxonomy.

    These don't try to fully validate the matrix (that needs sibling packs
    cloned alongside, which CI doesn't have). They verify the new flags
    parse and the empty-universe warning fires.
    """

    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["uv", "run", str(SCRIPT), *args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_help_lists_new_flags(self) -> None:
        proc = self.run_script("--help")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("--pack-search-path", proc.stdout)
        self.assertIn("--pack NAME=PATH", proc.stdout)

    def test_unknown_arg_rejected(self) -> None:
        proc = self.run_script("--no-such-flag")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("unknown arg", proc.stderr + proc.stdout)

    def test_pack_search_path_with_empty_dir_warns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            # Empty search path — no packs found there.
            proc = self.run_script("--pack-search-path", tmp)
            # The validator still runs against the local empty skills/ root;
            # we expect either a warning or failure due to no skills, never a
            # silent OK with 0 skills.
            self.assertNotEqual(
                proc.returncode,
                0,
                "expected non-zero exit when no skills are reachable",
            )

    def test_pack_override_directory_name_friction(self) -> None:
        """--pack NAME=PATH must work for non-canonical directory names."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            # Create a pseudo-pack at a non-canonical name with one fake skill.
            fake_pack = tmp_path / "weird-name"
            (fake_pack / "skills" / "demo-skill").mkdir(parents=True)
            (fake_pack / "skills" / "demo-skill" / "SKILL.md").write_text(
                "---\nname: demo-skill\ndescription: demo\n---\n"
            )
            proc = self.run_script(
                "--pack",
                f"my-pack={fake_pack}",
            )
            # Run completes (may exit non-zero due to kernel checks against
            # an incomplete fake matrix), but the "skill universe is empty"
            # warning must not fire — demo-skill should be visible.
            self.assertNotIn("skill universe is empty", proc.stderr)


if __name__ == "__main__":
    unittest.main()

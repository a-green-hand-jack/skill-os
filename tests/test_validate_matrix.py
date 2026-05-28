from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "validate_matrix.py"

sys.path.insert(0, str(SCRIPT.parent))
import validate_matrix  # type: ignore  # noqa: E402


class ValidateMatrixTest(unittest.TestCase):
    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(SCRIPT), *args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_help_lists_pack_flags(self) -> None:
        proc = self.run_script("--help")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("--pack-search-path", proc.stdout)
        self.assertIn("--pack NAME=PATH", proc.stdout)

    def test_profile_name_pack_override_normalizes_to_repo_name(self) -> None:
        profiles = {"ml-research": {"future_repo": "ml-research-skills"}}
        overrides = validate_matrix.parse_pack_overrides(
            ["ml-research=/tmp/ml-pack"],
            profiles,
            {"ml-research-skills"},
        )
        self.assertEqual(len(overrides), 1)
        self.assertEqual(overrides[0].requested_name, "ml-research")
        self.assertEqual(overrides[0].repo_name, "ml-research-skills")

    def test_all_checks_can_be_skipped_for_wrapper_smoke(self) -> None:
        proc = self.run_script(
            "--skip-tests",
            "--skip-adapters",
            "--skip-taxonomy",
            "--skip-pins",
            "--json",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        report = json.loads(proc.stdout)
        self.assertTrue(report["passed"])
        self.assertEqual(report["summary"]["skipped"], 4)
        self.assertTrue(all(step["status"] == "skipped" for step in report["steps"]))

    def test_missing_pack_paths_fail_pin_check(self) -> None:
        with tempfile.TemporaryDirectory(prefix="matrix-pins-") as tmp:
            proc = self.run_script(
                "--skip-tests",
                "--skip-adapters",
                "--skip-taxonomy",
                "--pack-search-path",
                tmp,
                "--json",
            )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        report = json.loads(proc.stdout)
        self.assertFalse(report["passed"])
        self.assertEqual(report["summary"]["failed"], 1)
        pin_step = next(step for step in report["steps"] if step["name"] == "pack-pins")
        self.assertEqual(pin_step["status"], "failed")
        self.assertTrue(all(row["status"] == "missing" for row in report["pack_paths"]))


if __name__ == "__main__":
    unittest.main()

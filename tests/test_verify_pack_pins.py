from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "verify_pack_pins.py"
PROFILE_INDEX = REPO_ROOT / "profiles" / "profile-index.yaml"


def init_git_repo_at(path: Path, commit_message: str = "init") -> str:
    """Initialize an empty git repo with one commit; return the commit SHA."""
    path.mkdir(parents=True, exist_ok=True)
    env_setup = [
        ["git", "-C", str(path), "init", "-q", "-b", "main"],
        ["git", "-C", str(path), "config", "user.email", "test@example.com"],
        ["git", "-C", str(path), "config", "user.name", "test"],
        ["git", "-C", str(path), "commit", "--allow-empty", "-q", "-m", commit_message],
    ]
    for cmd in env_setup:
        subprocess.run(cmd, check=True, capture_output=True)
    sha = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return sha


class VerifyPackPinsTest(unittest.TestCase):
    """Behavioural test for scripts/verify_pack_pins.py."""

    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(SCRIPT), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_parses_pinned_packs_from_profile_index(self) -> None:
        """All six pack entries must have valid 40-char hex pinned_commit."""
        import sys

        sys.path.insert(0, str(SCRIPT.parent))
        import verify_pack_pins  # type: ignore

        pinned = verify_pack_pins.parse_pinned_packs(PROFILE_INDEX.read_text())
        self.assertEqual(
            set(pinned.keys()),
            {
                "core-ops-skills",
                "automation-skills",
                "paper-reading-skills",
                "research-distillation-skills",
                "quick-experiment-skills",
                "ml-research-skills",
            },
        )
        for name, meta in pinned.items():
            self.assertRegex(
                meta["pinned_commit"],
                r"^[0-9a-f]{40}$",
                f"{name} pinned_commit is not a 40-char SHA",
            )

    def test_missing_pack_directory_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            # Empty parent: no pack dirs exist.
            proc = self.run_script("--pack-search-path", tmp, "--json")
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            data = json.loads(proc.stdout)
            statuses = {r["pack"]: r["status"] for r in data["results"]}
            self.assertTrue(all(s == "missing" for s in statuses.values()), statuses)

    def test_pack_with_wrong_commit_is_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            # Create a real git repo for one pack with a SHA that won't match
            # the pinned commit (random commit message → unique SHA).
            pack_name = "core-ops-skills"
            sha = init_git_repo_at(parent / pack_name, "verify-test")

            proc = self.run_script("--pack-search-path", tmp, "--json")
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            data = json.loads(proc.stdout)
            core_entry = next(r for r in data["results"] if r["pack"] == pack_name)
            self.assertEqual(core_entry["status"], "mismatch")
            self.assertEqual(core_entry["actual_commit"], sha)
            self.assertNotEqual(core_entry["actual_commit"], core_entry["pinned_commit"])

    def test_no_pack_path_yields_skipped(self) -> None:
        proc = self.run_script("--json")
        # When no search path AND no overrides, every pack is skipped → exit 0.
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        data = json.loads(proc.stdout)
        self.assertTrue(
            all(r["status"] == "skipped" for r in data["results"]),
            [(r["pack"], r["status"]) for r in data["results"]],
        )


if __name__ == "__main__":
    unittest.main()

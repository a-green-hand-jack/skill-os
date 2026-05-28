from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "score_profile_routing.py"


class ProfileRoutingHarnessTest(unittest.TestCase):
    maxDiff = None

    def run_script(self, *args: str | Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(SCRIPT), *(str(arg) for arg in args)],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_gold_predictions_score_cleanly(self) -> None:
        with tempfile.TemporaryDirectory(prefix="profile-routing-") as tmp:
            gold = Path(tmp) / "gold.json"

            write_proc = self.run_script("--write-gold", gold)
            self.assertEqual(write_proc.returncode, 0, write_proc.stderr or write_proc.stdout)
            self.assertTrue(gold.is_file())

            score_proc = self.run_script("--predictions", gold)
            self.assertEqual(score_proc.returncode, 0, score_proc.stderr or score_proc.stdout)
            self.assertIn("Exact accuracy: 8/8 (100.0%)", score_proc.stdout)
            self.assertIn("PASS", score_proc.stdout)

    def test_blank_template_is_scored_as_failures(self) -> None:
        with tempfile.TemporaryDirectory(prefix="profile-routing-") as tmp:
            template = Path(tmp) / "template.json"

            write_proc = self.run_script("--write-template", template)
            self.assertEqual(write_proc.returncode, 0, write_proc.stderr or write_proc.stdout)

            score_proc = self.run_script("--predictions", template)
            self.assertEqual(score_proc.returncode, 1)
            self.assertIn("Exact accuracy: 0/8 (0.0%)", score_proc.stdout)
            self.assertIn("FAIL", score_proc.stdout)

    def test_mapping_predictions_support_partial_scoring(self) -> None:
        with tempfile.TemporaryDirectory(prefix="profile-routing-") as tmp:
            predictions = Path(tmp) / "partial.json"
            predictions.write_text(
                json.dumps(
                    {
                        "PRE-001": {
                            "profile": "global-bootstrap",
                            "entrypoint": "ml-research-bootstrap",
                        }
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            score_proc = self.run_script("--predictions", predictions, "--allow-missing")
            self.assertEqual(score_proc.returncode, 0, score_proc.stderr or score_proc.stdout)
            self.assertIn("Scored predictions: 1", score_proc.stdout)
            self.assertIn("Missing predictions: 7", score_proc.stdout)
            self.assertIn("Exact accuracy: 1/1 (100.0%)", score_proc.stdout)

    def test_should_not_profile_violation_is_reported(self) -> None:
        with tempfile.TemporaryDirectory(prefix="profile-routing-") as tmp:
            predictions = Path(tmp) / "wrong.json"
            predictions.write_text(
                json.dumps(
                    {
                        "predictions": [
                            {
                                "id": "PRE-001",
                                "profile": "ml-research",
                                "entrypoint": "ml-research-router",
                            }
                        ]
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            score_proc = self.run_script("--predictions", predictions, "--allow-missing")
            self.assertEqual(score_proc.returncode, 1)
            self.assertIn("PRE-001", score_proc.stdout)
            self.assertIn("profile `ml-research` is listed in should_not_profiles", score_proc.stdout)


if __name__ == "__main__":
    unittest.main()

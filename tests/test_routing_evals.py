from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
EVALS_PATH = REPO_ROOT / "tests" / "routing-evals.json"


class RoutingEvalsTest(unittest.TestCase):
    """Structural regression for the matrix-wide leaf-routing eval fixture.

    These evals describe the expected router → leaf path for prompts that
    span multiple sibling pack repos (e.g. experiment-evidence-router lives
    in quick-experiment-skills, experiment-debugger lives there too, while
    ml-research-router and paper-* skills live in ml-research-skills).

    skill-os owns this fixture because it is the only repo that sees the
    full matrix. The test enforces structural well-formedness; deeper
    cross-pack skill-existence checks are an opt-in script (not run here)
    because they would require every sibling pack to be checked out
    alongside skill-os.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads(EVALS_PATH.read_text())
        cls.evals = cls.payload["evals"]

    def test_each_eval_has_required_fields(self) -> None:
        required = {
            "id",
            "prompt",
            "expected_path",
            "should_trigger",
            "should_not_trigger",
            "rationale",
        }
        for entry in self.evals:
            missing = required - set(entry)
            self.assertFalse(
                missing,
                f"eval {entry.get('id', '?')} missing fields: {sorted(missing)}",
            )

    def test_ids_are_unique(self) -> None:
        ids = [entry["id"] for entry in self.evals]
        self.assertEqual(
            len(ids), len(set(ids)), f"duplicate IDs in routing-evals.json: {ids}"
        )

    def test_expected_path_ends_with_should_trigger(self) -> None:
        for entry in self.evals:
            path = entry["expected_path"]
            self.assertGreater(
                len(path), 0, f"{entry['id']}: expected_path must be non-empty"
            )
            self.assertEqual(
                path[-1],
                entry["should_trigger"],
                f"{entry['id']}: expected_path[-1] must equal should_trigger",
            )

    def test_should_not_trigger_excludes_should_trigger(self) -> None:
        for entry in self.evals:
            self.assertNotIn(
                entry["should_trigger"],
                entry["should_not_trigger"],
                f"{entry['id']}: should_trigger cannot also be in should_not_trigger",
            )

    def test_prompts_are_non_empty(self) -> None:
        for entry in self.evals:
            self.assertTrue(
                entry["prompt"].strip(),
                f"{entry['id']}: prompt must be non-empty",
            )

    def test_path_entries_are_kebab_case_names(self) -> None:
        import re

        skill_name = re.compile(r"^[a-z][a-z0-9-]*$")
        for entry in self.evals:
            for name in entry["expected_path"]:
                self.assertRegex(
                    name,
                    skill_name,
                    f"{entry['id']}: expected_path entry {name!r} must be kebab-case",
                )
            self.assertRegex(
                entry["should_trigger"],
                skill_name,
                f"{entry['id']}: should_trigger {entry['should_trigger']!r} must be kebab-case",
            )

    def test_payload_has_documentation_comments(self) -> None:
        self.assertIn("_comment", self.payload)
        self.assertIn("_format", self.payload)


if __name__ == "__main__":
    unittest.main()

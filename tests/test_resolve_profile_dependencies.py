from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "resolve_profile_dependencies.py"


def run(args: list[str]) -> tuple[int, dict]:
    proc = subprocess.run(
        ["python3", str(SCRIPT), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    return proc.returncode, json.loads(proc.stdout)


class ResolveProfileDependenciesTest(unittest.TestCase):
    maxDiff = None

    def test_quick_experiment_resolves_to_core_ops_automation_quick_experiment(self) -> None:
        code, report = run(["quick-experiment"])
        self.assertEqual(code, 0)
        self.assertTrue(report["passed"])
        self.assertEqual(report["issues"], [])
        order = [entry["profile"] for entry in report["resolution_order"]]
        self.assertEqual(order, ["core-ops", "automation", "quick-experiment"])

    def test_paper_reading_resolves_to_core_ops_first(self) -> None:
        code, report = run(["paper-reading"])
        self.assertEqual(code, 0)
        self.assertTrue(report["passed"])
        order = [entry["profile"] for entry in report["resolution_order"]]
        self.assertEqual(order, ["core-ops", "paper-reading"])

    def test_core_ops_alone_has_no_dependencies(self) -> None:
        code, report = run(["core-ops"])
        self.assertEqual(code, 0)
        self.assertTrue(report["passed"])
        order = [entry["profile"] for entry in report["resolution_order"]]
        self.assertEqual(order, ["core-ops"])

    def test_resolution_entries_include_router_metadata(self) -> None:
        code, report = run(["quick-experiment"])
        self.assertEqual(code, 0)
        quick = next(
            entry for entry in report["resolution_order"]
            if entry["profile"] == "quick-experiment"
        )
        self.assertEqual(quick["entrypoints"], ["experiment-evidence-router"])
        self.assertEqual(quick["routers"], ["experiment-evidence-router"])

    def test_multiple_requests_deduplicate_dependencies(self) -> None:
        code, report = run(["paper-reading", "quick-experiment"])
        self.assertEqual(code, 0)
        order = [entry["profile"] for entry in report["resolution_order"]]
        # core-ops should appear once and before both paper-reading and
        # quick-experiment.
        self.assertEqual(order.count("core-ops"), 1)
        self.assertEqual(order.count("automation"), 1)
        self.assertLess(order.index("core-ops"), order.index("paper-reading"))
        self.assertLess(order.index("core-ops"), order.index("automation"))
        self.assertLess(order.index("automation"), order.index("quick-experiment"))

    def test_unknown_profile_is_reported(self) -> None:
        code, report = run(["definitely-not-a-profile"])
        self.assertEqual(code, 1)
        self.assertFalse(report["passed"])
        self.assertTrue(
            any("unknown profile" in issue for issue in report["issues"])
        )

    def test_circular_dependency_is_detected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cycle-resolver-") as tmp_str:
            tmp = Path(tmp_str)
            cycle_yaml = tmp / "profile-index.yaml"
            cycle_yaml.write_text(
                "schema_version: 0\n"
                "profiles:\n"
                "  a:\n"
                "    status: draft\n"
                "    future_repo: a-skills\n"
                "    depends_on:\n"
                "      - b\n"
                "  b:\n"
                "    status: draft\n"
                "    future_repo: b-skills\n"
                "    depends_on:\n"
                "      - a\n",
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "a",
                    "--profile-index",
                    str(cycle_yaml),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 1)
            report = json.loads(proc.stdout)
            self.assertFalse(report["passed"])
            self.assertTrue(
                any("circular" in issue.lower() for issue in report["issues"])
            )

    def test_missing_dependency_target_is_reported(self) -> None:
        with tempfile.TemporaryDirectory(prefix="missing-dep-") as tmp_str:
            tmp = Path(tmp_str)
            yaml = tmp / "profile-index.yaml"
            yaml.write_text(
                "schema_version: 0\n"
                "profiles:\n"
                "  alpha:\n"
                "    status: draft\n"
                "    future_repo: alpha-skills\n"
                "    depends_on:\n"
                "      - omega\n",
                encoding="utf-8",
            )
            proc = subprocess.run(
                ["python3", str(SCRIPT), "alpha", "--profile-index", str(yaml)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 1)
            report = json.loads(proc.stdout)
            self.assertFalse(report["passed"])
            self.assertTrue(
                any("omega" in issue for issue in report["issues"])
            )


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "export_skill_kernel_adapters.py"
CONTRACTS = REPO_ROOT / "schemas" / "skill-kernel" / "runtime-adapter-contracts.json"
TRIGGER_CAPTURE = (
    REPO_ROOT
    / "schemas"
    / "skill-kernel"
    / "runtime-trigger-capture-2026-05-27.json"
)
CORE_OPS_SEMANTICS_CAPTURE = (
    REPO_ROOT
    / "schemas"
    / "skill-kernel"
    / "core-ops-runtime-semantics-2026-05-27.json"
)
MANIFEST_EXERCISE_CAPTURE = (
    REPO_ROOT
    / "schemas"
    / "skill-kernel"
    / "manifest-exercise-runtime-capture-2026-05-27.json"
)


class SkillKernelAdapterExportTest(unittest.TestCase):
    maxDiff = None

    def run_script(self, *args: str | Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(SCRIPT), *(str(arg) for arg in args)],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_stdout_export_preserves_codex_contracts(self) -> None:
        proc = self.run_script("--runtime", "codex")
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)

        bundle = json.loads(proc.stdout)
        self.assertEqual(bundle["bundle_schema_version"], "0.1-dry-run")
        self.assertTrue(bundle["dry_run"])
        self.assertEqual(bundle["source_of_truth"], "kernel")
        self.assertEqual(bundle["adapter_count"], 5)

        adapters = {
            adapter["kernel"]["kernel_id"]: adapter
            for adapter in bundle["adapters"]
        }
        self.assertEqual(
            set(adapters),
            {
                "core-ops",
                "paper-reading",
                "research-distillation-workflow-contract",
                "automation",
                "quick-experiment",
            },
        )

        for kernel_id, adapter in adapters.items():
            with self.subTest(kernel_id=kernel_id):
                self.assertEqual(adapter["runtime"], "codex")
                self.assertTrue(adapter["dry_run"])
                self.assertFalse(adapter["installable"])
                self.assertEqual(adapter["source_of_truth"], "kernel")
                self.assertEqual(
                    adapter["runtime_contract"]["contract_id"],
                    "codex-skill-directory-v0",
                )
                self.assertEqual(
                    adapter["runtime_projection"]["skill_markdown"]["path"],
                    "SKILL.md",
                )
                self.assertEqual(
                    adapter["runtime_projection"]["skill_markdown"]["frontmatter"][
                        "name"
                    ],
                    adapter["kernel"]["kernel_id"],
                )
                self.assertLessEqual(
                    len(
                        adapter["runtime_projection"]["skill_markdown"][
                            "frontmatter"
                        ]["description"]
                    ),
                    500,
                )
                self.assertFalse(
                    adapter["runtime_projection"]["compatibility"]["installable_now"]
                )
                self.assertIn(
                    "workflow",
                    adapter["runtime_projection"]["field_mapping"]["docs_only"],
                )
                semantics = adapter["selection_semantics"]
                self.assertEqual(
                    adapter["runtime_projection"]["routing_hints"][
                        "selection_semantics"
                    ],
                    semantics,
                )
                self.assertIn(
                    semantics["runtime_expectation"],
                    {"direct-entrypoint", "profile-first-entrypoint"},
                )
                self.assertEqual(
                    set(adapter["workflow"]["supported_lanes"]),
                    {"action", "evidence", "combined", "no-contract"},
                )
                self.assertIn(
                    "uv run scripts/validate_skill_taxonomy.py",
                    adapter["validation"]["commands"],
                )
                self.assertIn("project-memory", adapter["memory"]["writeback_targets"])
                self.assertTrue(adapter["kernel"]["source_paths"])

    def test_check_all_generates_every_declared_runtime(self) -> None:
        proc = self.run_script("--runtime", "all", "--check")
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        self.assertIn("PASS: generated 16 dry-run adapter(s) from 5 kernel(s)", proc.stdout)

    def test_output_dir_writes_one_file_per_selected_runtime(self) -> None:
        with tempfile.TemporaryDirectory(prefix="kernel-adapters-") as tmp:
            proc = self.run_script("--runtime", "generic-agent", "--output-dir", tmp)
            self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)

            summary = json.loads(proc.stdout)
            self.assertEqual(summary["adapter_count"], 5)
            written = sorted(Path(tmp).glob("*.generic-agent.adapter.json"))
            self.assertEqual(len(written), 5)

            adapter = json.loads(written[0].read_text(encoding="utf-8"))
            self.assertEqual(adapter["runtime"], "generic-agent")
            self.assertEqual(adapter["adapter_schema_version"], "0.1-dry-run")
            self.assertFalse(adapter["installable"])
            self.assertEqual(adapter["source_of_truth"], "kernel")
            self.assertEqual(adapter["runtime_notes"][0], "dry-run adapter only; do not install directly")
            self.assertEqual(
                adapter["runtime_projection"]["contract_id"],
                "generic-agent-skill-directory-v0",
            )

    def test_preview_skill_root_writes_runtime_like_skill_dirs(self) -> None:
        with tempfile.TemporaryDirectory(prefix="kernel-preview-skills-") as tmp:
            proc = self.run_script("--runtime", "codex", "--preview-skill-root", tmp)
            self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)

            summary = json.loads(proc.stdout)
            self.assertEqual(summary["adapter_count"], 5)
            self.assertEqual(summary["fixture_count"], 5)
            self.assertEqual(summary["smoke_check"], "passed")

            skill_file = Path(tmp) / "codex" / "core-ops" / "SKILL.md"
            interface_file = (
                Path(tmp) / "codex" / "core-ops" / "agents" / "openai.yaml"
            )
            manifest_file = Path(tmp) / "preview-manifest.json"
            self.assertTrue(skill_file.is_file())
            self.assertTrue(interface_file.is_file())
            self.assertTrue(manifest_file.is_file())

            text = skill_file.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"))
            self.assertIn('name: "core-ops"', text)
            self.assertIn('description: "Provide the shared operational substrate', text)
            self.assertIn("preview-only runtime fixture", text)
            self.assertIn("Source of truth: `kernel`", text)
            self.assertIn("Installable now: `false`", text)
            self.assertIn("Selection semantics", text)
            self.assertIn("profile-first-entrypoint", text)

            manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
            self.assertTrue(manifest["dry_run"])
            self.assertEqual(manifest["source_of_truth"], "kernel")
            self.assertEqual(manifest["fixture_count"], 5)

    def test_preview_skill_root_all_runtimes_avoids_name_collisions(self) -> None:
        with tempfile.TemporaryDirectory(prefix="kernel-preview-skills-") as tmp:
            proc = self.run_script("--runtime", "all", "--preview-skill-root", tmp)
            self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)

            summary = json.loads(proc.stdout)
            self.assertEqual(summary["adapter_count"], 16)
            self.assertEqual(summary["fixture_count"], 16)
            self.assertEqual(summary["smoke_check"], "passed")

            self.assertTrue((Path(tmp) / "codex" / "core-ops" / "SKILL.md").is_file())
            self.assertTrue((Path(tmp) / "claude-code" / "core-ops" / "SKILL.md").is_file())
            self.assertTrue((Path(tmp) / "cursor" / "core-ops" / "SKILL.md").is_file())
            self.assertFalse((Path(tmp) / "cursor" / "paper-reading").exists())
            self.assertFalse(
                (
                    Path(tmp)
                    / "claude-code"
                    / "core-ops"
                    / "agents"
                    / "openai.yaml"
                ).exists()
            )

    def test_installable_manifest_root_writes_review_gated_manifests(self) -> None:
        with tempfile.TemporaryDirectory(prefix="kernel-installable-manifests-") as tmp:
            proc = self.run_script(
                "--runtime",
                "all",
                "--installable-manifest-root",
                tmp,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)

            summary = json.loads(proc.stdout)
            self.assertEqual(summary["adapter_count"], 16)
            self.assertEqual(summary["manifest_count"], 16)
            self.assertEqual(summary["smoke_check"], "passed")
            self.assertTrue(summary["prototype"])
            self.assertTrue(summary["manual_review_required"])
            self.assertFalse(summary["safe_to_install_automatically"])

            index_file = Path(tmp) / "installable-manifest-index.json"
            core_manifest_file = Path(tmp) / "codex" / "core-ops" / "adapter-manifest.json"
            self.assertTrue(index_file.is_file())
            self.assertTrue(core_manifest_file.is_file())

            index = json.loads(index_file.read_text(encoding="utf-8"))
            self.assertEqual(index["manifest_count"], 16)
            self.assertEqual(index["source_of_truth"], "kernel")
            self.assertTrue(index["prototype"])
            self.assertFalse(index["safe_to_install_automatically"])

            manifest = json.loads(core_manifest_file.read_text(encoding="utf-8"))
            self.assertEqual(manifest["manifest_schema_version"], "0.1-prototype")
            self.assertTrue(manifest["prototype"])
            self.assertTrue(manifest["manual_review_required"])
            self.assertFalse(manifest["safe_to_install_automatically"])
            self.assertEqual(manifest["source_of_truth"], "kernel")
            self.assertEqual(manifest["runtime"], "codex")
            self.assertEqual(manifest["kernel"]["kernel_id"], "core-ops")
            self.assertEqual(
                manifest["runtime_contract"]["contract_id"],
                "codex-skill-directory-v0",
            )
            self.assertEqual(
                manifest["install_target"]["skill_directory"],
                "core-ops",
            )
            self.assertIn("SKILL.md", manifest["install_target"]["required_files"])
            self.assertEqual(
                manifest["skill_markdown"]["frontmatter"]["name"],
                "core-ops",
            )
            self.assertEqual(
                manifest["selection_semantics"]["runtime_expectation"],
                "profile-first-entrypoint",
            )
            self.assertIn(
                "mature owner skills",
                manifest["selection_semantics"]["delegation_policy"],
            )
            self.assertIn(
                "workflow",
                manifest["non_authoritative_kernel_fields"],
            )
            self.assertIn(
                "validation gate definitions",
                manifest["forbidden_authoritative_fields"],
            )
            self.assertFalse(
                {
                    "workflow",
                    "memory",
                    "validation",
                    "promotion",
                    "install_policy",
                }.intersection(manifest)
            )
            self.assertTrue(
                all(
                    not source_path.startswith("/")
                    for source_path in manifest["kernel_source_paths"]
                )
            )
            self.assertEqual(
                {
                    gate["id"]
                    for gate in manifest["review_gates"]
                },
                {
                    "kernel-source-of-truth",
                    "selection-semantics-preserved",
                    "docs-only-fields-not-authoritative",
                    "manual-review-required",
                },
            )

    def test_installable_manifest_exercise_writes_session_only_skill_root(self) -> None:
        with tempfile.TemporaryDirectory(prefix="kernel-installable-manifests-") as manifests_tmp:
            with tempfile.TemporaryDirectory(prefix="kernel-manifest-exercise-") as exercise_tmp:
                proc = self.run_script(
                    "--runtime",
                    "all",
                    "--installable-manifest-root",
                    manifests_tmp,
                    "--exercise-skill-root",
                    exercise_tmp,
                )
                self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)

                summary = json.loads(proc.stdout)
                self.assertEqual(summary["manifest_count"], 16)
                self.assertEqual(summary["exercise_count"], 16)
                self.assertEqual(summary["smoke_check"], "passed")
                self.assertEqual(summary["exercise_smoke_check"], "passed")
                self.assertTrue(summary["session_only"])
                self.assertFalse(summary["global_install_modified"])

                skill_file = Path(exercise_tmp) / "codex" / "core-ops" / "SKILL.md"
                interface_file = (
                    Path(exercise_tmp)
                    / "codex"
                    / "core-ops"
                    / "agents"
                    / "openai.yaml"
                )
                summary_file = Path(exercise_tmp) / "manifest-exercise-summary.json"
                self.assertTrue(skill_file.is_file())
                self.assertTrue(interface_file.is_file())
                self.assertTrue(summary_file.is_file())
                self.assertFalse(
                    (
                        Path(exercise_tmp)
                        / "claude-code"
                        / "core-ops"
                        / "agents"
                        / "openai.yaml"
                    ).exists()
                )

                text = skill_file.read_text(encoding="utf-8")
                self.assertTrue(text.startswith("---\n"))
                self.assertIn('name: "core-ops"', text)
                self.assertIn("session-only runtime exercise", text)
                self.assertIn("Source of truth: `kernel`", text)
                self.assertIn("Manual review required: `true`", text)
                self.assertIn("Safe to install automatically: `false`", text)
                self.assertIn("profile-first-entrypoint", text)

                exercise_summary = json.loads(summary_file.read_text(encoding="utf-8"))
                self.assertEqual(
                    exercise_summary["exercise_schema_version"],
                    "0.1-session-only",
                )
                self.assertEqual(exercise_summary["exercise_count"], 16)
                self.assertTrue(exercise_summary["session_only"])
                self.assertFalse(exercise_summary["global_install_modified"])

    def test_undeclared_runtime_fails_for_kernel(self) -> None:
        proc = self.run_script(
            "schemas/skill-kernel/examples/paper-reading.kernel.json",
            "--runtime",
            "cursor",
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("does not declare runtime `cursor`", proc.stderr)

    def test_check_does_not_write_output_dir(self) -> None:
        with tempfile.TemporaryDirectory(prefix="kernel-adapters-") as tmp:
            proc = self.run_script("--runtime", "codex", "--check", "--output-dir", tmp)
            self.assertEqual(proc.returncode, 2)
            self.assertIn("--check cannot be combined with output-writing options", proc.stderr)
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_check_does_not_write_preview_skill_root(self) -> None:
        with tempfile.TemporaryDirectory(prefix="kernel-preview-skills-") as tmp:
            proc = self.run_script("--runtime", "codex", "--check", "--preview-skill-root", tmp)
            self.assertEqual(proc.returncode, 2)
            self.assertIn("--check cannot be combined with output-writing options", proc.stderr)
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_check_does_not_write_installable_manifest_root(self) -> None:
        with tempfile.TemporaryDirectory(prefix="kernel-installable-manifests-") as tmp:
            proc = self.run_script(
                "--runtime",
                "codex",
                "--check",
                "--installable-manifest-root",
                tmp,
            )
            self.assertEqual(proc.returncode, 2)
            self.assertIn("--check cannot be combined with output-writing options", proc.stderr)
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_exercise_skill_root_requires_installable_manifest_root(self) -> None:
        with tempfile.TemporaryDirectory(prefix="kernel-manifest-exercise-") as tmp:
            proc = self.run_script("--exercise-skill-root", tmp)
            self.assertEqual(proc.returncode, 2)
            self.assertIn(
                "--exercise-skill-root requires --installable-manifest-root",
                proc.stderr,
            )
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_exercise_skill_root_rejects_known_global_skill_roots(self) -> None:
        with tempfile.TemporaryDirectory(prefix="kernel-installable-manifests-") as manifests_tmp:
            unsafe_root = Path.home() / ".codex" / "skills" / "kernel-exercise-test"
            proc = self.run_script(
                "--runtime",
                "codex",
                "--installable-manifest-root",
                manifests_tmp,
                "--exercise-skill-root",
                unsafe_root,
            )
            self.assertEqual(proc.returncode, 2)
            self.assertIn("--exercise-skill-root is unsafe", proc.stderr)

    def test_runtime_contract_fixture_records_observed_codex_and_claude_surfaces(self) -> None:
        contracts = json.loads(CONTRACTS.read_text(encoding="utf-8"))
        self.assertEqual(contracts["schema_version"], "0.1")
        self.assertIn("contracts", contracts)

        codex = contracts["contracts"]["codex"]
        claude = contracts["contracts"]["claude-code"]
        self.assertEqual(codex["support_level"], "observed-local-install")
        self.assertEqual(claude["support_level"], "observed-local-install")
        self.assertIn("~/.agents/skills/<skill-name>", codex["skill_roots"])
        self.assertIn("~/.claude/skills/<skill-name>", claude["skill_roots"])

        for runtime, contract in {"codex": codex, "claude-code": claude}.items():
            with self.subTest(runtime=runtime):
                self.assertEqual(contract["required_files"], ["SKILL.md"])
                self.assertEqual(
                    contract["frontmatter"]["required"],
                    ["name", "description"],
                )
                self.assertEqual(contract["frontmatter"]["description_max_chars"], 500)

    def test_claude_projection_omits_openai_interface_metadata(self) -> None:
        proc = self.run_script("--runtime", "claude-code")
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        bundle = json.loads(proc.stdout)

        for adapter in bundle["adapters"]:
            with self.subTest(kernel=adapter["kernel"]["kernel_id"]):
                self.assertEqual(
                    adapter["runtime_contract"]["contract_id"],
                    "claude-code-skill-directory-v0",
                )
                self.assertNotIn("interface_metadata", adapter["runtime_projection"])
                self.assertEqual(
                    adapter["runtime_projection"]["skill_markdown"]["frontmatter"][
                        "name"
                    ],
                    adapter["kernel"]["kernel_id"],
                )

    def test_runtime_trigger_capture_records_codex_and_claude_preview_visibility(self) -> None:
        capture = json.loads(TRIGGER_CAPTURE.read_text(encoding="utf-8"))
        expected = {
            "core-ops",
            "paper-reading",
            "research-distillation-workflow-contract",
        }
        self.assertEqual(set(capture["preview_source"]["expected_skills"]), expected)

        codex = capture["codex"]
        self.assertFalse(codex["staging"]["global_install_modified"])
        self.assertEqual(codex["prompt_visibility"]["status"], "passed")
        self.assertEqual(
            set(codex["prompt_visibility"]["visible_preview_skills"]),
            expected,
        )
        codex_tasks = {
            task["expected_preview_skill"]: task
            for task in codex["model_route"]["tasks"]
        }
        self.assertFalse(codex_tasks["core-ops"]["preview_skill_selected"])
        self.assertTrue(codex_tasks["paper-reading"]["preview_skill_selected"])
        self.assertTrue(
            codex_tasks["research-distillation-workflow-contract"][
                "preview_skill_selected"
            ]
        )

        claude = capture["claude_code"]
        self.assertFalse(claude["staging"]["global_install_modified"])
        self.assertEqual(claude["plugin_validation"]["status"], "passed-with-warning")
        self.assertEqual(claude["prompt_visibility"]["status"], "passed")
        self.assertEqual(
            set(claude["prompt_visibility"]["visible_preview_skills"]),
            expected,
        )
        self.assertEqual(claude["model_route"]["status"], "blocked")
        self.assertIn("Not logged in", claude["model_route"]["blocker"])

    def test_core_ops_runtime_semantics_capture_resolves_profile_first_behavior(self) -> None:
        capture = json.loads(CORE_OPS_SEMANTICS_CAPTURE.read_text(encoding="utf-8"))
        scenarios = {
            scenario["id"]: scenario
            for scenario in capture["codex"]["scenarios"]
        }
        self.assertFalse(scenarios["full-shared-root"]["core_ops_selected"])
        self.assertTrue(scenarios["profile-first-hinted"]["core_ops_selected"])
        self.assertTrue(scenarios["isolated-core-ops-root"]["core_ops_selected"])
        self.assertEqual(
            capture["decision"]["core_ops_runtime_expectation"],
            "profile-first-entrypoint",
        )
        self.assertIn(
            "mature owner skills",
            capture["decision"]["delegation_policy"],
        )

    def test_manifest_exercise_runtime_capture_records_session_only_behavior(self) -> None:
        capture = json.loads(MANIFEST_EXERCISE_CAPTURE.read_text(encoding="utf-8"))
        expected = {
            "core-ops",
            "paper-reading",
            "research-distillation-workflow-contract",
        }
        source = capture["manifest_exercise_source"]
        self.assertEqual(set(source["expected_skills"]), expected)
        self.assertTrue(source["session_only"])
        self.assertFalse(source["global_install_modified"])
        self.assertFalse(source["safe_to_install_automatically"])

        codex = capture["codex"]
        self.assertFalse(codex["staging"]["global_install_modified"])
        self.assertEqual(codex["prompt_visibility"]["status"], "passed")
        self.assertEqual(
            set(codex["prompt_visibility"]["visible_session_only_skills"]),
            expected,
        )
        tasks = {
            task["id"]: task
            for task in codex["model_route"]["tasks"]
        }
        self.assertFalse(
            tasks["shared-repo-root-profile-first-closeout"]["session_skill_selected"]
        )
        self.assertEqual(
            tasks["shared-repo-root-profile-first-closeout"]["selected_profile_skill"],
            "project-ops-router",
        )
        self.assertTrue(
            tasks["isolated-empty-workdir-core-ops-closeout"]["session_skill_selected"]
        )
        self.assertEqual(
            tasks["isolated-empty-workdir-core-ops-closeout"]["selected_profile_skill"],
            "core-ops",
        )
        self.assertTrue(
            tasks["isolated-empty-workdir-paper-reading"]["session_skill_selected"]
        )
        self.assertEqual(
            tasks["isolated-empty-workdir-paper-reading"]["selected_profile_skill"],
            "paper-reading",
        )
        self.assertTrue(
            tasks["isolated-empty-workdir-research-distillation"]["session_skill_selected"]
        )
        self.assertIn(
            "research-distillation-workflow-contract",
            tasks["isolated-empty-workdir-research-distillation"]["selected_leaf_skills"],
        )

        claude = capture["claude_code"]
        self.assertFalse(claude["staging"]["global_install_modified"])
        self.assertEqual(claude["plugin_validation"]["status"], "passed-with-warning")
        self.assertEqual(claude["prompt_visibility"]["status"], "passed")
        self.assertEqual(
            set(claude["prompt_visibility"]["visible_session_only_skills"]),
            expected,
        )
        self.assertEqual(
            claude["bare_plugin_probe"]["status"],
            "plugin-load-passed-model-route-blocked",
        )
        self.assertEqual(claude["model_route"]["status"], "blocked")
        self.assertIn("Not logged in", claude["model_route"]["blocker"])


if __name__ == "__main__":
    unittest.main()

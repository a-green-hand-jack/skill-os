---
auto-generated: true
refresh: regenerate after structural changes (kernel schema, contract, installer, chain installer)
volatile-fields: git-state, sibling-pack-HEADs, test-counts
---

# Project Briefing — skill-os

> **Must-read at session start.** Re-verify volatile facts (git state, sibling pack HEADs) before acting.

## Identity

- Project: `skill-os` — the hub / framework of the [Skill OS matrix](https://github.com/a-green-hand-jack/skill-os). Owns the rules; pack repos own the skills.
- Phase: post-Phase-B2 maintenance | Gate: keep all 47 tests passing; never regress the safe-install / repo-split refusal chain.
- Repo: `a-green-hand-jack/skill-os`. Public on GitHub since 2026-05-28.

## Critical Must-Know

- **47 tests pass** as of 2026-05-28 (5 test files: `test_skill_kernel_adapter_export` 16 / `test_profile_routing_harness` 6 / `test_resolve_profile_dependencies` 7 / `test_synthetic_install_chain` 7 / `test_synthetic_repo_split_chain` 2 / `test_synthetic_cross_repo_install` 5 / `test_synthetic_chain_install` 4). The 22 skill-dependent tests that used to live in ml-research-skills were either deleted (after hard-slim) or replaced by synthetic-fixture coverage here.
- **Authoritative content this repo owns** (NOT in any pack repo):
  - `schemas/skill-kernel/skill-kernel.schema.json` — portable kernel schema
  - `schemas/skill-kernel/install-handoff-contract.schema.json` + `install-handoff-contract-2026-05-28.json` (active, `reviewed-execute-enabled`) + `install-handoff-contract-2026-05-27.json` (frozen, `superseded`)
  - `schemas/skill-kernel/install-plan.schema.json` + `write-actions.schema.json` + `repo-split-inventory.schema.json` + `repo-split-privacy-audit.schema.json`
  - `schemas/skill-kernel/runtime-adapter-contracts.json` + 3 runtime captures
  - `schemas/skill-kernel/examples/{core-ops, paper-reading, automation, quick-experiment, research-distillation-workflow-contract}.kernel.json` — reference kernels (each pack repo has its own copy as the authoritative one)
  - `schemas/skill-kernel/repo-split/*.json` — generated inventories + audits for the 5 split-target packs
  - `schemas/skill-kernel/examples/install-plans/*.plan.json` — 7 plan fixtures
  - `schemas/skill-kernel/proposed-revisions/install-handoff-contract-2026-05-28.proposal.md`
  - `profiles/profile-index.yaml` — full matrix registry with github_url + depends_on for each profile
  - `docs/design/skill-matrix.md` — design doc
- **Scripts** (all in `scripts/`):
  - `apply_install_plan.py`, `apply_repo_split.py` — real installer + scaffolder (refuse without --execute, refuse global skill roots, refuse without contract authorization)
  - `export_skill_kernel_adapters.py` — dry-run adapter export, preview skill roots, installable manifest prototypes, session-only exercise roots
  - `inventory_profile_for_split.py` — source inventory + privacy audit (accepts `--source-root` for sibling packs)
  - `preview_install_writer.py`, `preview_repo_split_writer.py` — read-only write-action enumerators (accept `--source-root`)
  - `validate_install_handoff_plan.py` — plan validator (accepts `--source-root` since ACT-082; multi-root resolution for cross-repo installs)
  - `validate_skill_taxonomy.py` — full taxonomy + profile + kernel schema consistency check
  - `validate_skills.py` — skill sanity (frontmatter, naming, helper references)
  - `score_profile_routing.py` — profile-routing eval scorer
  - `memory_bootstrap.py` — memory contract bootstrap
  - `resolve_profile_dependencies.py` (ACT-077) — depends_on chain resolver
  - `install_profile_chain.py` (ACT-081) — chain installer: resolves depends_on + drives apply_install_plan per step
- **Active contract gates**: `automation_policy.real_installer_authorized: true`. `may_write_runtime_files_without_review: false`. `may_write_global_roots_without_explicit_user_request: false`. Modes `project-local-profile-install` + `repo-split-handoff` are `allowed_now: true`; `global-bootstrap-install` + `maintainer-debug-global-install` are `allowed_now: false`.
- **Sibling pack repos** (all live on GitHub at `a-green-hand-jack/*` as of 2026-05-28):
  - `core-ops-skills` (12 skills, substrate)
  - `automation-skills` (6, depends_on core-ops)
  - `paper-reading-skills` (11, depends_on core-ops)
  - `research-distillation-skills` (13, depends_on core-ops)
  - `quick-experiment-skills` (9, depends_on core-ops + automation)
  - `ml-research-skills` (46 after hard-slim, depends_on all five above)
- Validation: `python3 -m unittest discover tests` runs all 47. `python3 scripts/export_skill_kernel_adapters.py --runtime all --check` must PASS (currently "generated 13 dry-run adapter(s) from 4 kernel(s)" — see schemas/skill-kernel/examples/ for kernel count). `uv run scripts/validate_skill_taxonomy.py` is the deepest invariant check.
- Cross-repo install: scripts accept `--source-root <pack-path>` (or `SKILL_OS_SOURCE_ROOT` env var). The chain installer uses `--pack-search-path` to find pack repos by `future_repo` name.
- Empty `skills/.gitkeep` exists because the active contract lists `skills` as an authoritative source path; skill-os doesn't own skill files.
- Git closeout: use `git push` directly. No `project-push` wrapper here.

## Top Claims

- The matrix can be installed end-to-end with one command: `python3 scripts/install_profile_chain.py <profile> --target-parent <project>/.agents/skills --pack-search-path <packs-parent> --execute` — `confirmed` (validated 2026-05-28 against quick-experiment chain pulling from 3 GitHub-cloned packs).
- All 7 pack repos in the matrix are public on GitHub at `a-green-hand-jack/*` — `confirmed`.
- The installer and scaffolder refuse to write under any known global skill root regardless of contract state — `confirmed` (tests in `test_synthetic_install_chain.py` and `test_synthetic_cross_repo_install.py`).

## Top Risks

- RSK-024: Hub schema drift if a pack repo's kernel diverges from the reference example in this repo. Mitigated by `--source-root` resolution but not yet enforced automatically.
- RSK-027: When a sibling pack is updated independently, the pinned commit in `profile-index.yaml` becomes stale until refreshed. Mitigated by `verify_pack_pins.py` returning non-zero on mismatch; pin refresh is operator-driven.

## Open Actions (skill-os scope)

- ACT-077 + ACT-080 + ACT-081 + ACT-082 + ACT-085 + ACT-086 + ACT-087 — all `done`.
- (queue empty)

## Decision Log (recent)

- ACT-086 (2026-05-28): each sibling pack has a `pinned_commit` + `pinned_at` in `profiles/profile-index.yaml` `repo_matrix`. `scripts/verify_pack_pins.py` is read-only and exits non-zero on mismatch; it never auto-checks-out the pinned ref. 4 tests in `test_verify_pack_pins.py`. Total skill-os test count: 58.
- ACT-085 (2026-05-28): matrix-wide leaf-routing regression fixture lives in **skill-os** (`tests/routing-evals.json` + `tests/test_routing_evals.py`). Reasoning: skills referenced by the evals span 6 pack repos after the hard-slim; only the hub sees the full matrix. The test enforces structural well-formedness; cross-pack skill-existence checks would require every pack cloned alongside and are an opt-in script, not part of the default suite.

## Full Memory

`memory/project-conventions.md` · `memory/hot-results.md` · `memory/current-status.md` · `memory/decision-log.md` · `memory/action-board.md` · `memory/risk-board.md`

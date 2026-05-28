---
auto-generated: true
refresh: run research-project-memory --closeout or update manually after major work
volatile-fields: git-state, installed-skill-copies
---

# Project Briefing — ml-research-skills

> **Must-read at session start.** Re-verify volatile facts (git state, installed copies) before acting.

## Identity

- Project: ml-research-skills (ML research domain pack and first profile in a broader skill-matrix system)
- Phase: maintenance | Gate: keep validation passing; update README/AGENTS/CLAUDE/profiles/memory on skill or profile changes
- Repo: `a-green-hand-jack/ml-research-skills` | Global bootstrap: `npx skills add a-green-hand-jack/ml-research-skills -g -a codex claude-code -s ml-research-bootstrap -y`

## Critical Must-Know

- **74 skills** as of 2026-05-25 (69 leaf/utility + 4 domain routers + 1 root router). All frontmatter, helper references, and doc-table entries must stay in sync.
- **5 routers**: `ml-research-router` (root) + `experiment-evidence-router`, `project-ops-router`, `paper-writing-router`, `discovery-router` (domain) — route-only, no business logic.
- Profile layer: `profiles/profile-index.yaml` is the agent-neutral install/routing registry; `schemas/skill-kernel/` is the minimum portable kernel schema with five checked example kernels — `core-ops`, `paper-reading`, `research-distillation`, `automation`, `quick-experiment` — plus `runtime-adapter-contracts.json`, runtime captures, resolved `core-ops` selection semantics, review-gated installable manifest prototypes, session-only manifest exercises, reviewed install/repo-split handoff contract (active: `install-handoff-contract-2026-05-28.json`, `reviewed-execute-enabled`; frozen pre-revision `install-handoff-contract-2026-05-27.json` preserved for refusal regression), install-plan schema, repo-split source-inventory + privacy-audit schemas, and five checked-in repo-split inventories (core-ops 78 / paper-reading 88 / research-distillation 90 / automation 63 / quick-experiment 62 files, all audits `status: passed`). After ACT-073 + ACT-075, `remote-project-control` and `run-status-monitor` are owned by `automation` (not `core-ops`); `quick-experiment` declares `depends_on: [core-ops, automation]`; `automation` declares `depends_on: core-ops`. **As of ACT-074, all five profiles are real-split into sibling local repos under `/Users/jieke/Projects/<profile>-skills/`** (commit hashes in EVD-060); pushes to GitHub deferred to ACT-076. The exporter generates 16 dry-run adapter manifests from 5 kernels. `scripts/export_skill_kernel_adapters.py` dry-runs runtime metadata, preview roots, prototype manifests, and session-only exercise roots while keeping kernels authoritative; `scripts/validate_install_handoff_plan.py` validates install/repo-split plans without writing files; `scripts/preview_install_writer.py` and `scripts/preview_repo_split_writer.py` enumerate read-only write-actions; `scripts/inventory_profile_for_split.py` produces inventory + privacy audit; `scripts/apply_install_plan.py` and `scripts/apply_repo_split.py` are the real installer / scaffolder that execute reviewed plans under the active contract through explicit `--execute`, refuse known global roots, and emit rollback records. `docs/design/skill-matrix.md` records the multi-repo Skill OS direction; `profiles/research-distillation/` has profile-local artifacts. Active profiles: `global-bootstrap`, `ml-research`; draft profiles: `core-ops`, `paper-reading`, `research-distillation`, `automation`.
- Runtime selection: `core-ops` is a profile-first entrypoint for isolated/profile-first contexts and an intentional delegator when mature owner skills are visible in a full shared root.
- Install boundary: global installs should default to `ml-research-bootstrap`; install the full bundle only inside initialized ML research projects or for maintainer/debug validation.
- Unknown project-local skill selection: inside an initialized ML research project, start at `ml-research-router`; it reads `references/skill-index.md` for budget-resilient routing when leaf descriptions are truncated.
- Validation: `python3 scripts/validate_skills.py` — must pass before every commit.
- Template placeholders must use `{{UPPER_SNAKE_CASE}}` — lowercase triggers a validator error.
- Git closeout: use `project-push /Users/jieke/Projects/project-skills origin main` for routine pushes.
- Skill descriptions are routing rules, not titles — Codex hard-limits 500 chars per skill.
- Memory bootstrap: `uv run scripts/memory_bootstrap.py [--skill <name>]` — prints MUST READ / ACTIVE FACTS / DO NOT / WRITEBACK for any task.
- Taxonomy validator: `uv run scripts/validate_skill_taxonomy.py` — checks router/leaf consistency, expected_path chains, memory contracts, skill-index.yaml, profile-index.yaml schema, skill-kernel schema/examples, and profile-routing eval targets.
- Memory reliability: `memory/fact-index.yaml` (P0 facts), `memory/memory-revision.json` rev 32 (stale detection), `taxonomy/memory-contracts/` (per-skill contracts).
- Startup memory includes root `memory/project-conventions.md` and `memory/hot-results.md`; both paths must exist.
- Project-code worktrees share uv env by default: `UV_PROJECT_ENVIRONMENT=<ProjectRoot>/.uv-envs/code` plus `uv run` from the active worktree; use stage envs only for dependency/stack/sync-risk exceptions.

## Top Claims

- Collection covers the full ML research lifecycle from idea to release — `confirmed`
- All skills are ≤500 lines SKILL.md; larger reference material lives in linked files — `confirmed`

## Open Actions (top 3)

- ACT-038: Design and ship `memory/BRIEFING.md` + `hot-results.md` pattern to solve agent forgetting — `done` (this session)
- ACT-039: Reinstall updated skills after memory-reliability/routing changes — `done` (local global install 2026-05-20)
- ACT-041: Add shared project-code uv env policy for sibling worktrees — `done`
- ACT-042: Harden root skill discovery for listing-budget truncation — `done`
- ACT-044: Add first profile registry for broader skill-matrix design — `done`
- ACT-045: Harden profile schema and add skill-matrix design doc — `done`
- ACT-046: Add profile-level routing evals before leaf routing — `done`
- ACT-047: Add profile-routing scoring harness — `done`
- ACT-048: Add research-distillation profile-local templates — `done`
- ACT-049: Trial research-distillation on ByteDance UI-TARS — `done`
- ACT-050: Compare UI-TARS with Tongyi DeepResearch — `done`
- ACT-051: Draft combined `agent-workflow-contract-planner` proposal — `done`
- ACT-052: Add workflow-contract template and routing evals — `done`
- ACT-053: Exercise workflow-contract template on real tasks — `done`
- ACT-054: Define minimum `skill-kernel` schema — `done`
- ACT-055: Instantiate core-ops and second profile kernels — `done`
- ACT-056: Design kernel adapter/export dry run — `done`
- ACT-057: Compare dry-run adapters with real Codex/Claude metadata expectations — `done`
- ACT-058: Generate preview SKILL.md fixtures from runtime projections — `done`
- ACT-059: Capture actual Codex/Claude runtime trigger behavior from preview roots — `done`
- ACT-060: Resolve `core-ops` profile-first adapter semantics before installable manifests — `done`
- ACT-061: Prototype installable adapter manifests from dry-run projections — `done`
- ACT-062: Exercise installable manifest prototypes in a temporary runtime/session-only root without modifying global installs — `done`
- ACT-063: Capture actual Codex/Claude prompt-surface behavior from manifest-exercised session-only roots — `done`
- ACT-064: Define the reviewed install or repo-split handoff contract from the manifest-exercise runtime capture before writing any real installer — `done`
- ACT-065: Implement a non-mutating install-plan validator before any runtime write command — `done`
- ACT-066: Exercise the validator on concrete `core-ops` project-local install and repo-split plan fixtures — `done`
- ACT-067: Build a read-only install writer preview that enumerates the exact write actions a future installer would emit — `done`
- ACT-068: Generate a programmatic source inventory and publication audit for the `core-ops` profile (95 files, 14 skills, audit passed) — `done`
- ACT-069: Add a repo-split preview that enumerates copy/scaffold actions for a passing repo-split plan (153 actions on the `core-ops` plan) — `done`
- ACT-070: Extend inventory + privacy audit + repo-split preview to `paper-reading` (88 files) and `research-distillation` (90 files) — `done`
- ACT-071: Ship real installer + scaffolder gated by active contract, plus drafted contract-revision proposal — `done`
- ACT-072: Apply the contract revision to authorize real reviewed-plan writes (active contract is now `install-handoff-contract-2026-05-28.json`; frozen 05-27 contract preserved for refusal regression) — `done`
- ACT-073: Restructure profile axes — promoted `automation` to real splittable profile (63 files / 6 skills); moved remote-project-control + run-status-monitor from core-ops to automation; documented depends_on:core-ops — `done`
- ACT-074: Real-split the five profiles into sibling local repos under /Users/jieke/Projects/ (core-ops-skills @ fffb379, paper-reading-skills @ 84f78b7, research-distillation-skills @ c3287c3, automation-skills @ 6a56d86, quick-experiment-skills @ 8a4355b); push to GitHub deferred — `done`
- ACT-075: Evaluate axis additions — ADD quick-experiment (5th split-target, 62 files / 9 skills, depends_on core-ops + automation); SKIP code-engineering — `done`
- ACT-076: Push the five destination repos to GitHub at `a-green-hand-jack/*` (public, topic-tagged: skill-os, agent-skills, claude-code, codex + per-profile) — `done`
- ACT-077: Implement installer-level enforcement of profile depends_on chains — `todo`

## Top Risks

- RSK-001: Skill inventory drift between `skills/`, README, AGENTS, CLAUDE, and installed runtime copies
- RSK-004: Memory could become stale if not updated after skill behavior changes
- RSK-021: Agents may still run bare `uv sync` in a worktree until updated skills/templates are reinstalled or reread
- RSK-023: Profile registry can drift from real skills or future split repos if not validated

## Full Memory

`memory/project-conventions.md` · `memory/hot-results.md` · `memory/current-status.md` · `memory/decision-log.md` · `memory/action-board.md` · `memory/risk-board.md`

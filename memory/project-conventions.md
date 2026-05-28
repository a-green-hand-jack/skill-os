# Project Conventions

Active rules agents must follow in this project. Maintained by `research-project-memory`.
Last reviewed: 2026-05-26

> Read this file at every session start immediately after `memory/BRIEFING.md`.
> When a convention no longer applies, move it to **Expired** with a reason; do not silently delete it.

## Active

| ID | Rule | Category | Since | Notes |
|----|------|----------|-------|-------|
| PC-001 | Run scope detection before substantial memory work: `git rev-parse --show-toplevel` and `git rev-parse --git-common-dir`. | worktree | 2026-05-15 | Prevents worktree-local results from being written into root project memory. |
| PC-002 | Read `memory/BRIEFING.md`, then this file, then `memory/hot-results.md` before project-root maintenance decisions. | memory | 2026-05-16 | `hot-results.md` is intentionally present even though this skill repo has no experiment results. |
| PC-003 | Use `python3 scripts/validate_skills.py` and `uv run scripts/validate_skill_taxonomy.py` before committing skill, template, helper, inventory, profile, or memory protocol changes. | validation | 2026-05-05 | First validator covers 74 skills and routing/template sanity. Second covers router-child consistency, expected_path chains, memory contracts, skill-index.yaml, and profile-index.yaml. |
| PC-004 | Use `project-push /Users/jieke/Projects/project-skills origin main` for routine pushes after safe-git preflight. | git | 2026-05-12 | Do not replace preflight with the wrapper; pass explicit repo, remote, and branch. |
| PC-005 | Keep `skills/`, README.md, AGENTS.md, CLAUDE.md, `memory/`, and installed skill copies aligned after skill behavior changes. | maintenance | 2026-05-05 | Reinstall changed skills when runtime behavior or routing metadata changes. |
| PC-006 | Inside initialized ML research projects, when the user describes an ML research workflow but does not know or name the skill, start at `ml-research-router`; for clear-domain tasks, route through the relevant domain router before guessing leaf skills. | routing | 2026-05-18 | Root router loads `references/skill-index.md` for budget-resilient discovery when leaf descriptions are truncated. Domain routers load `contrastive-routing.md` for confusable pairs. |
| PC-007 | When adding or materially changing memory/fact-index.yaml or memory/project-conventions.md, increment the revision in memory/memory-revision.json. | memory | 2026-05-18 | Enables stale-session detection via `uv run scripts/memory_bootstrap.py --check-stale`. |
| PC-008 | Default global installation to `ml-research-bootstrap`; install the full ML research bundle only inside initialized ML research projects or for maintainer/debug validation of this skill repo. | install | 2026-05-25 | Prevents the full lifecycle bundle from interfering with ordinary non-ML projects while keeping project-local ML research workflows powerful. |
| PC-009 | Treat project profiles as the first-class install/routing boundary for the broader skill-matrix design; keep `profiles/profile-index.yaml`, `tests/profile-routing-evals.json`, `scripts/score_profile_routing.py`, and `docs/design/skill-matrix.md` agent-neutral and validate profile schema/evals plus the harness before closeout. | profile | 2026-05-26 | Current active profile is `ml-research`; draft profiles identify future `core-ops`, paper-reading, research-distillation, and automation pack boundaries. |
| PC-010 | Register profile-local docs, templates, and examples in `profiles/profile-index.yaml` under `artifacts`, keep them under `profiles/<profile-name>/`, and add a focused asset test when the assets define reusable workflow structure. | profile | 2026-05-26 | Prevents draft profile assets from becoming untracked prose before a separate skill pack exists. |

## Suspended

<!-- Temporarily inactive conventions - may be re-activated. -->

| ID | Rule | Category | Suspended | Resume condition |
|----|------|----------|-----------|-----------------|

## Expired

<!-- Dead conventions - kept for audit trail. -->

| ID | Rule | Category | Expired | Reason |
|----|------|----------|---------|--------|

---

## Categories

`git` · `ssh` · `python-env` · `memory` · `compute` · `paper` · `worktree` · `shell` · `validation` · `maintenance` · `install` · `profile` · `other`

## Lifecycle

- **Active** -> agent must follow now
- **Suspended** -> skip until resume condition is met
- **Expired** -> convention no longer applies; keep row for audit trail, add reason

## Update Rule

- Add a row when a new project-specific convention is established by any skill.
- Expire a row when infrastructure, scope, or project phase makes it obsolete.
- Never delete rows; move to Expired so future sessions know the history.
- Review at every major phase transition or after repeated agent regressions.

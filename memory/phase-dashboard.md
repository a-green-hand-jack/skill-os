# ml-research-skills Phase Dashboard

> Global project-cycle view for this skill-system repository.

## Current Phase

- Phase: `maintenance`
- Readiness: `partial`
- Objective: keep the skill collection coherent, installable, memory-backed, and auditable as the workflow architecture evolves.
- Active gate: choose Fast / Skill / Code / Risk closeout path, then run only the validation needed for the selected path before push; profile changes also require `uv run scripts/validate_skill_taxonomy.py`; profile-routing harness, research-distillation asset, skill-kernel adapter-export, preview-root, installable-manifest, manifest-exercise, runtime trigger-capture, runtime selection-semantics, manifest-exercise runtime-capture, install-handoff contract, and install-plan validator changes require their focused tests.
- Next phase trigger: a tagged skill-system release or a successful full audit showing memory, sidecar routing, personalization writeback, source-card routing, publication audits, run-status artifacts, SSH wrapper routing/templates, stable push wrappers, token telemetry, and code review protocols are consistently wired across high-value skills.
- Last updated: 2026-05-27

## Phase Table

| Phase | Status | Gate | Linked claims | Linked evidence | Blocking risks | Active actions |
|---|---|---|---|---|---|---|
| idea | done | project has clear purpose and lifecycle scope | CLM-001 | EVD-001 |  |  |
| positioning | done | skill system positioned as ML research lifecycle tooling | CLM-001 | EVD-001 | RSK-001 | ACT-003 |
| method-design | done | memory, sidecar, reviewer, token, and toolchain protocols defined | CLM-001, CLM-002, CLM-003, CLM-004, CLM-005 | EVD-002, EVD-003, EVD-004, EVD-005 | RSK-002, RSK-004 | ACT-001, ACT-002 |
| implementation | partial | skills and helper scripts exist and pass focused checks | CLM-002, CLM-003, CLM-004, CLM-005 | EVD-003, EVD-004, EVD-005 | RSK-005 | ACT-005 |
| internal-review | partial | periodic skill-system audit and isolated reviews catch drift | CLM-002, CLM-005 | EVD-003 | RSK-001, RSK-005 | ACT-003 |
| artifact-release | partial | install command succeeds for Codex and Claude Code | CLM-005 | EVD-006 | RSK-001 | ACT-005 |
| maintenance | partial | docs, memory, profiles, sidecars, tags, telemetry, personalization writeback, source-card routing, publication audits, run-status artifacts, SSH wrapper routing/templates, stable push wrappers, paper-layout protocols, visual-style memory, layered writing contracts, and commit closeout paths remain current | CLM-001, CLM-003, CLM-004, CLM-006, CLM-008, CLM-009, CLM-010, CLM-011, CLM-012, CLM-013, CLM-014, CLM-015, CLM-016, CLM-017, CLM-018, CLM-026 | EVD-004, EVD-006, EVD-007, EVD-010, EVD-011, EVD-012, EVD-013, EVD-014, EVD-015, EVD-016, EVD-017, EVD-018, EVD-019, EVD-020, EVD-029, EVD-032, EVD-033, EVD-034, EVD-035, EVD-036, EVD-037, EVD-038, EVD-039, EVD-040, EVD-041, EVD-042, EVD-043, EVD-044, EVD-045, EVD-046, EVD-047, EVD-048, EVD-049, EVD-050 | RSK-003, RSK-004, RSK-002, RSK-006, RSK-007, RSK-008, RSK-009, RSK-010, RSK-011, RSK-012, RSK-023, RSK-024 | ACT-001, ACT-004, ACT-006, ACT-011, ACT-012, ACT-013, ACT-014, ACT-015, ACT-016, ACT-017, ACT-018, ACT-019, ACT-020, ACT-021, ACT-044, ACT-047, ACT-048, ACT-049, ACT-050, ACT-051, ACT-052, ACT-053, ACT-054, ACT-055, ACT-056, ACT-057, ACT-058, ACT-066 |

## Stale Or Regressed Objects

| Object | Why stale/regressed | Required check | Owner | Updated |
|---|---|---|---|---|
| README/AGENTS/CLAUDE skill summaries | They drift whenever skills are added or behavior changes. | `python3 scripts/validate_skills.py` and manual summary check. | agent | 2026-05-05 |
| Installed global skills | They drift after skill commits unless reinstalled. | Prefer targeted `npx skills add ... -s <skill-name> -y`; use full reinstall when inventory or many skills changed. | agent | 2026-05-06 |

## Next Session Entry Point

- Open: `memory/current-status.md`.
- Verify: `git status --short --branch`.
- Then: run the relevant validation gates for the files being changed; for skill-kernel adapter work include `tests.test_skill_kernel_adapter_export`, `python3 scripts/export_skill_kernel_adapters.py --runtime all --check`, preview-root smoke when `SKILL.md` fixture generation changes, installable-manifest smoke when manifest output changes, manifest-exercise smoke when session-only roots change, runtime trigger/selection/manifest-exercise capture review when adapter installability is being considered, install-handoff contract checks before any real installer or repo split, and `tests.test_install_handoff_plan_validator` when plan validation changes.

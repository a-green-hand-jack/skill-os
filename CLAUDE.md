# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with
code in this repository.

## Repository Purpose

**skill-os** — the framework / hub of the portable agent **Skill OS** matrix.
It owns kernel schema, install/repo-split handoff contract, installer +
scaffolder + validator scripts, and the matrix registry. The actual agent
skills live in per-profile pack repos:

- [core-ops-skills](https://github.com/a-green-hand-jack/core-ops-skills)
- [automation-skills](https://github.com/a-green-hand-jack/automation-skills)
- [paper-reading-skills](https://github.com/a-green-hand-jack/paper-reading-skills)
- [research-distillation-skills](https://github.com/a-green-hand-jack/research-distillation-skills)
- [quick-experiment-skills](https://github.com/a-green-hand-jack/quick-experiment-skills)
- [ml-research-skills](https://github.com/a-green-hand-jack/ml-research-skills) (full bundle pending Phase B2 slim)

This is **Phase B1** of the hub migration — kernel infrastructure has moved
here from `ml-research-skills`, but the operational tests that need a live
`skills/` directory remain in `ml-research-skills` until Phase B2.

## Testing Changes

Only the skill-independent tests run cleanly here:

```bash
python3 -m unittest -v tests.test_skill_kernel_adapter_export
python3 -m unittest -v tests.test_profile_routing_harness
```

The skill-dependent tests (`test_skill_kernel_schema`,
`test_install_handoff_plan_validator`, `test_install_plan_fixtures`,
`test_install_writer_preview`, `test_repo_split_inventory`,
`test_repo_split_writer_preview`, `test_apply_install_plan`) live in
`ml-research-skills` for now and will return here in Phase B2 with synthetic
fixtures.

Dry-run adapter export should always pass:

```bash
python3 scripts/export_skill_kernel_adapters.py --runtime all --check
```

## Operating The Installer And Scaffolder

`scripts/apply_install_plan.py` and `scripts/apply_repo_split.py` execute
reviewed install plans against the active contract
(`schemas/skill-kernel/install-handoff-contract-2026-05-28.json`,
`reviewed-execute-enabled`). They:

- Refuse known global skill roots regardless of contract state
- Refuse to write until `--execute` is passed
- Refuse to write unless the active contract sets
  `automation_policy.real_installer_authorized: true` AND the plan's mode is
  `allowed_now: true`
- Emit a rollback record artifact when `--rollback-record <path>` is set

Plans typically reference skills via paths inside a pack repo. To apply a
plan whose source skills live in a sibling pack repo, run the scaffolder
from that pack repo (or pass paths that point into it).

## Memory

Project memory (`memory/BRIEFING.md`, `memory/decision-log.md`, etc.) was
copied from `ml-research-skills` to preserve the OS-evolution history (ACT-038
through the hub split). Going forward, OS-level decisions should be recorded
here; pack-specific work belongs in the pack's own memory.

## Phase B2 plan

- Refactor skill-dependent tests to use synthetic `tests/fixtures/<profile>/`
  skill sets, so the full operational test suite runs inside skill-os.
- Slim `ml-research-skills`: build an explicit `ml-research.kernel.json` with
  named member skills (no more `include_all_repo_skills: true`), remove the
  ~50 skills that are now owned by split packs.
- Update CLAUDE.md / AGENTS.md across all pack repos to point at skill-os as
  the framework / rules layer.

## Source-of-truth rules

- **Kernel schema** is authoritative here (`schemas/skill-kernel/skill-kernel.schema.json`).
- **Active handoff contract** is authoritative here.
- **Profile-index** is authoritative here.
- **Skill files** (`SKILL.md` and bundled resources) are authoritative in the
  pack repos.
- The kernel examples under `schemas/skill-kernel/examples/` are reference
  copies; the authoritative kernel for a profile lives inside that profile's
  pack repo.

# skill-os

> The hub of a portable agent **Skill OS** matrix for AI research workflows.
> Defines the rules; the profile-pack repos hold the skills.

`skill-os` is the framework / source-of-truth-for-rules repo that sits on top
of a constellation of agent-skill profile packs. It owns:

- **Kernel schema** — `schemas/skill-kernel/skill-kernel.schema.json` and the
  portable kernel example shape used across all packs
- **Install / repo-split handoff contract** — the reviewed boundary that
  blocks unreviewed runtime writes; active contract at
  `schemas/skill-kernel/install-handoff-contract-2026-05-28.json`, frozen
  pre-revision preserved for refusal regression
- **Install-plan schema and validator** —
  `schemas/skill-kernel/install-plan.schema.json` plus
  `scripts/validate_install_handoff_plan.py`
- **Read-only previews** for project-local install + repo-split scaffold
  actions, with content-hash and rollback record templates
- **Real installer and scaffolder** — `scripts/apply_install_plan.py` and
  `scripts/apply_repo_split.py`; refuse known global skill roots; require
  `--execute` and an authorized contract
- **Matrix registry** — `profiles/profile-index.yaml`, listing every
  profile-pack repo by github_url
- **Design doc** — `docs/design/skill-matrix.md`

## Matrix today

| Profile | Status | Repo | Skills |
|---|---|---|---|
| `core-ops` | active | [core-ops-skills](https://github.com/a-green-hand-jack/core-ops-skills) | 12 — git, memory, docs, sidecars, validation, workspaces |
| `automation` | active | [automation-skills](https://github.com/a-green-hand-jack/automation-skills) | 6 — SSH/HPC/RunAI, scheduler probes; depends on `core-ops` |
| `paper-reading` | active | [paper-reading-skills](https://github.com/a-green-hand-jack/paper-reading-skills) | 11 — literature reading, source cards, corpus comparison; depends on `core-ops` |
| `research-distillation` | active | [research-distillation-skills](https://github.com/a-green-hand-jack/research-distillation-skills) | 13 — distill external papers/projects/people/workflows into reusable skills; depends on `core-ops` |
| `quick-experiment` | active | [quick-experiment-skills](https://github.com/a-green-hand-jack/quick-experiment-skills) | 9 — scratchpad experiments without the paper lifecycle; depends on `core-ops` + `automation` |
| `ml-research` | active | [ml-research-skills](https://github.com/a-green-hand-jack/ml-research-skills) | 74 (current full bundle pending Phase B2 slim) — full AI PhD / ML research lifecycle |

`global-bootstrap` is a thin entrypoint pack and stays inside
`ml-research-skills` for now.

## Folder-shape install recipes

A folder generally installs one or more profile packs side by side. Common
combinations:

- **Pure paper reading folder** → `core-ops` + `paper-reading` (23 skills)
- **Remote ops / cluster maintenance folder** → `core-ops` + `automation` (18 skills)
- **Quick experiment scratchpad** → `core-ops` + `automation` + `quick-experiment` (27 skills)
- **Full ML research project** → `ml-research` (74 skills — the current bundle)
- **Research distillation** → `core-ops` + `research-distillation` (25 skills)

The reviewed install plan flow lives under `scripts/apply_install_plan.py` and
`scripts/apply_repo_split.py`; both refuse to write until the active handoff
contract authorizes the target mode AND the caller passes `--execute`. They
also refuse any target under known global skill roots (`~/.codex/skills`,
`~/.agents/skills`, `~/.claude/skills`) regardless of contract state.

## Phase status

**Phase B1 (this repo, today)** — skill-os created from the source pack
`ml-research-skills`. Contains schema, contract, plan schema, kernel examples
(reference), scripts, registry, design doc, dry-run + adapter export tests.
Test coverage is partial: tests that need a live `skills/` directory have been
removed from this repo and remain authoritative in `ml-research-skills` for
now. `tests/test_skill_kernel_adapter_export.py` and
`tests/test_profile_routing_harness.py` run cleanly here.

**Phase B2 (future)** — refactor the operational tests to use synthetic skill
fixtures so the full test suite runs in skill-os. Slim `ml-research-skills`:
remove split-profile-only skills, add an explicit `ml-research.kernel.json`,
drop hub duplication. After B2, ml-research-skills is just one pack like the
others.

## Source of truth

- Kernel schema rules and the active handoff contract live HERE.
- Skill files (`SKILL.md` and bundled resources) live in each PACK repo.
- The reference kernel examples under `schemas/skill-kernel/examples/` are
  COPIES of what each pack repo carries; the authoritative kernel for a pack
  is the one inside that pack's own repo.

## License and use

Public on GitHub. Pull requests and issues welcome. Generated kernel + adapter
output is always marked `dry_run: true` until a reviewed install plan and an
authorized contract say otherwise. Read the contract before writing.
